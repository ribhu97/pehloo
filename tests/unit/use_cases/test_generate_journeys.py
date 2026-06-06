import pytest

from pehloo.domain.entities.persona import Persona
from pehloo.domain.entities.journey import Journey, JourneyStep
from pehloo.domain.ports.i_journey_generator import IJourneyGenerator
from pehloo.use_cases.generate_journeys import GenerateJourneys


class FakeJourneyGenerator(IJourneyGenerator):
    def __init__(self, journeys: list[Journey]) -> None:
        self._journeys = journeys
        self.last_call: dict | None = None

    async def generate(self, persona, target_url, count=3, previous=None, feedback=None):
        self.last_call = {
            "persona": persona,
            "target_url": target_url,
            "count": count,
            "previous": previous,
            "feedback": feedback,
        }
        return self._journeys


@pytest.fixture
def persona():
    return Persona(
        id="p1", name="Priya", description="PM", goals=["Sign up"],
        pain_points=["Forms"], tech_literacy="high", patience_level="medium",
    )


@pytest.fixture
def canned_journeys():
    return [
        Journey(id="j1", name="Onboarding", steps=[
            JourneyStep(index=0, instruction="Sign up", success_criteria="Dashboard"),
        ]),
        Journey(id="j2", name="Pricing", steps=[
            JourneyStep(index=0, instruction="Find pricing", success_criteria="See plans"),
        ]),
    ]


@pytest.mark.asyncio
async def test_generate_journeys_forwards_first_call(persona, canned_journeys):
    fake = FakeJourneyGenerator(canned_journeys)
    use_case = GenerateJourneys(generator=fake)

    result = await use_case.execute(persona, "https://example.com", count=3)

    assert result == canned_journeys
    assert fake.last_call["persona"] is persona
    assert fake.last_call["target_url"] == "https://example.com"
    assert fake.last_call["count"] == 3
    assert fake.last_call["previous"] is None
    assert fake.last_call["feedback"] is None


@pytest.mark.asyncio
async def test_generate_journeys_forwards_refinement(persona, canned_journeys):
    fake = FakeJourneyGenerator(canned_journeys)
    use_case = GenerateJourneys(generator=fake)

    previous = [canned_journeys[0]]
    feedback = "Make them shorter"
    await use_case.execute(persona, "https://example.com", previous=previous, feedback=feedback)

    assert fake.last_call["previous"] is previous
    assert fake.last_call["feedback"] == feedback
