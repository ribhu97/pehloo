from dataclasses import dataclass


@dataclass
class JourneyStep:
    index: int
    instruction: str
    success_criteria: str


@dataclass
class Journey:
    id: str
    name: str
    steps: list[JourneyStep]
