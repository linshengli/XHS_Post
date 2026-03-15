from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Any


def normalize_text(value: str) -> str:
    text = re.sub(r"\s+", " ", value.strip().lower())
    return re.sub(r"[^\w\u4e00-\u9fff# ]+", "", text)


def build_content_signature(title: str, content: str) -> dict[str, Any]:
    normalized_title = normalize_text(title)
    normalized_content = normalize_text(content)
    return {
        "title": title.strip(),
        "content_preview": content.strip()[:120],
        "normalized_title": normalized_title,
        "normalized_content": normalized_content,
        "combined": f"{normalized_title}\n{normalized_content}",
    }


def content_similarity(left: dict[str, Any], right: dict[str, Any]) -> float:
    title_ratio = SequenceMatcher(None, left["normalized_title"], right["normalized_title"]).ratio()
    content_ratio = SequenceMatcher(None, left["normalized_content"], right["normalized_content"]).ratio()
    return round((title_ratio * 0.35) + (content_ratio * 0.65), 4)


def find_similar_signature(
    candidate: dict[str, Any],
    existing_signatures: list[dict[str, Any]],
    *,
    threshold: float,
) -> dict[str, Any] | None:
    for signature in existing_signatures:
        similarity = content_similarity(candidate, signature)
        if similarity >= threshold:
            return {
                "similarity": similarity,
                "matched_title": signature.get("title", ""),
                "matched_preview": signature.get("content_preview", ""),
            }
    return None
