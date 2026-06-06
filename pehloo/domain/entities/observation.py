from dataclasses import dataclass
from datetime import datetime


@dataclass
class Observation:
    test_run_id: str
    step_index: int
    step_instruction: str
    status: str  # "completed" | "stuck" | "failed" | "skipped"
    narration: str
    friction_score: int  # 1–5
    delight_score: int   # 1–5
    url_at_step: str
    raw_agent_output: str
    timestamp: datetime
    screenshot_path: str | None = None
