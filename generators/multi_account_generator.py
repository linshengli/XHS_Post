#!/usr/bin/env python3
"""兼容层：旧多账号生成器，内部委托到 xhs_post。"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from typing import Any

from engines.constraint_engine import PersonaConstraintEngine
from xhs_post.llm import generate_structured_post
from xhs_post.matching import load_persona_config


class MultiAccountContentGenerator:
    def __init__(self, config_dir: str | None = None):
        self.config_dir = Path(config_dir) if config_dir else Path(__file__).resolve().parent.parent / "config"
        self.constraint_engine = PersonaConstraintEngine(config_dir=str(self.config_dir))

    def load_persona(self, persona_file: str) -> dict[str, Any]:
        return load_persona_config(self.config_dir, persona_file)

    def build_persona_prompt(self, persona: dict[str, Any], topic: str, angle: str) -> str:
        persona_info = persona.get("persona", {})
        tone = persona_info.get("tone", {})
        expressions = persona_info.get("expressions", {})
        content_domains = persona_info.get("content_domains", {})
        return "\n".join(
            [
                "请输出 JSON，包含 title, content, tags 三个字段。",
                f"主题：{topic}",
                f"角度：{angle}",
                f"人设：{persona_info.get('name', '博主')}",
                f"语调：{tone.get('style', 'semi-formal')}",
                f"主领域：{content_domains.get('primary', [])}",
                f"开场风格：{expressions.get('greetings', ['大家好'])[0]}",
                "要求：符合该人设语气；正文适合小红书图文；tags 返回数组。",
            ]
        )

    def call_llm(self, prompt: str) -> dict[str, Any]:
        return generate_structured_post(prompt, provider="mock")

    def parse_llm_response(self, response: dict[str, Any]) -> dict[str, Any]:
        return {
            "title": response["title"],
            "content": response["content"],
            "tags": response["tags"],
        }

    def generate_content(self, topic: str, persona_file: str, angle: str) -> dict[str, Any]:
        persona = self.load_persona(persona_file)
        response = self.parse_llm_response(self.call_llm(self.build_persona_prompt(persona, topic, angle)))
        full_content = f"{response['title']}\n\n{response['content']}"
        constraint_result = self.constraint_engine.check_content(full_content, persona)
        return {
            "persona_name": persona.get("persona", {}).get("name", "未知"),
            "persona_id": persona.get("account", {}).get("id", "unknown"),
            "topic": topic,
            "angle": angle,
            "title": response["title"],
            "content": response["content"],
            "tags": response["tags"],
            "constraint_result": constraint_result,
            "generated_at": datetime.now().isoformat(),
        }

    def generate_multi_account_content(
        self,
        topic: str,
        persona_files: list[str],
        angles_per_account: dict[str, str] | None = None,
    ) -> list[dict[str, Any]]:
        results = []
        for persona_file in persona_files:
            persona = self.load_persona(persona_file)
            account_id = persona.get("account", {}).get("id", Path(persona_file).stem)
            angle = (angles_per_account or {}).get(account_id) or persona.get("persona", {}).get("content_angles", ["经验分享"])[0]
            results.append(self.generate_content(topic, persona_file, angle))
        return results

    def save_content(self, content_result: dict[str, Any], output_dir: str | None = None) -> str:
        target_dir = Path(output_dir) if output_dir else Path.cwd() / "output"
        target_dir.mkdir(parents=True, exist_ok=True)
        output_file = target_dir / f"{content_result['persona_id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        output_file.write_text(
            "\n".join(
                [
                    f"# {content_result['title']}",
                    "",
                    f"**人设**: {content_result['persona_name']}",
                    f"**角度**: {content_result['angle']}",
                    "",
                    content_result["content"],
                    "",
                    " ".join(content_result["tags"]),
                ]
            ),
            encoding="utf-8",
        )
        return str(output_file)


def main() -> None:
    parser = argparse.ArgumentParser(description="兼容层：多账号内容生成器")
    parser.add_argument("--topic", type=str, required=True)
    parser.add_argument("--persona", type=str, default="personas/account_001.yaml")
    parser.add_argument("--angle", type=str, default="经验分享")
    parser.add_argument("--output-dir", type=str, default="output")
    args = parser.parse_args()

    generator = MultiAccountContentGenerator()
    result = generator.generate_content(args.topic, args.persona, args.angle)
    output_file = generator.save_content(result, args.output_dir)
    print(output_file)


if __name__ == "__main__":
    main()
