from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any


def load_json(file_path: Path) -> dict[str, Any]:
    if not file_path.exists():
        return {}
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_json(file_path: Path, data: dict[str, Any]) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def load_jsonl_files(input_dir: Path) -> list[dict[str, Any]]:
    posts: list[dict[str, Any]] = []
    if not input_dir.exists():
        return posts

    for file_path in sorted(input_dir.glob("*.jsonl")):
        with open(file_path, "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if not line:
                    continue
                try:
                    posts.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    return posts


def seed_file_from_legacy(target_path: Path, legacy_path: Path, default_data: dict[str, Any] | None = None) -> None:
    if target_path.exists():
        return
    target_path.parent.mkdir(parents=True, exist_ok=True)
    if legacy_path.exists():
        shutil.copyfile(legacy_path, target_path)
        return
    if default_data is not None:
        save_json(target_path, default_data)


def mirror_json_to_legacy(source_path: Path, legacy_path: Path) -> None:
    if not source_path.exists():
        return
    legacy_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source_path, legacy_path)
