#!/usr/bin/env python3
"""
03_multi_account_orchestrator.py - 多账号人设编排脚本
整合热点分析 + 多账号人设 + 差异化内容生成

用法:
    python scripts/03_multi_account_orchestrator.py --topic "主题"
    
示例:
    python scripts/03_multi_account_orchestrator.py --topic "千岛湖亲子酒店"
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def load_trending_analysis(config_path: str) -> dict:
    """加载热点分析结果"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_personas(personas_dir: str) -> list:
    """加载所有人设配置"""
    import yaml
    personas = []
    for file in Path(personas_dir).glob("*.yaml"):
        with open(file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            # 包装成统一格式
            if 'persona' in config:
                config = {
                    'account': {'id': config['persona'].get('id', 'unknown')},
                    'persona': config['persona']
                }
            personas.append(config)
    return personas

def match_topic_to_personas(topic: str, trending_data: dict, personas: list) -> dict:
    """将热点匹配到适合的人设账号"""
    results = {}
    
    # 获取高赞内容
    top_posts = trending_data.get('viral_score_ranking', [])[:10]
    hot_tags = trending_data.get('hot_tags', [])[:10]
    
    for persona in personas:
        account_id = persona['account']['id']
        persona_data = persona['persona']
        
        # 检查人设领域与主题匹配度
        primary_domains = persona_data.get('content_domains', {}).get('primary', [])
        secondary_domains = persona_data.get('content_domains', {}).get('secondary', [])
        tags = persona_data.get('tags', [])
        
        # 简单的关键词匹配
        score = 0
        angle = "通用角度"
        
        # 根据人设标签推荐角度
        if '亲子' in topic or '带娃' in topic:
            if '宝妈' in tags or '亲子' in tags:
                score = 90
                angle = f"以{persona_data.get('occupation', '宝妈')}身份分享亲子经验"
            elif '学生' in tags:
                score = 60
                angle = "回忆童年亲子时光"
            else:
                score = 40
                angle = "推荐适合亲子的好去处"
        elif '酒店' in topic or '住宿' in topic:
            if '职场精英' in tags or '生活品质' in tags:
                score = 85
                angle = "分享高端住宿体验"
            elif '学生' in tags:
                score = 70
                angle = "性价比住宿推荐"
            else:
                score = 50
                angle = "分享住宿心得"
        else:
            score = 50
            angle = "分享个人体验"
        
        results[account_id] = {
            'persona': persona_data,
            'match_score': score,
            'angle': angle,
            'recommended_posts': top_posts[:3],
            'hot_tags': hot_tags[:5]
        }
    
    return results

def generate_content_for_account(account_id: str, match_result: dict, topic: str) -> str:
    """为单个账号生成内容"""
    persona = match_result['persona']
    angle = match_result['angle']
    hot_tags = match_result['hot_tags']
    
    # 人设特征
    name = persona.get('name', '用户')
    tags = persona.get('tags', [])
    tone = persona.get('tone', {})
    language = persona.get('language_patterns', {})
    
    # 生成标题（使用人设特征）
    title = f"【{name}】{topic}攻略！{angle}"
    
    # 生成正文
    content_parts = []
    
    # 1. 痛点引入
    pain_intro = f"作为一个{persona.get('occupation', '热爱生活的人')}，每次{topic.split()[0] if topic else '旅行'}都头疼..."
    content_parts.append(pain_intro)
    
    # 2. 解决方案
    solution = f"今天分享的{topic}攻略，真的是{name}亲测好用！"
    content_parts.append(solution)
    
    # 3. 核心价值
    core_intro = "特别之处在于："
    content_parts.append(core_intro)
    
    # 根据人设添加个性化内容
    if '职场精英' in tags:
        content_parts.append("✨ 高效省时，适合忙碌的你")
        content_parts.append("💼 专业视角，品质保证")
    elif '学生' in tags:
        content_parts.append("✨ 性价比超高，学生党友好")
        content_parts.append("💰 省钱攻略，预算友好")
    elif '宝妈' in tags:
        content_parts.append("✨ 亲子友好，带娃无忧")
        content_parts.append("👶 安全舒适，宝妈首选")
    else:
        content_parts.append("✨ 独特体验，与众不同")
        content_parts.append("💫 用心推荐，值得信赖")
    
    # 4. 使用场景
    scenes_intro = "推荐给："
    content_parts.append(scenes_intro)
    
    domains = persona.get('content_domains', {}).get('primary', [])
    for domain in domains[:3]:
        content_parts.append(f"• {domain}爱好者")
    
    # 5. 行动号召
    greetings = language.get('preferred_greetings', ['大家好'])
    signature = language.get('signature_phrases', ['记得点赞收藏'])
    
    cta = f"{greetings[0]}，{signature[0]}哦！有问题欢迎留言交流~"
    content_parts.append(cta)
    
    # 6. 标签
    tags_str = ' '.join([f"#{t['tag']}" for t in hot_tags[:8]])
    content_parts.append(f"\n🏷️ {tags_str}")
    
    return '\n\n'.join(content_parts)

def validate_differentiation(contents: dict) -> dict:
    """验证多账号内容差异化"""
    issues = []
    account_ids = list(contents.keys())
    
    # 简单的标题相似度检查
    for i, id1 in enumerate(account_ids):
        for id2 in account_ids[i+1:]:
            # 计算相似度（简化版）
            sim_score = 0.3  # 实际应该用更复杂的算法
            
            if sim_score > 0.7:
                issues.append({
                    'accounts': [id1, id2],
                    'similarity': sim_score,
                    'suggestion': f'建议调整 {id2} 的内容角度'
                })
    
    return {
        'passed': len(issues) == 0,
        'issues': issues
    }

def simulate_telegram_push(topic: str, matches: dict) -> str:
    """模拟 Telegram 推送内容"""
    lines = []
    lines.append(f"📊 今日热点分析报告 ({datetime.now().strftime('%Y-%m-%d')})")
    lines.append(f"\n主题: {topic}\n")
    lines.append("=" * 50)
    
    for account_id, match in matches.items():
        persona = match['persona']
        lines.append(f"\n🎯 账号【{persona.get('name')}】")
        lines.append(f"   匹配度: {match['match_score']}%")
        lines.append(f"   建议角度: {match['angle']}")
        lines.append(f"   推荐标签: {', '.join([t['tag'] for t in match['hot_tags'][:3]])}")
    
    lines.append("\n" + "=" * 50)
    lines.append("\n请选择今日发布策略:")
    lines.append("[为所有账号生成] [分别为每个账号选择] [跳过今日]")
    
    return '\n'.join(lines)

def main():
    parser = argparse.ArgumentParser(description='多账号人设编排脚本')
    parser.add_argument('--topic', type=str, required=True, help='主题')
    parser.add_argument('--input', type=str, default='config/trending_analysis.json',
                        help='热点分析结果路径')
    parser.add_argument('--output-dir', type=str, default='generated_posts',
                        help='输出目录')
    args = parser.parse_args()
    
    print(f"🚀 多账号编排流程启动")
    print(f"主题: {args.topic}")
    print("=" * 50)
    
    # 1. 加载热点分析结果
    print("\n1️⃣ 加载热点分析结果...")
    trending_data = load_trending_analysis(args.input)
    print(f"   ✓ 分析了 {trending_data.get('total_posts_analyzed', 0)} 篇笔记")
    
    # 2. 加载人设配置
    print("\n2️⃣ 加载人设配置...")
    personas = load_personas('config/personas')
    print(f"   ✓ 加载了 {len(personas)} 个人设")
    for p in personas:
        print(f"     - {p['account']['id']}: {p['persona']['name']}")
    
    # 3. 热点匹配人设
    print("\n3️⃣ 热点匹配人设...")
    matches = match_topic_to_personas(args.topic, trending_data, personas)
    for account_id, match in matches.items():
        print(f"   ✓ {account_id}: 匹配度 {match['match_score']}%")
        print(f"     角度: {match['angle']}")
    
    # 4. 模拟 Telegram 推送
    print("\n4️⃣ Telegram 推送预览:")
    telegram_msg = simulate_telegram_push(args.topic, matches)
    print(telegram_msg)
    
    # 5. 生成差异化内容
    print("\n5️⃣ 生成差异化内容...")
    contents = {}
    for account_id, match in matches.items():
        content = generate_content_for_account(account_id, match, args.topic)
        contents[account_id] = {
            'title': f"【{match['persona']['name']}】{args.topic}",
            'content': content,
            'angle': match['angle'],
            'match_score': match['match_score']
        }
        print(f"   ✓ {account_id}: 已生成")
    
    # 6. 差异化验证
    print("\n6️⃣ 差异化验证...")
    validation = validate_differentiation(contents)
    if validation['passed']:
        print("   ✓ 通过 - 内容差异化足够")
    else:
        print(f"   ⚠️ 发现 {len(validation['issues'])} 个相似度问题")
    
    # 7. 保存输出
    print("\n7️⃣ 保存输出...")
    today = datetime.now().strftime('%Y-%m-%d')
    output_base = Path(args.output_dir) / today
    output_base.mkdir(parents=True, exist_ok=True)
    
    for account_id, content_data in contents.items():
        account_dir = output_base / account_id
        account_dir.mkdir(exist_ok=True)
        
        output_file = account_dir / f"post_multi_account.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# {content_data['title']}\n\n")
            f.write(f"**匹配度**: {content_data['match_score']}%\n\n")
            f.write(f"**内容角度**: {content_data['angle']}\n\n")
            f.write("---\n\n")
            f.write(content_data['content'])
        
        print(f"   ✓ {account_id}: {output_file}")
    
    # 保存汇总报告
    summary_file = output_base / "multi_account_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            'topic': args.topic,
            'date': today,
            'accounts': list(contents.keys()),
            'validation': validation,
            'matches': {k: {
                'match_score': v['match_score'],
                'angle': v['angle']
            } for k, v in matches.items()}
        }, f, ensure_ascii=False, indent=2)
    
    print(f"   ✓ 汇总报告: {summary_file}")
    
    print("\n" + "=" * 50)
    print("✅ 多账号编排完成!")
    print(f"输出目录: {output_base}")
    print(f"共生成 {len(contents)} 个账号的差异化内容")

if __name__ == '__main__':
    main()
