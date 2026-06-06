import json
import uuid

from pehloo.domain.entities.persona import Persona
from pehloo.domain.ports.i_persona_parser import IPersonaParser


class JSONPersonaParser(IPersonaParser):
    def parse(self, source: str) -> list[Persona]:
        with open(source, encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, dict):
            records = data.get("personas", [data])
        else:
            records = data

        return [self._parse_one(r) for r in records]

    def _parse_one(self, raw: dict) -> Persona:
        return Persona(
            id=raw.get("id", str(uuid.uuid4())),
            name=raw["name"],
            description=raw.get("description", ""),
            goals=raw.get("goals", []),
            pain_points=raw.get("pain_points", raw.get("painPoints", [])),
            tech_literacy=raw.get("tech_literacy", raw.get("techLiteracy", "medium")),
            patience_level=raw.get("patience_level", raw.get("patienceLevel", "medium")),
            raw=raw,
        )
