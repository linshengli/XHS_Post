from __future__ import annotations

import re
from typing import Any


KEYWORD_EXPANSION = {
    "亲子": ["亲子", "带娃", "遛娃", "儿童", "小朋友", "宝妈", "宝宝", "家庭", "孩子", "小孩"],
    "住宿": ["住宿", "酒店", "民宿", "度假村", "宾馆", "客栈", "公寓", "入住"],
    "酒店": ["酒店", "住宿", "民宿", "度假村", "宾馆", "入住", "客房", "房型"],
    "骑行": ["骑行", "自行车", "绿道", "骑车", "单车", "山地车", "公路车", "骑行路线"],
    "美食": ["美食", "餐厅", "小吃", "吃饭", "探店", "打卡", "美食推荐", "当地美食", "特色菜"],
    "攻略": ["攻略", "指南", "路线", "玩法", "推荐", "教程", "必看", "超全", "详细"],
    "旅游": ["旅游", "旅行", "游玩", "景点", "景区", "打卡地", "目的地", "出游"],
    "户外": ["户外", "露营", "徒步", "爬山", "自然", "野外", "露营基地"],
    "摄影": ["摄影", "拍照", "出片", "机位", "写真", "约拍", "摄影技巧"],
    "购物": ["购物", "买买买", "商场", "集市", "特产", "伴手礼", "shopping"],
    "交通": ["交通", "地铁", "公交", "高铁", "机场", "自驾", "停车", "租车"],
}

GENERIC_WORDS = {"攻略", "指南", "推荐", "教程", "分享", "心得", "体验", "日记", "玩法", "超全", "详细", "必看", "路线"}


def expand_keywords(topic: str) -> list[str]:
    keywords: list[str] = []
    for key, values in KEYWORD_EXPANSION.items():
        if key in topic:
            keywords.extend(values)
    keywords.extend(re.split(r"[,\s]+", topic))
    return list({keyword for keyword in keywords if keyword})


def extract_core_topics(topic: str) -> list[str]:
    presets = ["千岛湖", "西双版纳", "北京", "上海", "杭州"]
    for preset in presets:
        if preset in topic:
            return [preset]
    return [topic[:2]]


def filter_posts_by_source_keyword(posts: list[dict[str, Any]], topic: str) -> list[dict[str, Any]]:
    filtered = []
    core_topics = extract_core_topics(topic)

    for post in posts:
        source_keyword = post.get("source_keyword", "")
        if source_keyword and any(core in source_keyword or source_keyword in core for core in core_topics):
            filtered.append(post)
            continue

        text = " ".join(
            [
                post.get("title", ""),
                post.get("desc", ""),
                post.get("tag_list", ""),
            ]
        )
        if any(core in text for core in core_topics):
            filtered.append(post)

    return filtered


def filter_posts_by_topic(posts: list[dict[str, Any]], keywords: list[str]) -> list[dict[str, Any]]:
    filtered = []
    core_keywords = [keyword for keyword in keywords if keyword not in GENERIC_WORDS and len(keyword) > 1]

    for post in posts:
        text = " ".join(
            [
                post.get("title", ""),
                post.get("desc", ""),
                post.get("tag_list", ""),
            ]
        )
        if not any(keyword in text for keyword in core_keywords):
            continue
        if any(keyword in text for keyword in keywords):
            filtered.append(post)

    return filtered


def parse_like_count(like_str: str | None) -> int:
    if not like_str:
        return 0
    try:
        if "万" in like_str:
            return int(float(like_str.replace("万", "").strip()) * 10000)
        return int(like_str)
    except (TypeError, ValueError):
        return 0
