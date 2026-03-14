#!/usr/bin/env python3
"""
小红书笔记质量验证与评分脚本
检查标准：
1. 标题吸引力（数字、emoji、痛点、好奇心）
2. 正文结构（开头钩子、价值点、行动号召）
3. 标签相关性
4. Emoji 使用密度
5. 内容原创性（重复度检测）
6. 字数合规性
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime
from difflib import SequenceMatcher

# 配置
INPUT_DIR = Path("/home/tbxsx/XHS_Post/generated_posts/2026-03-15")
OUTPUT_FILE = INPUT_DIR / "quality_report.json"

# 小红书标准
STANDARDS = {
    "title_min_length": 10,
    "title_max_length": 20,
    "content_min_chars": 300,
    "content_max_chars": 1000,
    "emoji_min_count": 3,
    "emoji_max_count": 15,
    "tags_min_count": 5,
    "tags_max_count": 15,
    "paragraph_min_count": 3,
}


def load_post(file_path: Path) -> dict:
    """加载笔记文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 解析标题
    title_match = re.search(r'^#\s*🔥\s*标题选项.*?\n((?:\d+\..*?\n)+)', content, re.DOTALL)
    titles = []
    if title_match:
        title_lines = title_match.group(1).strip().split('\n')
        titles = [re.sub(r'^\d+\.\s*', '', line).strip() for line in title_lines if line.strip()]
    
    # 解析标签
    tags_pattern = re.compile(r'##\s*🏷️\s*推荐标签\s*\n([\s\S]*?)(?=##|\Z)')
    tags_match = tags_pattern.search(content)
    tags = []
    if tags_match:
        tags_text = tags_match.group(0)
        tags = re.findall(r'#\w+', tags_text)
    
    # 解析正文
    body_pattern = re.compile(r'##\s*✍️\s*正文\s*\n([\s\S]*?)(?=##\s*⏰|\Z)')
    body_match = body_pattern.search(content)
    body = ""
    if body_match:
        body = body_match.group(1).strip()
    
    # 解析发布时间
    time_pattern = re.compile(r'##\s*⏰\s*最佳发布时间\s*\n(.+?)(?:\n|$)')
    time_match = time_pattern.search(content)
    best_time = ""
    if time_match:
        best_time = time_match.group(1).strip()
    
    return {
        "filename": file_path.name,
        "titles": titles,
        "tags": tags,
        "body": body,
        "best_time": best_time,
        "full_content": content
    }


def count_emoji(text: str) -> int:
    """统计 Emoji 数量"""
    emoji_pattern = re.compile("["
        u"\U0001F300-\U0001F9FF"
        u"\U0001FA00-\U0001FAFF"
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE)
    return len(emoji_pattern.findall(text))


def check_title_quality(title: str) -> dict:
    """检查标题质量"""
    score = 0
    issues = []
    strengths = []
    
    # 长度检查
    length = len(title)
    if length < STANDARDS["title_min_length"]:
        issues.append(f"标题太短 ({length}字，建议{STANDARDS['title_min_length']}+)")
    elif length > STANDARDS["title_max_length"]:
        issues.append(f"标题太长 ({length}字，建议{STANDARDS['title_max_length']}字以内)")
    else:
        strengths.append(f"标题长度合适 ({length}字)")
        score += 10
    
    # 数字检查
    if re.search(r'\d+', title):
        strengths.append("包含数字（增加可信度）")
        score += 15
    
    # Emoji 检查
    emoji_count = count_emoji(title)
    if emoji_count > 0:
        strengths.append(f"使用 Emoji ({emoji_count}个)")
        score += 10
    else:
        issues.append("缺少 Emoji")
    
    # 痛点词检查
    pain_points = ['懒人', '避坑', '省钱', '必看', '攻略', '指南', '新手', '第一次']
    if any(p in title for p in pain_points):
        strengths.append("包含痛点关键词")
        score += 15
    
    # 好奇心检查
    curiosity_words = ['揭秘', '没想到', '居然', '原来', '秘密', '真相']
    if any(c in title for c in curiosity_words):
        strengths.append("制造好奇心")
        score += 10
    
    # 感叹号/强调检查
    if '!' in title or '❗' in title or '🔥' in title:
        strengths.append("使用强调符号")
        score += 5
    
    return {
        "title": title,
        "score": min(score, 50),
        "max_score": 50,
        "strengths": strengths,
        "issues": issues
    }


