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


@dataclass(slots=True)
class MultiAccountWorkflowRequest:
    topic: str
    input_path: Path
    output_dir: Path
    personas_dir: Path


@dataclass(slots=True)
class ImageWorkflowRequest:
    images_dir: Path
    output_path: Path
    topic: str | None = None


@dataclass(slots=True)
class ValidationWorkflowRequest:
    input_dir: Path
    output_path: Path
    pattern: str = "*.md"


@dataclass(slots=True)
class HotelOptimizationWorkflowRequest:
    input_dir: Path
    output_dir: Path
    personas_dir: Path
    report_path: Path | None = None


@dataclass(slots=True)
class LLMPostWorkflowRequest:
    topic: str
    count: int
    trending_input: Path
    output_dir: Path
    raw_posts_dir: Path
    state_file: Path | None = None
    provider: str | None = None
    seed: int | None = None
    similarity_threshold: float = 0.82
    max_attempts_per_post: int = 3


@dataclass(slots=True)
class ReleaseCandidateWorkflowRequest:
    topic: str
    count: int
    output_dir: Path
    validation_output: Path
    use_llm: bool = False
    provider: str | None = None
    seed: int | None = None


@dataclass(slots=True)
class ImagePlanWorkflowRequest:
    topic: str
    image_analysis_path: Path
    output_path: Path
    angle: str | None = None
    count: int = 4


@dataclass(slots=True)
class DraftRequirementsWorkflowRequest:
    topic: str
    trending_input: Path
    output_path: Path
