import asyncio
from datetime import datetime

import pytest

from pehloo.domain.entities.persona import Persona
from pehloo.domain.entities.journey import Journey, JourneyStep
from pehloo.domain.entities.test_run import TestRun
from pehloo.domain.entities.observation import Observation
from pehloo.domain.ports.i_browser_agent import IBrowserAgent
from pehloo.use_cases.execute_persona_run import ExecutePersonaRun


class MockBrowserAgent(IBrowserAgent):
    async def run_step(self, persona: Persona, step: JourneyStep, url: str) -> Observation:
        return Observation(
            test_run_id="",
            step_index=step.index,
            step_instruction=step.instruction,
            status="completed",
            narration="All good.",
            friction_score=1,
            delight_score=4,
            url_at_step=url,
            raw_agent_output="{}",
            timestamp=datetime.utcnow(),
        )


@pytest.fixture
def test_run():
    persona = Persona(
        id="p1", name="Priya", description="PM", goals=[], pain_points=[],
        tech_literacy="high", patience_level="medium",
    )
    journey = Journey(id="j1", name="Onboarding", steps=[
        JourneyStep(index=0, instruction="Sign up", success_criteria="Dashboard"),
        JourneyStep(index=1, instruction="Find pricing", success_criteria="Pricing page"),
    ])
    return TestRun(id="r1", persona=persona, journey=journey, target_url="https://example.com", started_at=datetime.utcnow())


@pytest.mark.asyncio
async def test_execute_persona_run_collects_observations(test_run):
    use_case = ExecutePersonaRun(browser_agent=MockBrowserAgent())
    observations = await use_case.execute(test_run)
    assert len(observations) == len(test_run.journey.steps)
    assert all(o.status == "completed" for o in observations)
