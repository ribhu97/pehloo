from pehloo.domain.entities.persona import Persona
from pehloo.domain.entities.journey import Journey
from pehloo.domain.ports.i_journey_generator import IJourneyGenerator


class GenerateJourneys:
    def __init__(self, generator: IJourneyGenerator) -> None:
        self._generator = generator

    async def execute(
        self,
        persona: Persona,
        target_url: str,
        count: int = 3,
        previous: list[Journey] | None = None,
        feedback: str | None = None,
    ) -> list[Journey]:
        return await self._generator.generate(
            persona=persona,
            target_url=target_url,
            count=count,
            previous=previous,
            feedback=feedback,
        )