def check_body_quality(body: str) -> dict:
    """检查正文质量"""
    score = 0
    issues = []
    strengths = []
    
    # 字数检查
    char_count = len(body)
    if char_count < STANDARDS["content_min_chars"]:
        issues.append(f"正文字数太少 ({char_count}字，建议{STANDARDS['content_min_chars']}+)")
    elif char_count > STANDARDS["content_max_chars"]:
        issues.append(f"正文字数太多 ({char_count}字，建议{STANDARDS['content_max_chars']}字以内)")
    else:
        strengths.append(f"正文字数合适 ({char_count}字)")
        score += 20
    
    # Emoji 密度检查
    emoji_count = count_emoji(body)
    if emoji_count < STANDARDS["emoji_min_count"]:
        issues.append(f"Emoji 太少 ({emoji_count}个，建议{STANDARDS['emoji_min_count']}+)")
    elif emoji_count > STANDARDS["emoji_max_count"]:
        issues.append(f"Emoji 太多 ({emoji_count}个，建议{STANDARDS['emoji_max_count']}个以内)")
    else:
        strengths.append(f"Emoji 密度合适 ({emoji_count}个)")
        score += 15
    
    # 段落检查
    paragraphs = [p for p in body.split('\n') if p.strip()]
    if len(paragraphs) < STANDARDS["paragraph_min_count"]:
        issues.append(f"段落太少 ({len(paragraphs)}段，建议{STANDARDS['paragraph_min_count']}段+)")
    else:
        strengths.append(f"段落结构清晰 ({len(paragraphs)}段)")
        score += 10
    
    # 清单体检查
    if any(marker in body for marker in ['✅', '❌', '📍', '•', '-', '1.', '2.']):
        strengths.append("使用清单体（易读性高）")
        score += 15
    
    # 行动号召检查
    cta_words = ['评论', '点赞', '收藏', '关注', '留言', '私信']
    if any(cta in body for cta in cta_words):
        strengths.append("包含行动号召")
        score += 10
    
    # 价值点检查
    value_patterns = ['推荐', '建议', '必看', '注意', ' tips', '攻略']
    if any(v in body for v in value_patterns):
        strengths.append("提供实用价值")
        score += 15
    
    return {
        "score": min(score, 85),
        "max_score": 85,
        "strengths": strengths,
        "issues": issues,
        "char_count": char_count,
        "emoji_count": emoji_count,
        "paragraph_count": len(paragraphs)
    }


def check_tags_quality(tags: list) -> dict:
    """检查标签质量"""
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
    
    # 检查是否有核心标签
    core_tags = ['千岛湖', '攻略', '旅游', '旅行']
    if any(core in ' '.join(tags) for core in core_tags):
        strengths.append("包含核心关键词标签")
        score += 10
    
    # 检查是否有热门标签
    hot_tags = ['周末去哪儿', '江浙沪周边游', '杭州周边游']
    if any(hot in ' '.join(tags) for hot in hot_tags):
        strengths.append("包含热门标签")
        score += 10
    
    return {
        "score": min(score, 40),
        "max_score": 40,
        "strengths": strengths,
        "issues": issues,
        "tags": tags
    }


def check_originality(posts: list) -> dict:
    """检查内容重复度"""
    results = []
    
    for i, post1 in enumerate(posts):
        duplicates = []
        for j, post2 in enumerate(posts):
            if i >= j:
                continue
            similarity = SequenceMatcher(None, post1['body'], post2['body']).ratio()
            if similarity > 0.8:
                duplicates.append({
                    "file": post2['filename'],
                    "similarity": round(similarity, 2)
                })
        
        results.append({
            "filename": post1['filename'],
            "high_similarity_with": duplicates
        })
    
    return results


def calculate_total_score(title_score: dict, body_score: dict, tags_score: dict) -> dict:
    """计算总分"""
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
        "grade": grade
    }


