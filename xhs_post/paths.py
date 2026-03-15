from __future__ import annotations

import os
from pathlib import Path


def resolve_base_dir() -> Path:
    env_base_dir = os.environ.get("XHS_POST_BASE_DIR")
    if env_base_dir:
        return Path(env_base_dir).expanduser().resolve()
    return Path(__file__).resolve().parent.parent


def resolve_repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def resolve_config_dir(base_dir: Path | None = None) -> Path:
    return (base_dir or resolve_base_dir()) / "config"


def resolve_state_dir(base_dir: Path | None = None) -> Path:
    return (base_dir or resolve_base_dir()) / "state"


def resolve_artifacts_dir(base_dir: Path | None = None) -> Path:
    return (base_dir or resolve_base_dir()) / "artifacts"


def resolve_generation_state_file(base_dir: Path | None = None) -> Path:
    return resolve_state_dir(base_dir) / "generation_state.json"


def resolve_trending_artifact_file(base_dir: Path | None = None) -> Path:
    return resolve_artifacts_dir(base_dir) / "trending" / "current.json"


def resolve_image_analysis_artifact_file(base_dir: Path | None = None) -> Path:
    return resolve_artifacts_dir(base_dir) / "images" / "image_analysis.json"


def resolve_validation_report_dir(base_dir: Path | None = None) -> Path:
    return resolve_artifacts_dir(base_dir) / "validation"


def ensure_runtime_layout(base_dir: Path | None = None) -> dict[str, Path]:
    root = base_dir or resolve_base_dir()
    paths = {
        "config": resolve_config_dir(root),
        "state": resolve_state_dir(root),
        "artifacts": resolve_artifacts_dir(root),
        "trending": resolve_trending_artifact_file(root),
        "images": resolve_image_analysis_artifact_file(root),
        "validation": resolve_validation_report_dir(root),
    }
    for key in ("config", "state", "artifacts", "validation"):
        paths[key].mkdir(parents=True, exist_ok=True)
    paths["trending"].parent.mkdir(parents=True, exist_ok=True)
    paths["images"].parent.mkdir(parents=True, exist_ok=True)
    return paths
