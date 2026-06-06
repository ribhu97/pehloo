import json
import tempfile
import os

import pytest

from pehloo.adapters.parsers.json_persona_parser import JSONPersonaParser
from pehloo.adapters.parsers.yaml_journey_parser import YAMLJourneyParser


def test_json_persona_parser_reads_list():
    data = [
        {"id": "p1", "name": "Alice", "description": "PM", "goals": ["ship it"],
         "pain_points": [], "tech_literacy": "high", "patience_level": "medium"},
    ]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(data, f)
        path = f.name
    try:
        personas = JSONPersonaParser().parse(path)
        assert len(personas) == 1
        assert personas[0].name == "Alice"
    finally:
        os.unlink(path)


def test_yaml_journey_parser_reads_steps():
    yaml_content = """
journeys:
  - name: Onboarding
    steps:
      - instruction: Sign up
        success: Reaches dashboard
      - instruction: Find pricing
        success: Sees pricing tiers
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(yaml_content)
        path = f.name
    try:
        journeys = YAMLJourneyParser().parse(path)
        assert len(journeys) == 1
        assert len(journeys[0].steps) == 2
        assert journeys[0].steps[0].instruction == "Sign up"
        assert journeys[0].steps[0].success_criteria == "Reaches dashboard"
    finally:
        os.unlink(path)


def test_yaml_journey_parser_raises_on_missing_success():
    yaml_content = """
- name: Bad Journey
  steps:
    - instruction: Do something
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(yaml_content)
        path = f.name
    try:
        with pytest.raises(ValueError, match="invalid"):
            YAMLJourneyParser().parse(path)
    finally:
        os.unlink(path)


def test_yaml_journey_parser_raises_on_empty_success():
    yaml_content = """
- name: Bad Journey
  steps:
    - instruction: Do something
      success: "   "
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(yaml_content)
        path = f.name
    try:
        with pytest.raises(ValueError, match="invalid"):
            YAMLJourneyParser().parse(path)
    finally:
        os.unlink(path)
