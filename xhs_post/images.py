from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from xhs_post.storage import load_json


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


def load_image_analysis(image_analysis_file: Path) -> list[dict[str, Any]]:
    data = load_json(image_analysis_file)
    return data.get("images", [])


def extract_crawled_images(raw_posts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    images = []
    for post in raw_posts:
        image_list = post.get("image_list") or post.get("images") or post.get("image_urls")
        if not image_list:
            continue
        urls: list[str] = []
        if isinstance(image_list, str):
            urls = [url.strip() for url in image_list.split(",") if url.strip()]
        elif isinstance(image_list, list):
            for item in image_list:
                if isinstance(item, str) and item.strip():
                    urls.append(item.strip())
                elif isinstance(item, dict):
                    for key in ("url", "image_url", "path"):
                        value = item.get(key)
                        if isinstance(value, str) and value.strip():
                            urls.append(value.strip())
                            break
        if not urls:
            continue
        images.append(
            {
                "source_title": post.get("title", ""),
                "source_keyword": post.get("source_keyword", ""),
                "urls": urls,
            }
        )
    return images


def select_crawled_images_for_post(raw_posts: list[dict[str, Any]], count: int = 4) -> list[dict[str, Any]]:
    roles = ["封面图", "场景图", "细节图", "体验图"]
    for image_group in extract_crawled_images(raw_posts):
        selected_urls = image_group["urls"][:count]
        if selected_urls:
            return [
                {
                    "path": url,
                    "role": roles[index] if index < len(roles) else f"配图{index + 1}",
                    "theme": image_group["source_keyword"] or image_group["source_title"],
                }
                for index, url in enumerate(selected_urls)
            ]
    return []


def _score_image(image: dict[str, Any], topic: str, angle: str | None = None) -> int:
    score = 0
    topic_tokens = [token for token in [topic, angle] if token]
    haystack = " ".join(
        image.get("theme_tokens", [])
        + [image.get("theme", ""), image.get("style", ""), image.get("emotion", "")]
        + image.get("suitable_for", [])
    )
    for token in topic_tokens:
        if token and token in haystack:
            score += 5
    if any(keyword in haystack for keyword in ["封面图", "场景图", "细节图", "体验记录", "体验图"]):
        score += 3
    return score


def select_images_for_post(
    topic: str,
    angle: str | None,
    image_analyses: list[dict[str, Any]],
    used_combinations: list[str] | None = None,
    count: int = 4,
) -> tuple[list[dict[str, Any]], str | None]:
    if not image_analyses:
        return [], None

    roles = ["封面图", "场景图", "细节图", "体验图"]
    ranked = sorted(
        image_analyses,
        key=lambda image: (_score_image(image, topic, angle), image.get("index", 0)),
        reverse=True,
    )
    used_combinations = used_combinations or []

    for start in range(len(ranked)):
        selected = ranked[start : start + count]
        if len(selected) < count:
            selected = ranked[:count]
        combination_id = "|".join(item["file_path"] for item in selected)
        if combination_id in used_combinations:
            continue
        return (
            [
                {
                    "path": image["file_path"],
                    "role": roles[index] if index < len(roles) else f"配图{index + 1}",
                    "theme": image.get("theme", ""),
                }
                for index, image in enumerate(selected)
            ],
            combination_id,
        )

    fallback = ranked[:count]
    combination_id = "|".join(item["file_path"] for item in fallback)
    return (
        [
            {
                "path": image["file_path"],
                "role": roles[index] if index < len(roles) else f"配图{index + 1}",
                "theme": image.get("theme", ""),
            }
            for index, image in enumerate(fallback)
        ],
        combination_id,
    )
