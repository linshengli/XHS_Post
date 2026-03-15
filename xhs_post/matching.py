from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from xhs_post.personas import load_personas, normalize_persona_config
from xhs_post.workflows.multi_account import match_topic_to_personas as workflow_match_topic_to_personas


def load_persona_config(config_dir: Path, persona_file: str) -> dict[str, Any]:
    file_path = config_dir / persona_file
    if not file_path.exists():
        raise FileNotFoundError(f"Persona file not found: {file_path}")
    with open(file_path, "r", encoding="utf-8") as file:
        return normalize_persona_config(yaml.safe_load(file) or {}, file_path)


def match_topic_to_personas(
    topic: str,
    personas_dir: Path,
    trending_data: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    personas = load_personas(personas_dir)
    matches = workflow_match_topic_to_personas(topic, trending_data or {}, personas)
    return [
        {
            "persona_id": account_id,
            "persona_name": match["persona"].get("name"),
            "topic": topic,
            "overall_score": round(match["match_score"] / 100, 3),
            "domain_score": round(match["match_score"] / 100, 3),
            "tag_score": 0.0,
            "matched_domains": match["persona"].get("content_domains", {}).get("primary", []),
            "matched_tags": match["persona"].get("tags", []),
            "suggested_angles": [
                {
                    "angle_name": match["angle"],
                    "description": f"围绕 {topic} 输出 {match['angle']}",
                    "priority": 1,
                }
            ],
            "recommendation_level": "high" if match["match_score"] >= 80 else "medium",
        }
        for account_id, match in matches.items()
    ]
