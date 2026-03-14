#!/usr/bin/env python3
"""
02_analyze_trending.py - 分析小红书热门内容特征（支持主题筛选）

用法:
  # 分析热点数据 (支持主题筛选)
  python scripts/02_analyze_trending.py --topic "主题关键词"
  
  # 带自定义关键词扩展
  python scripts/02_analyze_trending.py --topic "千岛湖骑行" --keywords "自行车,绿道,单车"

示例:
  python scripts/02_analyze_trending.py --topic "千岛湖亲子酒店"
  python scripts/02_analyze_trending.py --topic "千岛湖骑行"
  python scripts/02_analyze_trending.py --topic "北京美食探店"
"""

import os
import json
import argparse
from pathlib import Path
from collections import Counter
import re

# 配置路径
BASE_DIR = Path(os.path.expanduser("~/XHS_Post"))
INPUT_DIR = BASE_DIR / "xhs_post_from_search" / "jsonl"
OUTPUT_FILE = BASE_DIR / "config" / "trending_analysis.json"

# 高赞阈值
HIGH_LIKE_THRESHOLD = 3000

# 内置关键词映射表
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
    "购物": ["购物", "买买买", "商场", "集市", "特产", "伴手礼", " shopping"],
    "交通": ["交通", "地铁", "公交", "高铁", "机场", "自驾", "停车", "租车"],
}


def expand_keywords(topic: str) -> list:
    """为主题自动扩展关键词"""
    keywords = []
    
    # 从映射表中扩展
    for key, values in KEYWORD_EXPANSION.items():
        if key in topic:
            keywords.extend(values)
    
    # 添加主题原词（按空格或常见分隔符拆分）
    topic_words = re.split(r'[,\s]+', topic)
    keywords.extend(topic_words)
    
    # 去重
    return list(set(keywords))


def filter_posts_by_source_keyword(posts: list, topic: str) -> list:
    """按 source_keyword 过滤笔记 - 这是最可靠的主题匹配方式
    
    爬虫在抓取数据时会记录 source_keyword（搜索关键词）
    例如：搜索"千岛湖"时，所有抓取的笔记 source_keyword 都是"千岛湖"
    """
    filtered = []
    topic_lower = topic.lower()
    
    # 从 topic 中提取核心地名/主题词
    # 例如 "千岛湖亲子酒店" → ["千岛湖"]
    # 例如 "北京美食探店" → ["北京"]
    core_topics = []
    
    # 常见地名/主题词提取（可扩展）
    # 优先匹配长词
    if '千岛湖' in topic:
        core_topics.append('千岛湖')
    elif '西双版纳' in topic:
        core_topics.append('西双版纳')
    elif '北京' in topic:
        core_topics.append('北京')
    elif '上海' in topic:
        core_topics.append('上海')
    elif '杭州' in topic:
        core_topics.append('杭州')
    else:
        # 如果没有匹配到预设地名，使用 topic 的前两个字作为核心词
        # 例如 "美食探店" → "美食"
        core_topics.append(topic[:2])
    
    for post in posts:
        source_keyword = post.get('source_keyword', '')
        
        # 优先使用 source_keyword 匹配
        if source_keyword:
            source_lower = source_keyword.lower()
            # 检查 source_keyword 是否包含核心主题词
            if any(core in source_lower or source_lower in core for core in core_topics):
                filtered.append(post)
                continue
        
        # 如果 source_keyword 为空或不匹配，回退到内容匹配
        text = (
            post.get("title", "") + " " +
            post.get("desc", "") + " " +
            post.get("tag_list", "")
        )
        
        if any(core in text for core in core_topics):
            filtered.append(post)
    
    return filtered


