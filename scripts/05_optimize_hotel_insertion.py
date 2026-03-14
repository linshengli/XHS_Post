#!/usr/bin/env python3
"""
05_optimize_hotel_insertion.py - 酒店植入优化脚本
检查并优化每篇内容的酒店植入，确保自然不生硬

输入：
  - generated_posts/YYYY-MM-DD/drafts/*.md
  - config/personas/*.yaml

输出：
  - generated_posts/YYYY-MM-DD/optimized/*.md

用法:
  python scripts/05_optimize_hotel_insertion.py \
    --input-dir generated_posts/2026-03-15/drafts \
    --output-dir generated_posts/2026-03-15/optimized \
    --personas-dir config/personas
"""

import os
import re
import json
import yaml
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# 配置路径
BASE_DIR = Path(os.path.expanduser("~/XHS_Post"))

# 植入模式库
INSERTION_MODES = {
    "route_anchor": {
        "name": "路线锚点型",
        "formula": "区域 + 住宿建议 + 理由",
        "example": "住在天屿山附近最方便，去各个景点都在 20 分钟内",
        "keywords": ["附近", "方便", "顺路", "车程", "分钟", "位置"],
        "suitable_for": ["攻略号", "本地号"]
    },
    "problem_solver": {
        "name": "问题解法型",
        "formula": "痛点 + 解决方案 + 结果",
        "example": "带娃最怕行程太赶，所以选了亲子酒店当大本营",
        "keywords": ["所以", "解决了", "终于", "轻松", "不累", "省心"],
        "suitable_for": ["亲子号"]
    },
    "experience_evidence": {
        "name": "体验证据型",
        "formula": "具体细节 + 感受 + 推荐",
        "example": "早餐有小朋友爱吃的 pancake，儿童乐园玩了 1 小时",
        "keywords": ["有", "可以", "还能", "特别", "喜欢", "玩了"],
        "suitable_for": ["本地号", "亲子号", "酒店号"]
    },
    "contrast_decision": {
        "name": "对比决策型",
        "formula": "选项对比 + 理由 + 验证",
        "example": "本来想订民宿，最后还是选了酒店，因为...",
        "keywords": ["本来", "最后", "因为", "确实", "对比", "还是"],
        "suitable_for": ["攻略号", "亲子号"]
    },
    "series_diary": {
        "name": "系列日记型",
        "formula": "时间线 + 活动 + 反馈",
        "example": "住店日记 Day3：今天的小客人 3 岁，在儿童乐园玩了 2 小时",
        "keywords": ["今天", "昨天", "客人", "说", "日记", "Day"],
        "suitable_for": ["酒店号"]
    }
}

# 广告话术黑名单（需要替换的）
AD_PHRASES_BLACKLIST = {
    "豪华装修": "装修很新",
    "五星级服务": "服务很贴心",
    "尊享体验": "体验很好",
    "欢迎入住": "推荐给大家",
    "预订从速": "建议提前订",
    "高端大气": "环境不错",
    "奢华": "舒适",
    "顶级": "不错",
    "最": "很",  # 避免绝对化用语
    "第一": "前列",
    "限时折扣": "现在有活动",
    "价格优惠": "性价比不错",
    "点击链接": "可以私信",
    "私信优惠": "私信有惊喜"
}


