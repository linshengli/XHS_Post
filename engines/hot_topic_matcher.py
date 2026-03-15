#!/usr/bin/env python3
"""兼容层：旧热点匹配引擎，内部委托到 xhs_post.matching。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from xhs_post.personas import normalize_persona_config
from xhs_post.workflows.multi_account import match_topic_to_personas as workflow_match_topic_to_personas
from xhs_post.matching import load_persona_config, match_topic_to_personas


class HotTopicPersonaMatcher:
    def __init__(self, config_dir: str | None = None):
        base_dir = Path(config_dir) if config_dir else Path(__file__).resolve().parent.parent / "config"
        self.config_dir = base_dir
        self.personas_dir = base_dir / "personas"

    def load_persona(self, persona_file: str) -> dict[str, Any]:
        return load_persona_config(self.config_dir, persona_file)

    def extract_topic_keywords(self, topic: str) -> list[str]:
        return [item.strip() for item in topic.replace("，", ",").split(",") if item.strip()]

    def calculate_persona_match(self, topic: str, persona: dict[str, Any]) -> dict[str, Any]:
        normalized_persona = normalize_persona_config(persona)
        match = workflow_match_topic_to_personas(topic, {}, [normalized_persona])[normalized_persona["account"]["id"]]
        persona_data = normalized_persona.get("persona", {})
        match = {
            "persona_id": normalized_persona["account"]["id"],
            "persona_name": persona_data.get("name"),
            "topic": topic,
            "overall_score": round(match["match_score"] / 100, 3),
            "domain_score": round(match["match_score"] / 100, 3),
            "tag_score": 0.0,
            "matched_domains": persona_data.get("content_domains", {}).get("primary", []),
            "matched_tags": persona_data.get("tags", []),
            "suggested_angles": [{"angle_name": match["angle"], "description": match["angle"], "priority": 1}],
            "recommendation_level": "high" if match["match_score"] >= 80 else "medium",
        }
        return match

    def match_topic_to_personas(self, topic: str, persona_files: list[str]) -> list[dict[str, Any]]:
        requested_tokens = {Path(file_name).stem for file_name in persona_files}
        matches = match_topic_to_personas(topic, self.personas_dir, {})
        filtered = []
        for match in matches:
            persona_id = match["persona_id"]
            if persona_id in requested_tokens:
                filtered.append(match)
                continue
            if any(persona_id in token or token in persona_id for token in requested_tokens):
                filtered.append(match)
        return filtered

    def match_trending_analysis(self, trending_data: dict[str, Any], persona_files: list[str]) -> dict[str, Any]:
        topic = trending_data.get("topic", "")
        matches = self.match_topic_to_personas(topic, persona_files)
        return {
            "topic": topic,
            "match_count": len(matches),
            "matches": matches,
        }


def main() -> None:
    matcher = HotTopicPersonaMatcher()
    matches = matcher.match_topic_to_personas("千岛湖亲子酒店", ["account_001_qiandaohe_guide.yaml"])
    for match in matches:
        print(f"{match['persona_name']}: {match['overall_score']}")


if __name__ == "__main__":
    main()