def main():
    print("=" * 60)
    print("📊 小红书笔记质量验证与评分报告")
    print("=" * 60)
    print(f"检查目录：{INPUT_DIR}")
    print(f"检查时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 加载所有笔记
    posts_data = []
    for f in sorted(INPUT_DIR.glob("千岛湖旅游攻略_*.md")):
        posts_data.append(load_post(f))
    
    if not posts_data:
        print("❌ 未找到任何笔记文件！")
        return
    
    print(f"📁 加载 {len(posts_data)} 篇笔记\n")
    
    # 检查重复度
    print("🔍 检查内容重复度...")
    originality_results = check_originality(posts_data)
    high_dup_count = sum(1 for r in originality_results if r['high_similarity_with'])
    print(f"⚠️ 发现 {high_dup_count} 篇笔记存在高重复度问题\n")
    
    # 逐篇评分
    results = []
    for i, post in enumerate(posts_data, 1):
        print(f"[{i}/{len(posts_data)}] {post['filename']}")
        
        # 选第一个标题评分
        title_to_check = post['titles'][0] if post['titles'] else ""
        
        title_score = check_title_quality(title_to_check)
        body_score = check_body_quality(post['body'])
        tags_score = check_tags_quality(post['tags'])
        total_score = calculate_total_score(title_score, body_score, tags_score)
        
        result = {
            "filename": post['filename'],
            "selected_title": title_to_check,
            "all_titles": post['titles'],
            "tags": post['tags'],
            "title_score": title_score,
            "body_score": body_score,
            "tags_score": tags_score,
            "total_score": total_score,
            "originality": originality_results[i-1]
        }
        results.append(result)
        
        # 打印摘要
        status = "✅" if total_score["percentage"] >= 70 else "⚠️"
        print(f"  {status} 总分：{total_score['total']}/{total_score['max']} ({total_score['percentage']}%) - 等级：{total_score['grade']}")
        if title_score['issues']:
            print(f"     标题问题：{', '.join(title_score['issues'])}")
        if body_score['issues']:
            print(f"     正文问题：{', '.join(body_score['issues'])}")
        if tags_score['issues']:
            print(f"     标签问题：{', '.join(tags_score['issues'])}")
        print()
    
    # 生成报告
    report = {
        "report_date": datetime.now().isoformat(),
        "total_posts": len(posts_data),
        "summary": {
            "avg_score": round(sum(r['total_score']['percentage'] for r in results) / len(results), 1),
            "grade_distribution": {},
            "high_dup_count": high_dup_count
        },
        "posts": results
    }
    
    # 统计等级分布
    for r in results:
        grade = r['total_score']['grade']
        report['summary']['grade_distribution'][grade] = report['summary']['grade_distribution'].get(grade, 0) + 1
    
    # 保存报告
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print("=" * 60)
    print("📊 总体统计")
    print("=" * 60)
    print(f"平均分数：{report['summary']['avg_score']}%")
    print(f"等级分布：{report['summary']['grade_distribution']}")
    print(f"高重复度笔记：{high_dup_count} 篇")
    print()
    print(f"💾 完整报告已保存到：{OUTPUT_FILE}")
    
    # 生成改进建议
    print("\n" + "=" * 60)
    print("💡 改进建议")
    print("=" * 60)
    
    # 检查是否所有标题都一样
    all_titles = [r['selected_title'] for r in results]
    if len(set(all_titles)) == 1:
        print("❌ 严重问题：所有笔记标题完全相同！需要修复生成脚本")
    
    if high_dup_count > 0:
        print(f"⚠️ {high_dup_count} 篇笔记内容重复度过高，需要增加差异化")
    
    # 统计常见问题
    common_issues = {}
    for r in results:
        for issue in r['title_score']['issues'] + r['body_score']['issues'] + r['tags_score']['issues']:
            common_issues[issue] = common_issues.get(issue, 0) + 1
    
    if common_issues:
        print("\n常见问题 TOP 5:")
        for issue, count in sorted(common_issues.items(), key=lambda x: -x[1])[:5]:
            print(f"  - {issue} ({count}篇)")


if __name__ == "__main__":
    main()
