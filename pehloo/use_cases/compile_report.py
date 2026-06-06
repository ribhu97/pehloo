import uuid
from datetime import datetime
from typing import Any

from pehloo.domain.entities.test_run import TestRun
from pehloo.domain.entities.observation import Observation
from pehloo.domain.entities.report import Report, CriticalIssue
from pehloo.domain.ports.i_llm_client import ILLMClient
from pehloo.domain.ports.i_report_renderer import IReportRenderer


_SYSTEM_PROMPT = """You are a UX research analyst reviewing observations from multiple persona test runs.
Respond ONLY with valid JSON matching this schema:

{
  "summary": "2-3 sentence cross-persona narrative",
  "critical_issues": [
    {
      "title": "short imperative title (e.g. 'Signup CTA hidden below the fold')",
      "description": "1-2 sentences on what went wrong and why it matters",
      "suggested_fix": "concrete actionable fix the founder can ship",
      "affected_persona_ids": ["persona_id_1"],
      "affected_step_indices": [0, 2]
    }
  ],
  "per_persona_findings": {
    "persona_id_1": "one paragraph narrative for this persona"
  }
}

Focus critical_issues on problems seen by 2+ personas OR with friction >= 4.
Assume the reader is a solo founder who will fix these tomorrow — be concrete."""


class CompileReport:
    def __init__(self, llm_client: ILLMClient, renderer: IReportRenderer) -> None:
        self._llm = llm_client
        self._renderer = renderer

    async def execute(
        self,
        test_runs: list[TestRun],
        observations: list[Observation],
        output_path: str,
    ) -> Report:
        user_prompt = self._build_prompt(test_runs, observations)
        payload = await self._llm.complete_json(system=_SYSTEM_PROMPT, user=user_prompt)

        summary = str(payload.get("summary", ""))
        critical_issues = self._parse_issues(payload.get("critical_issues", []) or [], observations)
        per_persona = dict(payload.get("per_persona_findings", {}) or {})

        for run in test_runs:
            per_persona.setdefault(
                run.persona.id, self._fallback_persona_summary(run, observations)
            )

        prioritized = sorted(critical_issues, key=lambda i: i.severity, reverse=True)[:5]

        report = Report(
            id=str(uuid.uuid4()),
            test_runs=test_runs,
            observations=observations,
            summary=summary,
            critical_issues=critical_issues,
            per_persona_findings=per_persona,
            generated_at=datetime.utcnow(),
            prioritized_issues=prioritized,
        )
        self._renderer.render(report, output_path)
        return report

    def _build_prompt(self, test_runs: list[TestRun], observations: list[Observation]) -> str:
        lines = ["Persona roster:"]
        for run in test_runs:
            lines.append(
                f"- id={run.persona.id} name={run.persona.name} — {run.persona.description}"
            )
        lines.append("\nObservations:")
        for obs in observations:
            run = next(r for r in test_runs if r.id == obs.test_run_id)
            lines.append(
                f"[persona_id={run.persona.id} step={obs.step_index}] {obs.step_instruction}\n"
                f"  status={obs.status} friction={obs.friction_score}/5 "
                f"delight={obs.delight_score}/5 url={obs.url_at_step}\n"
                f"  narration: {obs.narration}"
            )
        return "\n".join(lines)

    def _parse_issues(
        self, raw_issues: list[dict[str, Any]], observations: list[Observation]
    ) -> list[CriticalIssue]:
        issues: list[CriticalIssue] = []
        for raw in raw_issues:
            persona_ids = [str(p) for p in (raw.get("affected_persona_ids") or [])]
            step_indices = [int(s) for s in (raw.get("affected_step_indices") or [])]
            issues.append(
                CriticalIssue(
                    title=str(raw.get("title", "Untitled issue")),
                    description=str(raw.get("description", "")),
                    suggested_fix=str(raw.get("suggested_fix", "")),
                    affected_persona_ids=persona_ids,
                    affected_step_indices=step_indices,
                    severity=self._severity(persona_ids, step_indices, observations),
                )
            )
        return issues

    def _severity(
        self,
        persona_ids: list[str],
        step_indices: list[int],
        observations: list[Observation],
    ) -> float:
        matching = [o for o in observations if o.step_index in step_indices]
        if not matching:
            return float(len(persona_ids))
        avg_friction = sum(o.friction_score for o in matching) / len(matching)
        return round(avg_friction * max(len(persona_ids), 1), 2)

    def _fallback_persona_summary(
        self, run: TestRun, observations: list[Observation]
    ) -> str:
        run_obs = [o for o in observations if o.test_run_id == run.id]
        if not run_obs:
            return "No observations recorded."
        avg_friction = sum(o.friction_score for o in run_obs) / len(run_obs)
        stuck = [o for o in run_obs if o.status in ("stuck", "failed")]
        return (
            f"Completed {len(run_obs)} steps. Avg friction {avg_friction:.1f}/5. "
            f"Blocked at {len(stuck)} step(s)."
        )
