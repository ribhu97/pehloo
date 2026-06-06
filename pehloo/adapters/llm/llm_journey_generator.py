import json
import uuid
from typing import Any

from pydantic import ValidationError

from pehloo.adapters.parsers.yaml_journey_parser import _JourneySchema
from pehloo.domain.entities.journey import Journey, JourneyStep
from pehloo.domain.entities.persona import Persona
from pehloo.domain.ports.i_journey_generator import IJourneyGenerator
from pehloo.domain.ports.i_llm_client import ILLMClient


_SYSTEM_PROMPT = """You are a UX research assistant designing user journeys for usability tests.

Given a persona and a target web app URL, you propose realistic end-to-end journeys this
persona would attempt on the site. Each journey is 3-6 concrete steps. Each step has a
clear `instruction` (what the user tries to do) and a `success` criterion (how we know
they succeeded).

You output STRICT JSON only — no prose, no markdown fences. The schema is:

{
  "journeys": [
    {
      "name": "<short title>",
      "steps": [
        {"instruction": "<what to do>", "success": "<observable success criterion>"}
      ]
    }
  ]
}
"""


class LLMJourneyGenerator(IJourneyGenerator):
    def __init__(self, llm_client: ILLMClient) -> None:
        self._llm = llm_client

    async def generate(
        self,
        persona: Persona,
        target_url: str,
        count: int = 3,
        previous: list[Journey] | None = None,
        feedback: str | None = None,
    ) -> list[Journey]:
        user_prompt = self._build_user_prompt(persona, target_url, count, previous, feedback)
        raw = await self._llm.complete(system=_SYSTEM_PROMPT, user=user_prompt)
        return self._parse_response(raw)

    def _build_user_prompt(
        self,
        persona: Persona,
        target_url: str,
        count: int,
        previous: list[Journey] | None,
        feedback: str | None,
    ) -> str:
        sections = [
            f"Target URL: {target_url}",
            "",
            "Persona:",
            f"  Name: {persona.name}",
            f"  Description: {persona.description}",
            f"  Goals: {', '.join(persona.goals) or '(none specified)'}",
            f"  Pain points: {', '.join(persona.pain_points) or '(none specified)'}",
            f"  Tech literacy: {persona.tech_literacy}",
            f"  Patience: {persona.patience_level}",
            "",
            f"Propose exactly {count} distinct journeys this persona would realistically attempt.",
        ]
        if previous and feedback:
            sections.extend([
                "",
                "Previous proposal (revise based on the user's feedback below):",
                json.dumps(_journeys_to_payload(previous), indent=2),
                "",
                f"User feedback: {feedback}",
                "",
                f"Revise the proposal accordingly. Still return exactly {count} journeys.",
            ])
        sections.extend(["", "Return JSON only."])
        return "\n".join(sections)

    def _parse_response(self, raw: str) -> list[Journey]:
        payload = _extract_json_object(raw)
        if not isinstance(payload, dict) or "journeys" not in payload:
            raise ValueError(
                f"LLM did not return the expected JSON shape. Got: {raw[:200]}"
            )

        journeys: list[Journey] = []
        for i, record in enumerate(payload["journeys"]):
            try:
                schema = _JourneySchema.model_validate(record)
            except ValidationError as exc:
                raise ValueError(f"Generated journey #{i + 1} is invalid: {exc}") from exc
            steps = [
                JourneyStep(index=j, instruction=s.instruction, success_criteria=s.success)
                for j, s in enumerate(schema.steps)
            ]
            journeys.append(Journey(id=str(uuid.uuid4()), name=schema.name, steps=steps))
        return journeys


def _journeys_to_payload(journeys: list[Journey]) -> dict[str, Any]:
    """Same dict shape as the YAML / JSON wire format — used for refinement context."""
    return {
        "journeys": [
            {
                "name": j.name,
                "steps": [
                    {"instruction": s.instruction, "success": s.success_criteria}
                    for s in j.steps
                ],
            }
            for j in journeys
        ]
    }


def _extract_json_object(text: str) -> Any:
    """Tolerate models that wrap JSON in code fences or add a stray prefix."""
    stripped = text.strip()
    if stripped.startswith("```"):
        # strip ``` or ```json fences
        stripped = stripped.strip("`")
        if stripped.lower().startswith("json"):
            stripped = stripped[4:]
        stripped = stripped.strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        start = stripped.find("{")
        end = stripped.rfind("}") + 1
        if start == -1 or end == 0:
            raise ValueError(f"No JSON object found in LLM response: {text[:200]}")
        return json.loads(stripped[start:end])
