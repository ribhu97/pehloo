from dataclasses import dataclass
from datetime import datetime

from pehloo.domain.entities.persona import Persona
from pehloo.domain.entities.journey import Journey


@dataclass
class TestRun:
    id: str
    persona: Persona
    journey: Journey
    target_url: str
    started_at: datetime
    completed_at: datetime | None = None
