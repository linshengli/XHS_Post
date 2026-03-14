from __future__ import annotations

import os
import sys
from pathlib import Path


def ensure_project_root_on_path() -> Path:
    """Ensure the repository root is importable when running scripts directly."""
    project_root = Path(__file__).resolve().parent.parent
    project_root_str = str(project_root)
    if project_root_str not in sys.path:
        sys.path.insert(0, project_root_str)
    return project_root


def resolve_base_dir() -> Path:
    """Resolve the project root for local runs, tests, and CI."""
    env_base_dir = os.environ.get("XHS_POST_BASE_DIR")
    if env_base_dir:
        return Path(env_base_dir).expanduser().resolve()

    return ensure_project_root_on_path()
