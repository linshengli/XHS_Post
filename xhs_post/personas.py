from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


DEFAULT_EXPRESSIONS = {
    "greetings": ["大家好"],
    "endings": ["记得点赞收藏"],
    "transitions": ["接着说重点"],
}

ANGLE_HINTS = {
    "route_anchor": "经验分享",
    "contrast_decision": "避坑指南",
    "problem_solver": "真实测评",
    "experience_evidence": "经验分享",
    "series_diary": "日常 Vlog",
}


def _normalize_tone(tone: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(tone or {})

    if "emoji_density" not in normalized:
        usage = normalized.get("emoji_usage", "moderate")
        density_map = {
            "low": 0.1,
            "low-moderate": 0.2,
            "moderate": 0.3,
            "moderate-high": 0.5,
            "high": 0.6,
        }
        normalized["emoji_density"] = density_map.get(str(usage), 0.3)

    if "style" not in normalized:
        normalized["style"] = normalized.get("perspective", "semi-formal")

    if "energy_level" not in normalized:
        normalized["energy_level"] = "medium"

    return normalized


def _derive_content_angles(persona: dict[str, Any]) -> list[str]:
    if persona.get("content_angles"):
        return persona["content_angles"]

    angles: list[str] = []
    hotel_insertion = persona.get("hotel_insertion", {})
    for mode in hotel_insertion.get("preferred_modes", []):
        angle = ANGLE_HINTS.get(mode)
        if angle and angle not in angles:
            angles.append(angle)

    if not angles:
        angles = ["经验分享", "避坑指南", "真实测评"]

    return angles


def normalize_persona_config(config: dict[str, Any], source: Path | None = None) -> dict[str, Any]:
    persona = dict(config.get("persona", {}))
    persona["tone"] = _normalize_tone(persona.get("tone", {}))
    persona["content_angles"] = _derive_content_angles(persona)
    persona["expressions"] = persona.get("expressions", DEFAULT_EXPRESSIONS)
    persona["demographics"] = persona.get(
        "demographics",
        {
            "occupation": persona.get("occupation", ""),
            "location": persona.get("location", ""),
            "age_range": "",
        },
    )
    persona["tags"] = [str(tag) for tag in persona.get("tags", [])]

    account_id = persona.get("id", source.stem if source else "unknown")
    account = dict(config.get("account", {}))
    account.setdefault("id", account_id)

    return {
        "account": account,
        "persona": persona,
        "source_file": str(source) if source else None,
    }


def load_personas(personas_dir: Path) -> list[dict[str, Any]]:
    personas = []
    for file_path in sorted(personas_dir.glob("*.yaml")):
        with open(file_path, "r", encoding="utf-8") as file:
            raw_config = yaml.safe_load(file) or {}
        personas.append(normalize_persona_config(raw_config, file_path))
    return personas
