from abc import ABC, abstractmethod

from pehloo.domain.entities.persona import Persona
from pehloo.domain.entities.journey import JourneyStep
from pehloo.domain.entities.observation import Observation


class IBrowserAgent(ABC):
    @abstractmethod
    async def run_step(self, persona: Persona, step: JourneyStep, url: str) -> Observation: ...

    async def close(self) -> None:
        """Release any persistent resources (browser session, etc.). Default no-op."""
        return None
