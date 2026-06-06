import uuid
from typing import Any

import yaml
from pydantic import BaseModel, field_validator, ValidationError

from pehloo.domain.entities.journey import Journey, JourneyStep
from pehloo.domain.ports.i_journey_parser import IJourneyParser


class _StepSchema(BaseModel):
    instruction: str
    success: str

    @field_validator("success")
    @classmethod
    def success_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("'success' field must not be empty")
        return v.strip()


class _JourneySchema(BaseModel):
    name: str
    steps: list[_StepSchema]


class YAMLJourneyParser(IJourneyParser):
    def parse(self, source: str) -> list[Journey]:
        with open(source, encoding="utf-8") as f:
            raw = yaml.safe_load(f)

        if isinstance(raw, dict) and "journeys" in raw:
            records: list[Any] = raw["journeys"]
        elif isinstance(raw, list):
            records = raw
        else:
            records = [raw]

        journeys = []
        for i, record in enumerate(records):
            try:
                schema = _JourneySchema.model_validate(record)
            except ValidationError as exc:
                raise ValueError(f"Journey #{i + 1} is invalid: {exc}") from exc
            journeys.append(self._to_entity(schema))
        return journeys

    def _to_entity(self, schema: _JourneySchema) -> Journey:
        steps = [
            JourneyStep(index=i, instruction=s.instruction, success_criteria=s.success)
            for i, s in enumerate(schema.steps)
        ]
        return Journey(id=str(uuid.uuid4()), name=schema.name, steps=steps)


def dump_journeys(journeys: list[Journey], path: str) -> None:
    """Serialise journeys to YAML in the same shape `YAMLJourneyParser` expects.

    Round-trip guarantee: the resulting file is parseable by `YAMLJourneyParser.parse`.
    """
    payload = {
        "journeys": [
            {
                "name": j.name,
                "steps": [
                    {"instruction": s.instruction, "success": s.success_criteria}
                    for s in j.steps
                ],
            }
            for j in journeys
        ]
    }
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(payload, f, sort_keys=False, default_flow_style=False)
