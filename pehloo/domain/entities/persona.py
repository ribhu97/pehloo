from dataclasses import dataclass, field


@dataclass
class Persona:
    id: str
    name: str
    description: str
    goals: list[str]
    pain_points: list[str]
    tech_literacy: str  # "low" | "medium" | "high"
    patience_level: str  # "low" | "medium" | "high"
    raw: dict = field(default_factory=dict)
