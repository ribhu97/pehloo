from abc import ABC, abstractmethod

from pehloo.domain.entities.journey import Journey


class IJourneyParser(ABC):
    @abstractmethod
    def parse(self, source: str) -> list[Journey]: ...
