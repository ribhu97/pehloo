from abc import ABC, abstractmethod

from pehloo.domain.entities.persona import Persona
from pehloo.domain.entities.journey import Journey


class IJourneyGenerator(ABC):
    @abstractmethod
    async def generate(
        self,
        persona: Persona,
        target_url: str,
        count: int = 3,
        previous: list[Journey] | None = None,
        feedback: str | None = None,
    ) -> list[Journey]: ...