def filter_posts_by_topic(posts: list, keywords: list) -> list:
    """筛选与主题相关的笔记（在 source_keyword 过滤后的二次筛选）
    
    使用严格模式：必须包含主题的核心词（地名/主要事物），而不仅仅是通用词如"攻略"、"推荐"
    """
    filtered = []
    
    # 通用词（不单独作为筛选依据）
    generic_words = {'攻略', '指南', '推荐', '教程', '分享', '心得', '体验', '日记', '玩法', '超全', '详细', '必看', '路线'}
    
    # 核心词是排除通用词后的关键词
    core_keywords = [kw for kw in keywords if kw not in generic_words and len(kw) > 1]
    
    for post in posts:
        # 检查标题、正文、标签
        text = (
            post.get("title", "") + " " +
            post.get("desc", "") + " " +
            post.get("tag_list", "")
        )
        
        # 必须包含至少一个核心关键词
        has_core = any(kw in text for kw in core_keywords)
        if not has_core:
            continue
        
        # 并且包含任何扩展关键词
        if any(kw in text for kw in keywords):
            filtered.append(post)
    
    return filtered


def parse_like_count(like_str: str) -> int:
    """解析点赞数字符串（支持 '8.1 万' 格式）"""
    if not like_str:
        return 0
    try:
        # 处理 "8.1 万" 格式
        if "万" in like_str:
            num_str = like_str.replace("万", "").strip()
            return int(float(num_str) * 10000)
        # 处理纯数字
        return int(like_str)
    except (ValueError, TypeError):
        return 0


def parse_tags(tag_string: str) -> list:
    """解析标签字符串为列表"""
    if not tag_string:
        return []
    # 处理逗号分隔的标签
    tags = [tag.strip() for tag in tag_string.split(',')]
    return [tag for tag in tags if tag]


def extract_title_patterns(titles: list) -> dict:
    """分析标题模式和公式"""
    patterns = {
        "numeric": [],  # 数字式标题
        "contrast": [],  # 对比式标题
        "pain_point": [],  # 痛点式标题
        "curiosity": [],  # 好奇式标题
        "value": []  # 价值式标题
    }
    
    for title in titles:
        # 数字式：包含数字
        if re.search(r'\d+', title):
            patterns["numeric"].append(title)
        
        # 对比式：包含对比词
        contrast_words = ['从...到', '别再', '对比', 'vs', '以前', '现在', '曾经', '如今']
        if any(word in title for word in contrast_words):
            patterns["contrast"].append(title)
        
        # 痛点式：包含问题词
        pain_words = ['发愁', '困扰', '问题', '必看', '解决', '头疼', '烦恼']
        if any(word in title for word in pain_words):
            patterns["pain_point"].append(title)
        
        # 好奇式：包含好奇词
        curiosity_words = ['震惊', '原来', '秘密', '没想到', '居然', '竟然', '揭秘']
        if any(word in title for word in curiosity_words):
            patterns["curiosity"].append(title)
        
        # 价值式：包含价值词
        value_words = ['免费', '分享', '教程', '攻略', '干货', '指南', '推荐']
        if any(word in title for word in value_words):
            patterns["value"].append(title)
    
    return patterns


def analyze_content_structure(descriptions: list) -> dict:
    """分析内容结构特征"""
    structures = {
        "avg_length": 0,
        "with_emoji": 0,
        "with_checklist": 0,
        "with_sections": 0,
        "common_emojis": [],
        "section_markers": []
    }
    
    if not descriptions:
        return structures
    
    # 计算平均长度
    lengths = [len(desc) for desc in descriptions if desc]
    structures["avg_length"] = sum(lengths) / len(lengths) if lengths else 0
    
    # 统计带 emoji 的内容
    emoji_pattern = re.compile(r'[\U00010000-\U00010ffff]')
    structures["with_emoji"] = sum(1 for desc in descriptions if emoji_pattern.search(desc))
    
    # 统计带清单的内容
    structures["with_checklist"] = sum(1 for desc in descriptions if '✅' in desc or '❌' in desc or '-' in desc or '•' in desc)
    
    # 统计分段内容
    structures["with_sections"] = sum(1 for desc in descriptions if desc.count('\n') >= 4)
    
    # 统计常见 emoji
    all_emojis = []
    for desc in descriptions:
        emojis = emoji_pattern.findall(desc)
        all_emojis.extend(emojis)
    
    emoji_counter = Counter(all_emojis)
    structures["common_emojis"] = [emoji for emoji, count in emoji_counter.most_common(10)]
    
    return structures


