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
