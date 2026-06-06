from dataclasses import dataclass, field
from datetime import datetime

from pehloo.domain.entities.test_run import TestRun
from pehloo.domain.entities.observation import Observation


@dataclass
class CriticalIssue:
    title: str
    description: str
    suggested_fix: str
    affected_persona_ids: list[str]
    affected_step_indices: list[int]
    severity: float  # friction_avg × persona_count, used for ranking


@dataclass
class Report:
    id: str
    test_runs: list[TestRun]
    observations: list[Observation]
    summary: str
    critical_issues: list[CriticalIssue]
    per_persona_findings: dict[str, str]
    generated_at: datetime
    prioritized_issues: list[CriticalIssue] = field(default_factory=list)
