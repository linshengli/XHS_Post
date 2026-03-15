#!/usr/bin/env python3
"""同步旧运行态文件到新的 state/artifacts 目录。"""

from _project_paths import ensure_project_root_on_path, resolve_base_dir

ensure_project_root_on_path()

from xhs_post.paths import (
    ensure_runtime_layout,
    resolve_config_dir,
    resolve_generation_state_file,
    resolve_image_analysis_artifact_file,
    resolve_trending_artifact_file,
)
from xhs_post.storage import seed_file_from_legacy


def main() -> None:
    base_dir = resolve_base_dir()
    ensure_runtime_layout(base_dir)
    config_dir = resolve_config_dir(base_dir)

    sync_pairs = [
        (resolve_generation_state_file(base_dir), config_dir / "generation_state.json"),
        (resolve_trending_artifact_file(base_dir), config_dir / "trending_analysis.json"),
        (resolve_image_analysis_artifact_file(base_dir), config_dir / "image_analysis.json"),
    ]

    for target_path, legacy_path in sync_pairs:
        seed_file_from_legacy(target_path, legacy_path, default_data={})
        print(f"{legacy_path} -> {target_path}")


if __name__ == "__main__":
    main()
