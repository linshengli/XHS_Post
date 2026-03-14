from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


def discover_image_files(images_dir: Path) -> list[Path]:
    return sorted(
        [
            file_path
            for file_path in images_dir.rglob("*")
            if file_path.is_file() and file_path.suffix.lower() in IMAGE_EXTENSIONS
        ]
    )


def _pick(items: list[str], index: int, offset: int = 0) -> str:
    return items[(index + offset) % len(items)]


def infer_theme_tokens(image_path: Path, topic: str | None = None) -> list[str]:
    tokens = []
    if topic:
        tokens.append(topic)
    if image_path.parent.name:
        tokens.append(image_path.parent.name)
    stem = image_path.stem.replace("_", " ").replace("-", " ").strip()
    if stem:
        tokens.append(stem)
    return tokens


def analyze_image_smart(image_path: Path, index: int, topic: str | None = None) -> dict[str, Any]:
    theme_tokens = infer_theme_tokens(image_path, topic)
    theme_seed = theme_tokens[0] if theme_tokens else "通用图文素材"

    generic_elements = ["人物", "环境", "细节", "场景", "构图", "光线", "色彩", "氛围"]
    generic_colors = ["暖色调", "冷色调", "自然色", "高对比", "柔和", "明亮", "低饱和"]
    generic_emotions = ["松弛感", "真实感", "氛围感", "生活感", "清爽", "治愈", "高级感"]
    generic_styles = ["生活记录", "旅行写真", "探店纪实", "轻攻略", "视觉笔记", "种草图文"]
    generic_content_types = ["封面图", "场景图", "细节图", "路线说明", "体验记录", "攻略配图"]

    return {
        "file_name": image_path.name,
        "file_path": str(image_path),
        "relative_dir": str(image_path.parent),
        "theme": theme_seed,
        "theme_tokens": theme_tokens,
        "elements": [_pick(generic_elements, index, offset) for offset in range(4)],
        "colors": [_pick(generic_colors, index, offset) for offset in range(2)],
        "emotion": _pick(generic_emotions, index),
        "style": _pick(generic_styles, index),
        "suitable_for": [_pick(generic_content_types, index, offset) for offset in range(2)],
        "analysis_method": "smart_inference",
        "index": index,
    }


def build_image_analysis(image_files: list[Path], topic: str | None = None) -> dict[str, Any]:
    analyses = [
        analyze_image_smart(image_path, index, topic)
        for index, image_path in enumerate(image_files)
    ]
    return {
        "total_images": len(analyses),
        "analysis_date": datetime.now().strftime("%Y-%m-%d"),
        "topic": topic,
        "images": analyses,
    }
