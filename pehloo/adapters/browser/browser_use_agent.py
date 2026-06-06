import json
from datetime import datetime

from browser_use import Agent, BrowserProfile, BrowserSession
from browser_use.llm.openrouter.chat import ChatOpenRouter

from pehloo.domain.entities.persona import Persona
from pehloo.domain.entities.journey import JourneyStep
from pehloo.domain.entities.observation import Observation
from pehloo.domain.ports.i_browser_agent import IBrowserAgent

_TASK_TEMPLATE = """\
You are {name}. {description}

Your goals: {goals}
Your pain points: {pain_points}
Tech literacy: {tech_literacy} | Patience: {patience_level}

Complete this task: {instruction}
Success looks like: {success_criteria}
{credentials_block}
As you navigate, think and act as this persona would. When you have completed the task (or are stuck),
return a JSON object with this exact schema:
{{
  "status": "completed" | "stuck" | "failed" | "skipped",
  "narration": "<first-person narration of your experience>",
  "friction_score": <1-5>,
  "delight_score": <1-5>,
  "url_at_step": "<current URL>"
}}
"""


class BrowserUseAgent(IBrowserAgent):
    def __init__(
        self,
        api_key: str,
        model: str,
        max_steps: int = 15,
        headless: bool = True,
        login_email: str | None = None,
        login_password: str | None = None,
    ) -> None:
        self._llm = ChatOpenRouter(model=model, api_key=api_key)
        self._max_steps = max_steps
        self._headless = headless
        self._login_email = login_email
        self._login_password = login_password
        self._session: BrowserSession | None = None
        self._started = False

    async def run_step(self, persona: Persona, step: JourneyStep, url: str) -> Observation:
        task = _TASK_TEMPLATE.format(
            name=persona.name,
            description=persona.description,
            goals=", ".join(persona.goals),
            pain_points=", ".join(persona.pain_points),
            tech_literacy=persona.tech_literacy,
            patience_level=persona.patience_level,
            instruction=step.instruction,
            success_criteria=step.success_criteria,
            credentials_block=self._credentials_block(),
        )

        if self._session is None:
            self._session = BrowserSession(
                browser_profile=BrowserProfile(headless=self._headless, keep_alive=True),
            )

        # Only navigate explicitly on the first step — subsequent steps continue
        # from wherever the prior step left the browser.
        initial_actions = None
        if not self._started:
            initial_actions = [{"navigate": {"url": url, "new_tab": False}}]
            self._started = True

        agent = Agent(
            task=task,
            llm=self._llm,
            max_actions_per_step=self._max_steps,
            browser_session=self._session,
            initial_actions=initial_actions,
        )
        result = await agent.run()

        final_text = (result.final_result() or "").strip()
        parsed = self._extract_json(final_text)
        raw_output = final_text or str(result)

        screenshot_path: str | None = None
        if hasattr(result, "screenshot_paths"):
            shots = result.screenshot_paths() or []
            if shots:
                screenshot_path = str(shots[-1])

        return Observation(
            test_run_id="",  # caller sets this after construction
            step_index=step.index,
            step_instruction=step.instruction,
            status=parsed.get("status", "failed"),
            narration=parsed.get("narration", ""),
            friction_score=int(parsed.get("friction_score", 3)),
            delight_score=int(parsed.get("delight_score", 1)),
            url_at_step=parsed.get("url_at_step", url),
            raw_agent_output=raw_output,
            timestamp=datetime.utcnow(),
            screenshot_path=screenshot_path,
        )

    def _credentials_block(self) -> str:
        if not self._login_email or not self._login_password:
            return ""
        return (
            f"\nIf you hit a login or sign-in screen, use these credentials:\n"
            f"  email/username: {self._login_email}\n"
            f"  password: {self._login_password}\n"
            f"Do not attempt to sign up a new account when these are provided.\n"
        )

    async def close(self) -> None:
        if self._session is not None:
            await self._session.kill()
            self._session = None
            self._started = False

    def _extract_json(self, text: str) -> dict:
        start = text.rfind("{")
        end = text.rfind("}") + 1
        if start == -1 or end == 0:
            return {}
        try:
            return json.loads(text[start:end])
        except json.JSONDecodeError:
            return {}