def load_persona(persona_file: Path) -> Optional[Dict]:
    """加载人设配置"""
    if not persona_file.exists():
        return None
    
    with open(persona_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    return config


def analyze_insertion_mode(content: str, preferred_modes: List[str]) -> str:
    """分析当前内容使用的植入模式"""
    for mode_name in preferred_modes:
        if mode_name not in INSERTION_MODES:
            continue
        
        mode = INSERTION_MODES[mode_name]
        # 检查是否包含该模式的关键词
        keyword_matches = sum(1 for kw in mode["keywords"] if kw in content)
        
        if keyword_matches >= 2:
            return mode_name
    
    # 如果没有匹配到，返回第一个首选模式
    return preferred_modes[0] if preferred_modes else "route_anchor"


def check_hotel_mentions(content: str) -> Dict:
    """检查酒店提及情况"""
    # 统计"酒店"一词出现次数
    hotel_mentions = len(re.findall(r'酒店|民宿|度假村|住宿', content))
    
    # 检查第一段是否出现酒店
    paragraphs = content.split('\n\n')
    first_para_has_hotel = bool(paragraphs) and bool(re.search(r'酒店|民宿|度假村', paragraphs[0]))
    
    # 提取提及酒店的具体句子
    hotel_sentences = []
    for sentence in re.split(r'[。！？!?]', content):
        if re.search(r'酒店|民宿|度假村', sentence):
            hotel_sentences.append(sentence.strip())
    
    return {
        "mention_count": hotel_mentions,
        "first_para_has_hotel": first_para_has_hotel,
        "hotel_sentences": hotel_sentences
    }


def replace_ad_phrases(content: str) -> tuple:
    """替换广告话术"""
    replaced_count = 0
    replaced_phrases = []
    
    optimized_content = content
    
    for ad_phrase, natural_phrase in AD_PHRASES_BLACKLIST.items():
        if ad_phrase in optimized_content:
            optimized_content = optimized_content.replace(ad_phrase, natural_phrase)
            replaced_count += 1
            replaced_phrases.append(ad_phrase)
    
    return optimized_content, replaced_count, replaced_phrases


def add_missing_details(content: str, required_details: List[str], persona_name: str) -> str:
    """检查并添加缺失的具体细节"""
    # 这里需要根据具体内容智能添加，暂时返回原内容
    # 实际实现时应该调用 LLM 生成缺失的细节
    return content


def optimize_content(content: str, persona_config: Dict) -> Dict:
    """优化单篇内容的酒店植入"""
    persona = persona_config.get('persona', {})
    hotel_insertion = persona.get('hotel_insertion', {})
    
    # 获取配置
    preferred_modes = hotel_insertion.get('preferred_modes', ['route_anchor'])
    mention_strength = hotel_insertion.get('mention_strength', 'soft')
    max_mentions = hotel_insertion.get('max_mentions_per_post', 3)
    avoid_first_para = hotel_insertion.get('avoid_first_paragraph', True)
    required_details = hotel_insertion.get('required_details', [])
    
    # 分析当前状态
    mention_analysis = check_hotel_mentions(content)
    current_mode = analyze_insertion_mode(content, preferred_modes)
    
    # 优化步骤
    issues = []
    optimizations = []
    
    # 1. 替换广告话术
    optimized_content, replaced_count, replaced_phrases = replace_ad_phrases(content)
    if replaced_count > 0:
        optimizations.append(f"替换{replaced_count}个广告话术：{', '.join(replaced_phrases)}")
        issues.append("包含广告话术")
    
    # 2. 检查提及次数
    if mention_analysis["mention_count"] > max_mentions:
        issues.append(f"酒店提及过频 ({mention_analysis['mention_count']}次，建议{max_mentions}次以内)")
        # 这里可以进一步优化，减少提及次数
    
    # 3. 检查第一段
    if avoid_first_para and mention_analysis["first_para_has_hotel"]:
        issues.append("第一段出现酒店名")
        # 可以优化：将第一段的酒店提及移到中后段
    
    # 4. 检查植入模式匹配
    if current_mode not in preferred_modes:
        issues.append(f"植入模式不匹配 (当前：{current_mode}, 推荐：{preferred_modes[0]})")
    
    # 5. 检查具体细节（简化版）
    detail_keywords = ["早餐", "儿童", "泳池", "乐园", "房间", "湖景", "活动", "服务"]
    has_details = any(kw in optimized_content for kw in detail_keywords)
    if not has_details:
        issues.append("缺少具体细节")
    
    return {
        "original_content": content,
        "optimized_content": optimized_content,
        "issues": issues,
        "optimizations": optimizations,
        "insertion_mode": current_mode,
        "mention_count": mention_analysis["mention_count"],
        "has_details": has_details
    }


def process_draft_file(input_file: Path, output_file: Path, persona_config: Dict) -> Dict:
    """处理单个草稿文件"""
    # 读取草稿
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 优化内容
    result = optimize_content(content, persona_config)
    
    # 保存优化后的内容
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(result["optimized_content"])
    
    # 记录处理结果
    result["input_file"] = str(input_file)
    result["output_file"] = str(output_file)
    
    return result


def find_matching_persona(file_name: str, personas: Dict[str, Dict]) -> Optional[Dict]:
    """根据文件名匹配人设"""
    # 尝试从文件名推断人设
    file_lower = file_name.lower()
    
    # 关键词匹配
    if '攻略' in file_lower or 'guide' in file_lower:
        return personas.get('account_001')
    elif '亲子' in file_lower or 'family' in file_lower or '遛娃' in file_lower:
        return personas.get('account_002')
    elif '本地' in file_lower or 'local' in file_lower:
        return personas.get('account_003')
    elif '酒店' in file_lower or 'hotel' in file_lower:
        return personas.get('account_004')
    
    # 默认返回第一个人设
    return list(personas.values())[0] if personas else None


def main():
    parser = argparse.ArgumentParser(description='酒店植入优化脚本')
    parser.add_argument('--input-dir', type=str, required=True, help='输入目录（草稿）')
    parser.add_argument('--output-dir', type=str, required=True, help='输出目录（优化后）')
    parser.add_argument('--personas-dir', type=str, default=str(BASE_DIR / 'config' / 'personas'), help='人设配置目录')
    
    args = parser.parse_args()
    
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    personas_dir = Path(args.personas_dir)
    
    print("=" * 60)
    print("🎯 酒店植入优化脚本")
    print("=" * 60)
    print(f"输入目录：{input_dir}")
    print(f"输出目录：{output_dir}")
    print(f"人设目录：{personas_dir}")
    print()
    
    # 加载所有人设配置
    personas = {}
    for persona_file in personas_dir.glob("*.yaml"):
        config = load_persona(persona_file)
        if config:
            persona_id = config['persona'].get('id', persona_file.stem)
            personas[persona_id] = config
    
    print(f"✅ 加载 {len(personas)} 个人设配置")
    
    # 处理所有草稿文件
    draft_files = list(input_dir.glob("*.md"))
    if not draft_files:
        print("❌ 未找到草稿文件！")
        return
    
    print(f"📝 开始处理 {len(draft_files)} 篇草稿...\n")
    
    results = []
    for i, draft_file in enumerate(draft_files, 1):
        print(f"[{i}/{len(draft_files)}] {draft_file.name}")
        
        # 匹配人设
        persona_config = find_matching_persona(draft_file.name, personas)
        if not persona_config:
            print(f"  ⚠️ 未找到匹配的人设，使用默认配置")
            continue
        
        persona_name = persona_config['persona'].get('name', '未知')
        print(f"  使用人设：{persona_name}")
        
        # 优化内容
        output_file = output_dir / draft_file.name
        result = process_draft_file(draft_file, output_file, persona_config)
        results.append(result)
        
        # 打印结果
        if result["issues"]:
            print(f"  ⚠️ 发现问题：{', '.join(result['issues'])}")
        if result["optimizations"]:
            print(f"  ✅ 已优化：{', '.join(result['optimizations'])}")
        print(f"  植入模式：{result['insertion_mode']}")
        print(f"  提及次数：{result['mention_count']}")
        print()
    
    # 生成处理报告
    report = {
        "processed_at": datetime.now().isoformat(),
        "total_files": len(results),
        "files_with_issues": sum(1 for r in results if r["issues"]),
        "files_optimized": sum(1 for r in results if r["optimizations"]),
        "results": results
    }
    
    report_file = output_dir / "optimization_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    # 打印总结
    print("=" * 60)
    print("📊 处理完成！")
    print("=" * 60)
    print(f"总文件数：{len(results)}")
    print(f"发现问题的文件：{report['files_with_issues']}")
    print(f"已优化的文件：{report['files_optimized']}")
    print(f"报告已保存到：{report_file}")


if __name__ == "__main__":
    main()
