from pehloo.domain.entities.persona import Persona
from pehloo.domain.entities.journey import Journey
from pehloo.domain.ports.i_persona_parser import IPersonaParser
from pehloo.domain.ports.i_journey_parser import IJourneyParser


class ParseInputs:
    def __init__(self, persona_parser: IPersonaParser, journey_parser: IJourneyParser) -> None:
        self._persona_parser = persona_parser
        self._journey_parser = journey_parser

    def execute(self, personas_path: str, journeys_path: str) -> tuple[list[Persona], list[Journey]]:
        personas = self._persona_parser.parse(personas_path)
        journeys = self._journey_parser.parse(journeys_path)
        return personas, journeys