def extract_value_points(posts: list) -> list:
    """从帖子中提取价值点（亮点、特色） - 从 title 和 desc 提取"""
    value_points = []
    value_keywords = ['特别', '亮点', '特色', '值得', '推荐', '喜欢', '满意', '惊喜', '棒', '绝', '赞']
    for post in posts:
        text = post.get('title', '') + ' ' + post.get('desc', '')
        if len(text) < 30: continue
        for s in re.split(r'[,.!?.\n]', text):
            s = s.strip()
            if len(s) > 15 and any(kw in s for kw in value_keywords):
                clean = re.sub(r'#\w+[话题]#', '', s).strip()
                if clean and clean not in value_points:
                    value_points.append(clean)
    return value_points[:50]

def extract_scenes(posts: list) -> list:
    """从帖子中提取使用场景"""
    scenes = []
    
    # 场景相关关键词
    scene_keywords = ['适合', '推荐', '场景', '时候', '时候', '人群', '情况', '时候去', '最佳']
    
    for post in posts:
        desc = post.get('desc', '')
        if not desc:
            continue
        
        sentences = re.split(r'[,.!?.\n]', desc)
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 5 and any(kw in sentence for kw in scene_keywords):
                clean_sentence = sentence.strip()
                if clean_sentence and clean_sentence not in scenes:
                    scenes.append(clean_sentence)
    
    return scenes[:30]


def extract_pain_points(posts: list) -> list:
    """从帖子中提取痛点"""
    pain_points = []
    
    # 痛点相关关键词
    pain_keywords = ['头疼', '困扰', '烦恼', '担心', '害怕', '最怕', '问题', '难点', '坑', '雷', '愁']
    
    for post in posts:
        desc = post.get('desc', '')
        if not desc:
            continue
        
        sentences = re.split(r'[,.!?.\n]', desc)
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 5 and any(kw in sentence for kw in pain_keywords):
                clean_sentence = sentence.strip()
                if clean_sentence and clean_sentence not in pain_points:
                    pain_points.append(clean_sentence)
    
    return pain_points[:30]


