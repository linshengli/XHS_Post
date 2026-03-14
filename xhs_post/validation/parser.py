from __future__ import annotations

import re
from pathlib import Path
from typing import Any


def discover_posts(input_dir: Path, pattern: str = "*.md") -> list[Path]:
    return sorted(input_dir.glob(pattern))


def load_post(file_path: Path) -> dict[str, Any]:
    content = file_path.read_text(encoding="utf-8")

    title_match = re.search(r"^#\s*🔥\s*标题选项.*?\n((?:\d+\..*?\n)+)", content, re.DOTALL)
    titles = []
    if title_match:
        title_lines = title_match.group(1).strip().split("\n")
        titles = [re.sub(r"^\d+\.\s*", "", line).strip() for line in title_lines if line.strip()]

    tags_match = re.search(r"##\s*🏷️\s*推荐标签\s*\n([\s\S]*?)(?=##|\Z)", content)
    tags = re.findall(r"#\w+", tags_match.group(0)) if tags_match else []

    body_match = re.search(r"##\s*✍️\s*正文\s*\n([\s\S]*?)(?=##\s*⏰|\Z)", content)
    body = body_match.group(1).strip() if body_match else ""

    time_match = re.search(r"##\s*⏰\s*最佳发布时间\s*\n(.+?)(?:\n|$)", content)
    best_time = time_match.group(1).strip() if time_match else ""

    return {
        "filename": file_path.name,
        "titles": titles,
        "tags": tags,
        "body": body,
        "best_time": best_time,
        "full_content": content,
    }
