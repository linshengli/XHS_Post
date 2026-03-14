from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from xhs_post.personas import load_personas


INSERTION_MODES = {
    "route_anchor": {"keywords": ["附近", "方便", "顺路", "车程", "分钟", "位置"]},
    "problem_solver": {"keywords": ["所以", "解决了", "终于", "轻松", "不累", "省心"]},
    "experience_evidence": {"keywords": ["有", "可以", "还能", "特别", "喜欢", "玩了"]},
    "contrast_decision": {"keywords": ["本来", "最后", "因为", "确实", "对比", "还是"]},
    "series_diary": {"keywords": ["今天", "昨天", "客人", "说", "日记", "Day"]},
}

AD_PHRASES_BLACKLIST = {
    "豪华装修": "装修很新",
    "五星级服务": "服务很贴心",
    "尊享体验": "体验很好",
    "欢迎入住": "推荐给大家",
    "预订从速": "建议提前订",
    "高端大气": "环境不错",
    "奢华": "舒适",
    "顶级": "不错",
    "最": "很",
    "第一": "前列",
    "限时折扣": "现在有活动",
    "价格优惠": "性价比不错",
    "点击链接": "可以私信",
    "私信优惠": "私信有惊喜",
}


def analyze_insertion_mode(content: str, preferred_modes: list[str]) -> str:
    for mode_name in preferred_modes:
        if mode_name not in INSERTION_MODES:
            continue
        keyword_matches = sum(1 for keyword in INSERTION_MODES[mode_name]["keywords"] if keyword in content)
        if keyword_matches >= 2:
            return mode_name
    return preferred_modes[0] if preferred_modes else "route_anchor"


def check_hotel_mentions(content: str) -> dict[str, Any]:
    mention_count = len(re.findall(r"酒店|民宿|度假村|住宿", content))
    paragraphs = content.split("\n\n")
    first_para_has_hotel = bool(paragraphs) and bool(re.search(r"酒店|民宿|度假村", paragraphs[0]))
    hotel_sentences = [
        sentence.strip()
        for sentence in re.split(r"[。！？!?]", content)
        if re.search(r"酒店|民宿|度假村", sentence)
    ]
    return {
        "mention_count": mention_count,
        "first_para_has_hotel": first_para_has_hotel,
        "hotel_sentences": hotel_sentences,
    }


def replace_ad_phrases(content: str) -> tuple[str, int, list[str]]:
    replaced_count = 0
    replaced_phrases = []
    optimized_content = content
    for ad_phrase, natural_phrase in AD_PHRASES_BLACKLIST.items():
        if ad_phrase in optimized_content:
            optimized_content = optimized_content.replace(ad_phrase, natural_phrase)
            replaced_count += 1
            replaced_phrases.append(ad_phrase)
    return optimized_content, replaced_count, replaced_phrases


def optimize_content(content: str, persona_config: dict[str, Any]) -> dict[str, Any]:
    persona = persona_config.get("persona", {})
    hotel_insertion = persona.get("hotel_insertion", {})
    preferred_modes = hotel_insertion.get("preferred_modes", ["route_anchor"])
    max_mentions = hotel_insertion.get("max_mentions_per_post", 3)
    avoid_first_para = hotel_insertion.get("avoid_first_paragraph", True)

    mention_analysis = check_hotel_mentions(content)
    current_mode = analyze_insertion_mode(content, preferred_modes)
    optimized_content, replaced_count, replaced_phrases = replace_ad_phrases(content)

    issues = []
    optimizations = []
    if replaced_count > 0:
        optimizations.append(f"替换{replaced_count}个广告话术：{', '.join(replaced_phrases)}")
        issues.append("包含广告话术")
    if mention_analysis["mention_count"] > max_mentions:
        issues.append(f"酒店提及过频 ({mention_analysis['mention_count']}次，建议{max_mentions}次以内)")
    if avoid_first_para and mention_analysis["first_para_has_hotel"]:
        issues.append("第一段出现酒店名")
    if current_mode not in preferred_modes:
        issues.append(f"植入模式不匹配 (当前：{current_mode}, 推荐：{preferred_modes[0]})")

    detail_keywords = ["早餐", "儿童", "泳池", "乐园", "房间", "湖景", "活动", "服务"]
    has_details = any(keyword in optimized_content for keyword in detail_keywords)
    if not has_details:
        issues.append("缺少具体细节")

    return {
        "original_content": content,
        "optimized_content": optimized_content,
        "issues": issues,
        "optimizations": optimizations,
        "insertion_mode": current_mode,
        "mention_count": mention_analysis["mention_count"],
        "has_details": has_details,
    }


def find_matching_persona(file_name: str, personas: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    file_lower = file_name.lower()
    if "攻略" in file_lower or "guide" in file_lower:
        return personas.get("account_001")
    if "亲子" in file_lower or "family" in file_lower or "遛娃" in file_lower:
        return personas.get("account_002")
    if "本地" in file_lower or "local" in file_lower:
        return personas.get("account_003")
    if "酒店" in file_lower or "hotel" in file_lower:
        return personas.get("account_004")
    return next(iter(personas.values()), None)


def load_persona_map(personas_dir: Path) -> dict[str, dict[str, Any]]:
    personas = {}
    for config in load_personas(personas_dir):
        personas[config["account"]["id"]] = config
    return personas