def analyze_trending_posts(posts: list, topic: str) -> dict:
    """分析热门帖子特征"""
    print(f"📊 共加载 {len(posts)} 篇主题相关笔记")
    
    if not posts:
        print("❌ 没有主题相关的笔记可供分析")
        return None
    
    # 筛选高赞笔记
    high_like_posts = []
    for post in posts:
        liked_count = parse_like_count(post.get('liked_count', '0'))
        if liked_count >= HIGH_LIKE_THRESHOLD:
            high_like_posts.append(post)
    
    print(f"🔥 找到 {len(high_like_posts)} 篇高赞笔记 (点赞>={HIGH_LIKE_THRESHOLD})")
    
    if not high_like_posts:
        # 如果没有达到阈值的，降低标准
        print(f"⚠️  高赞笔记较少，降低阈值到 1000...")
        for post in posts:
            liked_count = parse_like_count(post.get('liked_count', '0'))
            if liked_count >= 1000:
                high_like_posts.append(post)
    
    # 如果仍然没有高赞笔记，使用所有笔记
    if not high_like_posts:
        print(f"⚠️  没有高赞笔记，使用所有 {len(posts)} 篇笔记进行分析...")
        high_like_posts = posts
    
    # 提取所有标签
    all_tags = []
    for post in high_like_posts:
        tags = parse_tags(post.get('tag_list', ''))
        all_tags.extend(tags)
    
    # 统计热门标签
    tag_counter = Counter(all_tags)
    hot_tags = tag_counter.most_common(30)
    
    # 提取标题
    titles = [post.get('title', '') for post in high_like_posts if post.get('title')]
    title_patterns = extract_title_patterns(titles)
    
    # 分析内容结构
    descriptions = [post.get('desc', '') for post in high_like_posts if post.get('desc')]
    content_structure = analyze_content_structure(descriptions)
    
    # 提取互动话术
    call_to_action_patterns = [
        "建议收藏", "赶紧试试", "评论区留言", "私信我", 
        "关注我", "点赞", "转发", "分享", "推荐", "必看"
    ]
    
    cta_found = []
    for desc in descriptions:
        for cta in call_to_action_patterns:
            if cta in desc:
                cta_found.append(cta)
    
    cta_counter = Counter(cta_found)
    
    # 分析最佳发布时间（如果有时间信息）
    time_analysis = {"morning": 0, "afternoon": 0, "evening": 0, "night": 0}
    for post in high_like_posts:
        time_ms = post.get('time', 0)
        if time_ms:
            hour = int((time_ms / 1000 / 3600) % 24)
            if 6 <= hour < 12:
                time_analysis["morning"] += 1
            elif 12 <= hour < 18:
                time_analysis["afternoon"] += 1
            elif 18 <= hour < 23:
                time_analysis["evening"] += 1
            else:
                time_analysis["night"] += 1
    
    # 提取特征数据（用于内容生成）- 从所有相关笔记中提取，而不仅仅是高赞
    # 因为很多高赞笔记是短视频/图片，desc 字段只有标签没有实质内容
    all_relevant_posts = posts  # 使用所有相关笔记
    top_posts_with_content = []
    for p in all_relevant_posts:
        text = p.get('title', '') + ' ' + p.get('desc', '')
        if len(text) > 100:  # 只选择有实质内容的笔记
            top_posts_with_content.append(p)
    
    # 按点赞排序，取前 30 篇有内容的笔记
    top_posts = sorted(top_posts_with_content, 
                       key=lambda x: parse_like_count(x.get('liked_count', '0')), 
                       reverse=True)[:30]
    
    
    # 测试提取价值点
    test_vps = extract_value_points(top_posts)
    if test_vps:
        print(f"   提取到 {len(test_vps)} 个价值点")
    
    features = {
        "titles": [p["title"] for p in top_posts if p.get("title")],
        "descriptions": [p["desc"] for p in top_posts if p.get("desc")],
        "tags": [tag for tag, _ in hot_tags[:20]],
        "value_points": extract_value_points(top_posts),
        "scenes": extract_scenes(top_posts),
        "pain_points": extract_pain_points(top_posts),
    }
    
    
    # 构建分析结果
    analysis = {
        "analysis_date": Path(INPUT_DIR).stem.split('_')[-1] if INPUT_DIR.exists() else "2026-03-15",
        "topic": topic,
        "keywords_used": expand_keywords(topic),
        "total_posts_analyzed": len(posts),
        "filtered_posts": len(filter_posts_by_topic(posts, expand_keywords(topic))),
        "high_performing_posts": len(high_like_posts),
        "like_threshold_used": HIGH_LIKE_THRESHOLD,
        
        "hot_tags": [
            {"tag": tag, "count": count} 
            for tag, count in hot_tags
        ],
        
        "title_patterns": {
            "numeric": title_patterns["numeric"][:5],
            "contrast": title_patterns["contrast"][:5],
            "pain_point": title_patterns["pain_point"][:5],
            "curiosity": title_patterns["curiosity"][:5],
            "value": title_patterns["value"][:5]
        },
        
        "content_structure": content_structure,
        
        "call_to_action": [
            {"cta": cta, "count": count}
            for cta, count in cta_counter.most_common(10)
        ],
        
        "time_distribution": time_analysis,
        
        "recommended_posting_times": [
            "早上 7:30-9:00 (早高峰)",
            "中午 12:00-14:00 (午休)",
            "晚上 18:00-20:00 (晚高峰)",
            "晚上 21:00-23:00 (睡前)"
        ],
        
        "features": features,  # 用于内容生成的特征数据
        
        "key_insights": [
            f"高赞笔记平均字数：{content_structure['avg_length']:.0f} 字",
            f"{content_structure['with_emoji']}篇使用 Emoji 表情",
            f"{content_structure['with_checklist']}篇使用清单体",
            f"最常用 Emoji: {', '.join(content_structure['common_emojis'][:5]) if content_structure['common_emojis'] else '无'}",
        ]
    }
    
    return analysis


