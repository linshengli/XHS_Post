#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
热点匹配引擎 - Hot Topic Matcher
功能：
1. 热点与人设领域匹配算法
2. 内容角度建议生成
3. 匹配度评分系统

使用示例:
    matcher = HotTopicPersonaMatcher()
    matches = matcher.match热点_to_personas(trending_data, personas)
"""

import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime


class HotTopicPersonaMatcher:
    """
    热点与人设匹配引擎
    
    核心算法：
    1. 提取热点的关键词和主题
    2. 与人设的内容领域进行语义匹配
    3. 计算匹配度分数
    4. 生成内容角度建议
    """
    
    def __init__(self, config_dir: str = None):
        """
        初始化匹配器
        
        Args:
            config_dir: 配置文件目录，默认为 config/
        """
        if config_dir is None:
            # 默认使用脚本所在目录的 config 文件夹
            self.config_dir = Path(__file__).parent.parent / "config"
        else:
            self.config_dir = Path(config_dir)
        
        # 领域关键词映射 (用于语义匹配)
        self.domain_keywords = {
            "职场": ["工作", "上班", "面试", "简历", "升职", "加薪", "同事", "老板", "会议", "项目", "KPI", "OKR"],
            "穿搭": ["衣服", "服装", "搭配", "时尚", "穿衣", "OOTD", "通勤", "裙子", "外套", "鞋子"],
            "美妆": ["化妆", "护肤", "口红", "粉底", "面膜", "美容", "彩妆", " skincare"],
            "生活方式": ["生活", "日常", "Vlog", "记录", "分享", "好物", "提升"],
            "学习": ["学习", "考试", "考研", "证书", "课程", "笔记", "复习", "成绩", "GPA"],
            "数码": ["手机", "电脑", "平板", "耳机", "相机", "科技", "数码", "APP", "软件"],
            "校园": ["学校", "宿舍", "食堂", "同学", "老师", "社团", "活动", "校园"],
            "美食": ["美食", "餐厅", "吃饭", "探店", "打卡", "味道", "好吃", "食谱", "做饭"],
            "育儿": ["孩子", "宝宝", "婴儿", "儿童", "带娃", "喂奶", "辅食", "早教", "幼儿园"],
            "亲子": ["亲子", "家庭", "父母", "陪伴", "游戏", "活动", "教育"],
            "家庭": ["家庭", "家务", "装修", "家居", "生活", "日常"],
            "母婴": ["母婴", "孕期", "产后", "母乳", "奶粉", "尿不湿", "婴儿车"],
            "旅游": ["旅游", "旅行", "景点", "攻略", "酒店", "机票", "打卡"],
            "健身": ["健身", "运动", "减肥", "瘦身", "瑜伽", "跑步", "锻炼"],
            "本地": ["本地", "城市", "周边", "附近", "哪里", "推荐"],
        }
        
        # 内容角度模板
        self.content_angle_templates = {
            "经验分享": "分享{topic}的实用经验和技巧",
            "好物推荐": "推荐适合{persona}的{topic}相关产品",
            "避坑指南": "揭秘{topic}中容易踩的坑和注意事项",
            "对比测评": "对比多款{topic}产品/服务的优劣",
            "日常 Vlog": "记录{persona}与{topic}相关的日常生活",
            "教程类": "手把手教{topic}的具体操作方法",
            "省钱攻略": "{topic}相关的省钱技巧和性价比选择",
            "真实测评": "以{persona}身份真实体验{topic}",
        }
    
    def load_persona(self, persona_file: str) -> Dict:
        """
        加载人设配置文件
        
        Args:
            persona_file: 人设配置文件路径 (相对于 config_dir)
            
        Returns:
            人设配置字典
        """
        file_path = self.config_dir / persona_file
        if not file_path.exists():
            raise FileNotFoundError(f"Persona file not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def extract_topic_keywords(self, topic: str) -> List[str]:
        """
        从热点主题中提取关键词
        
        Args:
            topic: 热点主题字符串
            
        Returns:
            关键词列表
        """
        # 简单实现：按空格和常见分隔符分词
        import re
        words = re.split(r'[,\s，]+', topic)
        return [w.strip() for w in words if w.strip()]
    
    def calculate_domain_match(self, topic: str, domains: List[str]) -> float:
        """
        计算热点主题与人设内容领域的匹配度
        
        Args:
            topic: 热点主题
            domains: 人设的内容领域列表
            
        Returns:
            匹配度分数 (0-1)
        """
        topic_keywords = set(self.extract_topic_keywords(topic.lower()))
        
        max_score = 0.0
        
        for domain in domains:
            domain_lower = domain.lower()
            # 直接匹配领域名称
            if domain_lower in topic.lower():
                max_score = max(max_score, 1.0)
                continue
            
            # 匹配领域关键词
            if domain_lower in self.domain_keywords:
                domain_kws = set(self.domain_keywords[domain_lower])
                matching_kws = topic_keywords.intersection(domain_kws)
                score = len(matching_kws) / max(len(domain_kws), 1)
                max_score = max(max_score, score)
        
        return min(max_score, 1.0)
    
    def calculate_persona_match(self, topic: str, persona: Dict) -> Dict[str, Any]:
        """
        计算热点与单个 personas 的匹配度
        
        Args:
            topic: 热点主题
            persona: 人设配置字典
            
        Returns:
            匹配结果字典，包含分数和建议
        """
        persona_info = persona.get('persona', {})
        
        # 获取人设的内容领域
        content_domains = persona_info.get('content_domains', {})
        primary_domains = content_domains.get('primary', [])
        secondary_domains = content_domains.get('secondary', [])
        
        # 计算主领域匹配度
        primary_score = self.calculate_domain_match(topic, primary_domains)
        secondary_score = self.calculate_domain_match(topic, secondary_domains) * 0.7
        
        # 综合分数 (主领域权重 0.7, 副领域 0.3)
        overall_score = primary_score * 0.7 + secondary_score * 0.3
        
        # 获取人设标签
        persona_tags = set(persona_info.get('tags', []))
        topic_keywords = set(self.extract_topic_keywords(topic))
        
        # 计算标签匹配度
        tag_matches = persona_tags.intersection(topic_keywords)
        tag_score = len(tag_matches) / max(len(persona_tags), 1)
        
        # 最终分数 (领域匹配 0.6 + 标签匹配 0.4)
        final_score = overall_score * 0.6 + tag_score * 0.4
        
        # 生成内容角度建议
        suggested_angles = self._suggest_content_angles(
            topic, 
            persona_info, 
            primary_domains if primary_score > secondary_score else secondary_domains
        )
        
        return {
            'persona_id': persona_info.get('id'),
            'persona_name': persona_info.get('name'),
            'topic': topic,
            'overall_score': round(final_score, 3),
            'domain_score': round(overall_score, 3),
            'tag_score': round(tag_score, 3),
            'matched_domains': self._get_matched_domains(topic, primary_domains + secondary_domains),
            'matched_tags': list(tag_matches),
            'suggested_angles': suggested_angles,
            'recommendation_level': self._get_recommendation_level(final_score),
        }
    
    def _get_matched_domains(self, topic: str, domains: List[str]) -> List[str]:
        """获取匹配的领域列表"""
        matched = []
        topic_lower = topic.lower()
        
        for domain in domains:
            domain_lower = domain.lower()
            if domain_lower in topic_lower:
                matched.append(domain)
                continue
            
            if domain_lower in self.domain_keywords:
                topic_kws = set(self.extract_topic_keywords(topic_lower))
                domain_kws = set(self.domain_keywords[domain_lower])
                if topic_kws.intersection(domain_kws):
                    matched.append(domain)
        
        return matched
    
    def _suggest_content_angles(self, topic: str, persona: Dict, matched_domains: List[str]) -> List[Dict]:
        """
        生成内容角度建议
        
        Returns:
            角度建议列表，每个包含角度名称、描述、优先级
        """
        persona_name = persona.get('name', '博主')
        content_angles = persona.get('content_angles', [])
        
        suggestions = []
        for angle in content_angles[:5]:  # 最多 5 个建议
            if angle in self.content_angle_templates:
                description = self.content_angle_templates[angle].format(
                    topic=topic,
                    persona=persona_name
                )
            else:
                description = f"从{angle}角度创作{topic}相关内容"
            
            # 根据角度类型分配优先级
            priority_map = {
                "经验分享": 1,
                "好物推荐": 2,
                "避坑指南": 1,
                "对比测评": 3,
                "日常 Vlog": 4,
                "教程类": 2,
                "省钱攻略": 2,
                "真实测评": 3,
            }
            
            suggestions.append({
                'angle': angle,
                'description': description,
                'priority': priority_map.get(angle, 5),
            })
        
        # 按优先级排序
        suggestions.sort(key=lambda x: x['priority'])
        return suggestions
    
    def _get_recommendation_level(self, score: float) -> str:
        """
        根据分数获取推荐等级
        
        Returns:
            推荐等级：highly_recommended, recommended, optional, not_recommended
        """
        if score >= 0.7:
            return "highly_recommended"
        elif score >= 0.5:
            return "recommended"
        elif score >= 0.3:
            return "optional"
        else:
            return "not_recommended"
    
    def match_topic_to_personas(self, topic: str, persona_files: List[str]) -> List[Dict]:
        """
        将一个热点主题与多个人设进行匹配
        
        Args:
            topic: 热点主题
            persona_files: 人设配置文件列表
            
        Returns:
            匹配结果列表，按分数降序排列
        """
        results = []
        
        for pf in persona_files:
            try:
                persona = self.load_persona(pf)
                match_result = self.calculate_persona_match(topic, persona)
                results.append(match_result)
            except Exception as e:
                print(f"⚠️  加载人设 {pf} 失败：{e}")
                continue
        
        # 按分数降序排列
        results.sort(key=lambda x: x['overall_score'], reverse=True)
        return results
    
    def match_trending_analysis(self, trending_data: Dict, persona_files: List[str]) -> Dict:
        """
        对完整的热点分析结果进行匹配
        
        Args:
            trending_data: 热点分析结果 (来自 02_analyze_trending.py 的输出)
            persona_files: 人设配置文件列表
            
        Returns:
            匹配结果字典，包含每个热点的匹配建议
        """
        # 从 trending_data 中提取主题
        topic = trending_data.get('topic', '')
        
        # 如果没有明确主题，使用热门标签
        if not topic:
            hot_tags = trending_data.get('hot_tags', [])
            if hot_tags:
                topic = hot_tags[0].get('tag', '')
        
        if not topic:
            return {
                'error': '无法从热点数据中提取主题',
                'matches': []
            }
        
        # 执行匹配
        matches = self.match_topic_to_personas(topic, persona_files)
        
        # 按账号分组推荐
        recommendations = {
            'topic': topic,
            'analysis_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'highly_recommended': [m for m in matches if m['recommendation_level'] == 'highly_recommended'],
            'recommended': [m for m in matches if m['recommendation_level'] == 'recommended'],
            'optional': [m for m in matches if m['recommendation_level'] == 'optional'],
            'all_matches': matches,
        }
        
        return recommendations


# ==================== 命令行接口 ====================

def main():
    """测试匹配器功能"""
    import json
    import argparse
    
    parser = argparse.ArgumentParser(description="热点匹配引擎测试")
    parser.add_argument("--topic", type=str, default="职场穿搭", help="测试主题")
    parser.add_argument("--config-dir", type=str, default=None, help="配置文件目录")
    args = parser.parse_args()
    
    print("=" * 60)
    print("🔥 热点匹配引擎测试")
    print("=" * 60)
    
    matcher = HotTopicPersonaMatcher(config_dir=args.config_dir)
    
    # 测试人设文件
    persona_files = [
        "personas/account_001.yaml",
        "personas/account_002.yaml",
        "personas/account_003.yaml",
    ]
    
    print(f"\n📌 测试主题：{args.topic}")
    print("\n🎯 匹配结果:\n")
    
    matches = matcher.match_topic_to_personas(args.topic, persona_files)
    
    for match in matches:
        print(f"账号：{match['persona_name']}")
        print(f"  匹配度：{match['overall_score']:.1%}")
        print(f"  推荐等级：{match['recommendation_level']}")
        print(f"  匹配领域：{', '.join(match['matched_domains']) or '无'}")
        print(f"  匹配标签：{', '.join(match['matched_tags']) or '无'}")
        if match['suggested_angles']:
            print(f"  建议角度：{match['suggested_angles'][0]['angle']}")
        print()
    
    print("=" * 60)
    print("✅ 测试完成")
    print("=" * 60)


if __name__ == "__main__":
    exit(main())
