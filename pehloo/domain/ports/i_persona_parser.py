from abc import ABC, abstractmethod

from pehloo.domain.entities.persona import Persona


class IPersonaParser(ABC):
    @abstractmethod
    def parse(self, source: str) -> list[Persona]: ...
