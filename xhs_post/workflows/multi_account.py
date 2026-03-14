from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from xhs_post.models import MultiAccountWorkflowRequest
from xhs_post.personas import load_personas
from xhs_post.storage import load_json, save_json
from xhs_post.topic import expand_keywords


def load_trending_analysis(config_path: Path) -> dict[str, Any]:
    return load_json(config_path)


def match_topic_to_personas(topic: str, trending_data: dict[str, Any], personas: list[dict[str, Any]]) -> dict[str, Any]:
    results: dict[str, Any] = {}
    hot_tags = trending_data.get("hot_tags", [])[:10]
    keywords = set(expand_keywords(topic))

    for persona_config in personas:
        account_id = persona_config["account"]["id"]
        persona = persona_config["persona"]
        tags = set(persona.get("tags", []))
        primary_domains = persona.get("content_domains", {}).get("primary", [])
        secondary_domains = persona.get("content_domains", {}).get("secondary", [])
        domain_text = " ".join(primary_domains + secondary_domains)

        score = 35
        score += min(sum(10 for tag in tags if any(keyword in tag for keyword in keywords)), 30)
        score += min(sum(8 for keyword in keywords if keyword in domain_text), 30)
        score = min(score, 95)

        if any(keyword in "".join(tags) for keyword in ["亲子", "带娃"]) and ("亲子" in topic or "带娃" in topic):
            angle = f"以{persona.get('occupation', '亲子博主')}身份分享带娃体验"
        elif any(keyword in "".join(tags) for keyword in ["酒店", "住宿"]) and ("酒店" in topic or "住宿" in topic):
            angle = "从住宿体验角度拆解这次主题"
        elif "本地" in "".join(tags):
            angle = "用本地人视角给出真实建议"
        else:
            angle = persona.get("content_angles", ["经验分享"])[0]

        results[account_id] = {
            "persona": persona,
            "match_score": score,
            "angle": angle,
            "hot_tags": hot_tags[:5],
        }

    return results


def generate_content_for_account(match_result: dict[str, Any], topic: str) -> str:
    persona = match_result["persona"]
    angle = match_result["angle"]
    hot_tags = match_result["hot_tags"]
    expressions = persona.get("expressions", {})
    greetings = expressions.get("greetings", ["大家好"])
    endings = expressions.get("endings", ["记得点赞收藏"])
    primary_domains = persona.get("content_domains", {}).get("primary", [])

    lines = [
        f"{greetings[0]}，今天聊 {topic}。",
        f"这篇从“{angle}”来展开，更贴近 {persona.get('name', '这个账号')} 的内容风格。",
        "我会先说结论，再补充场景和适合的人群。",
        "核心亮点：",
    ]

    if any("亲子" in domain for domain in primary_domains):
        lines.extend(["✨ 带娃友好", "👶 细节更重要，少折腾比堆卖点更有价值"])
    elif any("酒店" in domain or "住宿" in domain for domain in primary_domains):
        lines.extend(["🏨 先看住得顺不顺，再看拍照和配套", "🧭 位置和动线通常比堆设施更关键"])
    else:
        lines.extend(["📍 先看是否适合目标人群", "💡 再看实际体验是否稳定"])

    lines.append("适合这些人：")
    for domain in primary_domains[:3]:
        lines.append(f"• {domain}关注者")

    lines.append(f"{endings[0]}，评论区交流。")
    if hot_tags:
        tags = " ".join(f"#{item['tag']}" for item in hot_tags[:5])
        lines.append(f"\n🏷️ {tags}")

    return "\n\n".join(lines)


def validate_differentiation(contents: dict[str, Any]) -> dict[str, Any]:
    issues = []
    account_ids = list(contents.keys())

    for index, left in enumerate(account_ids):
        for right in account_ids[index + 1 :]:
            if contents[left]["angle"] == contents[right]["angle"]:
                issues.append(
                    {
                        "accounts": [left, right],
                        "similarity": 0.8,
                        "suggestion": f"建议调整 {right} 的内容角度",
                    }
                )

    return {"passed": not issues, "issues": issues}


def simulate_telegram_push(topic: str, matches: dict[str, Any]) -> str:
    lines = [f"📊 今日热点分析报告 ({datetime.now().strftime('%Y-%m-%d')})", f"\n主题: {topic}\n", "=" * 50]
    for account_id, match in matches.items():
        persona = match["persona"]
        lines.append(f"\n🎯 账号【{persona.get('name')}】")
        lines.append(f"   匹配度: {match['match_score']}%")
        lines.append(f"   建议角度: {match['angle']}")
        lines.append(f"   推荐标签: {', '.join(item['tag'] for item in match['hot_tags'][:3])}")

    lines.append("\n" + "=" * 50)
    lines.append("\n请选择今日发布策略:")
    lines.append("[为所有账号生成] [分别为每个账号选择] [跳过今日]")
    return "\n".join(lines)


def run_multi_account_workflow(request: MultiAccountWorkflowRequest) -> dict[str, Any]:
    trending_data = load_trending_analysis(request.input_path)
    personas = load_personas(request.personas_dir)
    matches = match_topic_to_personas(request.topic, trending_data, personas)

    contents: dict[str, Any] = {}
    for account_id, match in matches.items():
        contents[account_id] = {
            "title": f"【{match['persona']['name']}】{request.topic}",
            "content": generate_content_for_account(match, request.topic),
            "angle": match["angle"],
            "match_score": match["match_score"],
        }

    validation = validate_differentiation(contents)
    today = datetime.now().strftime("%Y-%m-%d")
    output_base = request.output_dir / today
    output_base.mkdir(parents=True, exist_ok=True)

    for account_id, content_data in contents.items():
        account_dir = output_base / account_id
        account_dir.mkdir(exist_ok=True)
        output_file = account_dir / "post_multi_account.md"
        output_file.write_text(
            "\n".join(
                [
                    f"# {content_data['title']}",
                    "",
                    f"**匹配度**: {content_data['match_score']}%",
                    "",
                    f"**内容角度**: {content_data['angle']}",
                    "",
                    "---",
                    "",
                    content_data["content"],
                ]
            ),
            encoding="utf-8",
        )

    summary = {
        "topic": request.topic,
        "date": today,
        "accounts": list(contents.keys()),
        "validation": validation,
        "matches": {
            key: {"match_score": value["match_score"], "angle": value["angle"]}
            for key, value in matches.items()
        },
        "telegram_preview": simulate_telegram_push(request.topic, matches),
    }
    save_json(output_base / "multi_account_summary.json", summary)
    return summary
