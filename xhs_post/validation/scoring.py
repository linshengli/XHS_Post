from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Any

from xhs_post.validation.standards import STANDARDS


def count_emoji(text: str) -> int:
    emoji_pattern = re.compile(
        "["
        u"\U0001F300-\U0001F9FF"
        u"\U0001FA00-\U0001FAFF"
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        "]+",
        flags=re.UNICODE,
    )
    return len(emoji_pattern.findall(text))


def check_title_quality(title: str) -> dict[str, Any]:
    score = 0
    issues = []
    strengths = []

    length = len(title)
    if length < STANDARDS["title_min_length"]:
        issues.append(f"标题太短 ({length}字，建议{STANDARDS['title_min_length']}+)")
    elif length > STANDARDS["title_max_length"]:
        issues.append(f"标题太长 ({length}字，建议{STANDARDS['title_max_length']}字以内)")
    else:
        strengths.append(f"标题长度合适 ({length}字)")
        score += 10

    if re.search(r"\d+", title):
        strengths.append("包含数字（增加可信度）")
        score += 15

    emoji_count = count_emoji(title)
    if emoji_count > 0:
        strengths.append(f"使用 Emoji ({emoji_count}个)")
        score += 10
    else:
        issues.append("缺少 Emoji")

    pain_points = ["懒人", "避坑", "省钱", "必看", "攻略", "指南", "新手", "第一次"]
    if any(point in title for point in pain_points):
        strengths.append("包含痛点关键词")
        score += 15

    curiosity_words = ["揭秘", "没想到", "居然", "原来", "秘密", "真相"]
    if any(word in title for word in curiosity_words):
        strengths.append("制造好奇心")
        score += 10

    if "!" in title or "❗" in title or "🔥" in title:
        strengths.append("使用强调符号")
        score += 5

    return {
        "title": title,
        "score": min(score, 50),
        "max_score": 50,
        "strengths": strengths,
        "issues": issues,
    }


def check_body_quality(body: str) -> dict[str, Any]:
    score = 0
    issues = []
    strengths = []

    char_count = len(body)
    if char_count < STANDARDS["content_min_chars"]:
        issues.append(f"正文字数太少 ({char_count}字，建议{STANDARDS['content_min_chars']}+)")
    elif char_count > STANDARDS["content_max_chars"]:
        issues.append(f"正文字数太多 ({char_count}字，建议{STANDARDS['content_max_chars']}字以内)")
    else:
        strengths.append(f"正文字数合适 ({char_count}字)")
        score += 20

    emoji_count = count_emoji(body)
    if emoji_count < STANDARDS["emoji_min_count"]:
        issues.append(f"Emoji 太少 ({emoji_count}个，建议{STANDARDS['emoji_min_count']}+)")
    elif emoji_count > STANDARDS["emoji_max_count"]:
        issues.append(f"Emoji 太多 ({emoji_count}个，建议{STANDARDS['emoji_max_count']}个以内)")
    else:
        strengths.append(f"Emoji 密度合适 ({emoji_count}个)")
        score += 15

    paragraphs = [paragraph for paragraph in body.split("\n") if paragraph.strip()]
    if len(paragraphs) < STANDARDS["paragraph_min_count"]:
        issues.append(f"段落太少 ({len(paragraphs)}段，建议{STANDARDS['paragraph_min_count']}段+)")
    else:
        strengths.append(f"段落结构清晰 ({len(paragraphs)}段)")
        score += 10

    if any(marker in body for marker in ["✅", "❌", "📍", "•", "-", "1.", "2."]):
        strengths.append("使用清单体（易读性高）")
        score += 15

    if any(cta in body for cta in ["评论", "点赞", "收藏", "关注", "留言", "私信"]):
        strengths.append("包含行动号召")
        score += 10

    if any(value in body for value in ["推荐", "建议", "必看", "注意", " tips", "攻略"]):
        strengths.append("提供实用价值")
        score += 15

    return {
        "score": min(score, 85),
        "max_score": 85,
        "strengths": strengths,
        "issues": issues,
        "char_count": char_count,
        "emoji_count": emoji_count,
        "paragraph_count": len(paragraphs),
    }


def check_tags_quality(tags: list[str]) -> dict[str, Any]:
    score = 0
    issues = []
    strengths = []
    tag_count = len(tags)

    if tag_count < STANDARDS["tags_min_count"]:
        issues.append(f"标签太少 ({tag_count}个，建议{STANDARDS['tags_min_count']}+)")
    elif tag_count > STANDARDS["tags_max_count"]:
        issues.append(f"标签太多 ({tag_count}个，建议{STANDARDS['tags_max_count']}个以内)")
    else:
        strengths.append(f"标签数量合适 ({tag_count}个)")
        score += 20

    joined_tags = " ".join(tags)
    if any(core in joined_tags for core in ["千岛湖", "攻略", "旅游", "旅行"]):
        strengths.append("包含核心关键词标签")
        score += 10

    if any(hot in joined_tags for hot in ["周末去哪儿", "江浙沪周边游", "杭州周边游"]):
        strengths.append("包含热门标签")
        score += 10

    return {
        "score": min(score, 40),
        "max_score": 40,
        "strengths": strengths,
        "issues": issues,
        "tags": tags,
    }


def check_originality(posts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    results = []
    for index, post1 in enumerate(posts):
        duplicates = []
        for inner_index, post2 in enumerate(posts):
            if index >= inner_index:
                continue
            similarity = SequenceMatcher(None, post1["body"], post2["body"]).ratio()
            if similarity > 0.8:
                duplicates.append({"file": post2["filename"], "similarity": round(similarity, 2)})
        results.append({"filename": post1["filename"], "high_similarity_with": duplicates})
    return results


def calculate_total_score(title_score: dict[str, Any], body_score: dict[str, Any], tags_score: dict[str, Any]) -> dict[str, Any]:
    total = title_score["score"] + body_score["score"] + tags_score["score"]
    max_total = title_score["max_score"] + body_score["max_score"] + tags_score["max_score"]

    grade = "F"
    if total >= max_total * 0.9:
        grade = "A+"
    elif total >= max_total * 0.8:
        grade = "A"
    elif total >= max_total * 0.7:
        grade = "B"
    elif total >= max_total * 0.6:
        grade = "C"
    elif total >= max_total * 0.5:
        grade = "D"

    return {
        "total": total,
        "max": max_total,
        "percentage": round(total / max_total * 100, 1),
        "grade": grade,
    }
