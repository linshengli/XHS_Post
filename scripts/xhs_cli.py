#!/usr/bin/env python3
from __future__ import annotations

from _project_paths import ensure_project_root_on_path, resolve_base_dir

ensure_project_root_on_path()

from xhs_post.cli import main


if __name__ == "__main__":
    main()
