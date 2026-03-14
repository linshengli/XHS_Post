from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class TopicWorkflowRequest:
    topic: str
    count: int = 10
    analysis_output: Path | None = None
    generation_output: Path | None = None
    seed: int | None = None