def load_jsonl_files(input_dir: Path) -> list:
    """加载目录下所有 JSONL 文件"""
    posts = []
    
    if not input_dir.exists():
        print(f"⚠️  输入目录不存在：{input_dir}")
        return posts
    
    for file_path in input_dir.glob("*.jsonl"):
        print(f"  加载：{file_path.name}")
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        post = json.loads(line)
                        posts.append(post)
                    except json.JSONDecodeError as e:
                        print(f"⚠️  JSON 解析错误：{e}")
    
    return posts


def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='小红书热门内容分析工具 - 支持主题筛选')
    parser.add_argument('--topic', type=str, required=True,
                        help='要分析的主题关键词（必填）')
    parser.add_argument('--keywords', type=str, default=None,
                        help='自定义关键词扩展（可选，逗号分隔）')
    parser.add_argument('--output', type=str, default=None,
                        help='输出文件路径（可选）')
    
    args = parser.parse_args()
    
    # 设置输出文件
    output_file = Path(args.output) if args.output else OUTPUT_FILE
    
    print("=" * 60)
    print("📈 小红书热门内容分析工具 - 主题筛选模式")
    print("=" * 60)
    print(f"\n🎯 分析主题：{args.topic}")
    
    # 扩展关键词
    keywords = expand_keywords(args.topic)
    if args.keywords:
        custom_keywords = [kw.strip() for kw in args.keywords.split(',')]
        keywords.extend(custom_keywords)
        print(f"🔑 自定义关键词：{custom_keywords}")
    
    keywords = list(set(keywords))
    print(f"🔑 扩展后关键词 ({len(keywords)}个): {', '.join(keywords[:10])}...")
    
    # 加载数据
    print(f"\n📂 加载数据：{INPUT_DIR}/*.jsonl")
    posts = load_jsonl_files(INPUT_DIR)
    
    if not posts:
        print("❌ 未找到任何数据")
        return None
    
    # Step 1: 按 source_keyword 过滤（最可靠的主题匹配）
    print(f"\n🔍 Step 1: 按 source_keyword 筛选主题相关数据...")
    posts_by_source = filter_posts_by_source_keyword(posts, args.topic)
    print(f"   找到 {len(posts_by_source)} 篇与 '{args.topic}' 相关的笔记 (原始：{len(posts)}篇)")
    
    if not posts_by_source:
        print(f"❌ 错误：数据中没有 source_keyword 为 '{args.topic}' 的笔记")
        print(f"   建议：")
        print(f"   1. 检查数据文件中的 source_keyword 字段")
        print(f"   2. 使用 --topic 参数匹配现有的 source_keyword")
        print(f"   3. 或者爬取 '{args.topic}' 主题的新数据")
        return None
    
    # Step 2: 按关键词二次筛选（更精确的内容匹配）
    print(f"\n🔍 Step 2: 按关键词二次筛选内容...")
    filtered_posts = filter_posts_by_topic(posts_by_source, keywords)
    print(f"   筛选后剩余 {len(filtered_posts)} 篇笔记")
    
    if not filtered_posts:
        print(f"⚠️  警告：source_keyword 匹配成功，但内容关键词筛选后无结果")
        print(f"   回退到使用 source_keyword 匹配的所有笔记...")
        filtered_posts = posts_by_source
    
    # 分析
    print("\n🔍 开始分析...")
    analysis = analyze_trending_posts(filtered_posts, args.topic)
    
    if not analysis:
        print("❌ 分析失败")
        return None
    
    # 保存结果
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'=' * 60}")
    print("✅ 热门内容分析完成！")
    print(f"\n📊 关键发现:")
    for insight in analysis['key_insights']:
        print(f"  • {insight}")
    
    print(f"\n🏷️  Top 10 热门标签:")
    for i, tag_info in enumerate(analysis['hot_tags'][:10], 1):
        print(f"  {i}. #{tag_info['tag']} ({tag_info['count']}次)")
    
    print(f"\n💾 结果已保存到：{output_file}")
    print(f"{'=' * 60}")
    
    return analysis


if __name__ == "__main__":
    main()
