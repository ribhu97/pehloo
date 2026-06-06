from pehloo.domain.entities.persona import Persona
from pehloo.domain.entities.journey import Journey, JourneyStep


def test_persona_fields():
    p = Persona(
        id="p1", name="Alice", description="desc", goals=["goal"],
        pain_points=[], tech_literacy="high", patience_level="medium",
    )
    assert p.name == "Alice"
    assert p.tech_literacy == "high"


def test_journey_step_index():
    step = JourneyStep(index=0, instruction="Do X", success_criteria="X done")
    assert step.index == 0


def test_journey_has_steps():
    journey = Journey(id="j1", name="Onboarding", steps=[
        JourneyStep(index=0, instruction="Sign up", success_criteria="Dashboard loaded"),
    ])
    assert len(journey.steps) == 1
