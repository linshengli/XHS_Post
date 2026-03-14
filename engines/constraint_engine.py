#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
人设约束引擎 - Persona Constraint Engine
功能:
1. 禁用词检查
2. 语调一致性检查 (表情符号密度、句长)
3. 内容领域相关性检查
4. 评分系统

使用示例:
    engine = PersonaConstraintEngine()
    result = engine.check_content(content, persona)
    if result['passed']:
        print("内容符合人设约束")
"""

import re
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime


class PersonaConstraintEngine:
    """
    人设约束检查引擎
    
    检查维度:
    1. 禁用词检查 - 确保不包含人设禁止使用的词汇
    2. 语调一致性 - 检查表情符号密度、句子长度、正式程度
    3. 内容领域相关性 - 确保内容在人设的内容领域范围内
    4. 综合评分 - 给出整体符合度评分
    """
    
    def __init__(self, config_dir: str = None):
        """
        初始化约束引擎
        
        Args:
            config_dir: 配置文件目录
        """
        if config_dir is None:
            self.config_dir = Path(__file__).parent.parent / "config"
        else:
            self.config_dir = Path(config_dir)
        
        # 语调风格的正式程度映射
        self.formality_keywords = {
            'formal': ['您好', '敬请', '谨此', '感谢', '希望', '建议', '请'],
            'semi-formal': ['好呀', '分享', '推荐', '可以', '试试', '一起'],
            'casual': ['家人们', '兄弟们', '绝绝子', 'yyds', '种草', '拔草', '冲'],
        }
        
        # 句子长度标准 (字符数)
        self.sentence_length_standards = {
            'low': {'min': 15, 'max': 40, 'avg': 25},
            'medium': {'min': 10, 'max': 30, 'avg': 20},
            'high': {'min': 5, 'max': 20, 'avg': 12},
        }
    
    def load_persona(self, persona_file: str) -> Dict:
        """加载人设配置文件"""
        file_path = self.config_dir / persona_file
        if not file_path.exists():
            raise FileNotFoundError(f"Persona file not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def check_forbidden_words(self, content: str, persona: Dict) -> Dict[str, Any]:
        """
        检查禁用词
        
        Args:
            content: 待检查的内容
            persona: 人设配置
            
        Returns:
            检查结果字典
        """
        persona_info = persona.get('persona', {})
        forbidden_words = persona_info.get('forbidden_words', [])
        
        found_words = []
        for word in forbidden_words:
            if word.lower() in content.lower():
                found_words.append(word)
        
        return {
            'check_type': 'forbidden_words',
            'passed': len(found_words) == 0,
            'found_words': found_words,
            'forbidden_words': forbidden_words,
            'score': 1.0 if len(found_words) == 0 else max(0, 1.0 - len(found_words) * 0.2),
        }
    
    def check_emoji_density(self, content: str, persona: Dict) -> Dict[str, Any]:
        """
        检查表情符号密度
        
        Args:
            content: 待检查的内容
            persona: 人设配置
            
        Returns:
            检查结果字典
        """
        persona_info = persona.get('persona', {})
        tone = persona_info.get('tone', {})
        expected_density = tone.get('emoji_density', 0.3)
        preferred_emojis = set(tone.get('preferred_emojis', []))
        
        # 计算表情符号总数
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F700-\U0001F77F"  # alchemical symbols
            "\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
            "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
            "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
            "\U0001FA00-\U0001FA6F"  # Chess Symbols
            "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
            "\U00002702-\U000027B0"  # Dingbats
            "\U00002600-\U000026FF"  # Miscellaneous Symbols
            "]+",
            flags=re.UNICODE
        )
        
        emojis = emoji_pattern.findall(content)
        emoji_count = len(emojis)
        
        # 计算句子数量
        sentences = re.split(r'[.!?。！？\n]+', content)
        sentences = [s.strip() for s in sentences if s.strip()]
        sentence_count = max(len(sentences), 1)
        
        # 实际密度 (每个句子的平均表情数)
        actual_density = emoji_count / sentence_count
        
        # 计算偏离度
        deviation = abs(actual_density - expected_density)
        
        # 分数计算 (偏离度越小分数越高)
        score = max(0, 1.0 - deviation)
        
        # 检查是否使用了首选表情
        non_preferred = [e for e in emojis if e not in preferred_emojis] if preferred_emojis else []
        
        return {
            'check_type': 'emoji_density',
            'passed': deviation <= 0.3,  # 允许 0.3 的偏差
            'expected_density': expected_density,
            'actual_density': round(actual_density, 2),
            'deviation': round(deviation, 2),
            'emoji_count': emoji_count,
            'sentence_count': sentence_count,
            'preferred_emojis_used': len([e for e in emojis if e in preferred_emojis]),
            'non_preferred_emojis': list(set(non_preferred))[:5],  # 最多显示 5 个
            'score': round(score, 2),
        }
    
    def check_sentence_length(self, content: str, persona: Dict) -> Dict[str, Any]:
        """
        检查句子长度
        
        Args:
            content: 待检查的内容
            persona: 人设配置
            
        Returns:
            检查结果字典
        """
        persona_info = persona.get('persona', {})
        tone = persona_info.get('tone', {})
        energy_level = tone.get('energy_level', 'medium')
        
        # 获取标准
        standard = self.sentence_length_standards.get(
            energy_level, 
            self.sentence_length_standards['medium']
        )
        
        # 分割句子
        sentences = re.split(r'[.!?。！？\n]+', content)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return {
                'check_type': 'sentence_length',
                'passed': True,
                'score': 1.0,
                'message': '无法分析句子长度',
            }
        
        # 计算平均句长
        lengths = [len(s) for s in sentences]
        avg_length = sum(lengths) / len(lengths)
        min_length = min(lengths)
        max_length = max(lengths)
        
        # 检查是否在标准范围内
        in_range = standard['min'] <= avg_length <= standard['max']
        
        # 分数计算
        if in_range:
            score = 1.0
        else:
            # 计算偏离度
            if avg_length < standard['min']:
                deviation = standard['min'] - avg_length
            else:
                deviation = avg_length - standard['max']
            score = max(0, 1.0 - deviation / standard['avg'])
        
        return {
            'check_type': 'sentence_length',
            'passed': in_range,
            'expected_range': f"{standard['min']}-{standard['max']}字符",
            'actual_avg': round(avg_length, 1),
            'actual_min': min_length,
            'actual_max': max_length,
            'sentence_count': len(sentences),
            'score': round(score, 2),
        }
    
    def check_formality_level(self, content: str, persona: Dict) -> Dict[str, Any]:
        """
        检查语调正式程度
        
        Args:
            content: 待检查的内容
            persona: 人设配置
            
        Returns:
            检查结果字典
        """
        persona_info = persona.get('persona', {})
        tone = persona_info.get('tone', {})
        expected_formality = tone.get('formality', 'semi-formal')
        
        # 统计各类关键词出现次数
        formality_scores = {}
        for level, keywords in self.formality_keywords.items():
            count = sum(1 for kw in keywords if kw in content)
            formality_scores[level] = count
        
        # 找出最匹配的风格
        detected_formality = max(formality_scores, key=formality_scores.get)
        
        # 检查是否匹配
        passed = detected_formality == expected_formality
        
        # 计算分数
        total = sum(formality_scores.values())
        if total == 0:
            score = 0.5  # 中性
        else:
            expected_count = formality_scores.get(expected_formality, 0)
            score = expected_count / total
        
        return {
            'check_type': 'formality_level',
            'passed': passed,
            'expected_formality': expected_formality,
            'detected_formality': detected_formality,
            'formality_scores': formality_scores,
            'score': round(score, 2),
        }
    
    def check_content_domain_relevance(self, content: str, persona: Dict) -> Dict[str, Any]:
        """
        检查内容领域相关性
        
        Args:
            content: 待检查的内容
            persona: 人设配置
            
        Returns:
            检查结果字典
        """
        persona_info = persona.get('persona', {})
        content_domains = persona_info.get('content_domains', {})
        all_domains = (
            content_domains.get('primary', []) + 
            content_domains.get('secondary', [])
        )
        
        # 领域关键词映射 (复用 matcher 的逻辑)
        domain_keywords = {
            "职场": ["工作", "上班", "面试", "简历", "升职", "加薪"],
            "穿搭": ["衣服", "服装", "搭配", "时尚", "穿衣", "OOTD"],
            "美妆": ["化妆", "护肤", "口红", "粉底", "面膜"],
            "生活方式": ["生活", "日常", "Vlog", "记录", "分享"],
            "学习": ["学习", "考试", "考研", "证书", "课程", "笔记"],
            "数码": ["手机", "电脑", "平板", "耳机", "科技", "APP"],
            "校园": ["学校", "宿舍", "食堂", "同学", "老师"],
            "美食": ["美食", "餐厅", "吃饭", "探店", "打卡", "好吃"],
            "育儿": ["孩子", "宝宝", "婴儿", "儿童", "带娃", "辅食"],
            "亲子": ["亲子", "家庭", "父母", "陪伴", "游戏"],
            "家庭": ["家庭", "家务", "装修", "家居"],
            "母婴": ["母婴", "孕期", "产后", "母乳", "奶粉"],
            "旅游": ["旅游", "旅行", "景点", "攻略", "酒店"],
            "健身": ["健身", "运动", "减肥", "瑜伽", "跑步"],
        }
        
        # 统计匹配的领域
        matched_domains = []
        content_lower = content.lower()
        
        for domain in all_domains:
            domain_lower = domain.lower()
            # 直接匹配
            if domain_lower in content_lower:
                matched_domains.append(domain)
                continue
            
            # 关键词匹配
            if domain_lower in domain_keywords:
                keywords = domain_keywords[domain_lower]
                if any(kw in content_lower for kw in keywords):
                    matched_domains.append(domain)
        
        # 计算相关性分数
        score = len(matched_domains) / max(len(all_domains), 1)
        score = min(score * 2, 1.0)  # 匹配 50% 以上就给满分
        
        return {
            'check_type': 'content_domain_relevance',
            'passed': len(matched_domains) > 0,
            'matched_domains': matched_domains,
            'all_domains': all_domains,
            'relevance_score': round(score, 2),
            'score': round(score, 2),
        }
    
    def check_content(self, content: str, persona: Dict) -> Dict[str, Any]:
        """
        完整的内容检查
        
        Args:
            content: 待检查的内容
            persona: 人设配置
            
        Returns:
            完整检查结果
        """
        # 执行所有检查
        checks = {
            'forbidden_words': self.check_forbidden_words(content, persona),
            'emoji_density': self.check_emoji_density(content, persona),
            'sentence_length': self.check_sentence_length(content, persona),
            'formality_level': self.check_formality_level(content, persona),
            'content_domain': self.check_content_domain_relevance(content, persona),
        }
        
        # 计算综合分数
        total_score = sum(check['score'] for check in checks.values())
        avg_score = total_score / len(checks)
        
        # 判断是否通过 (所有关键检查都通过)
        critical_checks = ['forbidden_words', 'content_domain']
        all_passed = all(
            checks[check]['passed'] 
            for check in critical_checks
        )
        
        # 生成改进建议
        suggestions = self._generate_suggestions(checks)
        
        return {
            'passed': all_passed,
            'overall_score': round(avg_score, 2),
            'checks': checks,
            'suggestions': suggestions,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
    
    def _generate_suggestions(self, checks: Dict) -> List[str]:
        """
        根据检查结果生成改进建议
        
        Args:
            checks: 各项检查结果
            
        Returns:
            建议列表
        """
        suggestions = []
        
        # 禁用词
        if not checks['forbidden_words']['passed']:
            words = checks['forbidden_words']['found_words']
            suggestions.append(f"⚠️  移除禁用词：{', '.join(words)}")
        
        # 表情符号
        if not checks['emoji_density']['passed']:
            expected = checks['emoji_density']['expected_density']
            actual = checks['emoji_density']['actual_density']
            if actual > expected:
                suggestions.append(f"💡 减少表情符号使用 (当前：{actual}, 建议：{expected})")
            else:
                suggestions.append(f"💡 增加表情符号使用 (当前：{actual}, 建议：{expected})")
        
        # 句子长度
        if not checks['sentence_length']['passed']:
            expected = checks['sentence_length']['expected_range']
            actual = checks['sentence_length']['actual_avg']
            suggestions.append(f"💡 调整句子长度 (当前：{actual}字，建议：{expected})")
        
        # 语调正式度
        if not checks['formality_level']['passed']:
            expected = checks['formality_level']['expected_formality']
            detected = checks['formality_level']['detected_formality']
            suggestions.append(f"💡 调整语调风格 (当前：{detected}, 建议：{expected})")
        
        # 内容领域
        if not checks['content_domain']['passed']:
            suggestions.append("💡 增强内容与人设领域的相关性")
        
        return suggestions
    
    def optimize_content(self, content: str, persona: Dict, max_iterations: int = 3) -> Dict[str, Any]:
        """
        迭代优化内容 (模拟优化，实际优化需要 LLM)
        
        Args:
            content: 原始内容
            persona: 人设配置
            max_iterations: 最大迭代次数
            
        Returns:
            优化结果
        """
        current_content = content
        history = []
        
        for i in range(max_iterations):
            result = self.check_content(current_content, persona)
            
            history.append({
                'iteration': i + 1,
                'content_preview': current_content[:100] + '...',
                'score': result['overall_score'],
                'passed': result['passed'],
                'suggestions': result['suggestions'],
            })
            
            if result['passed']:
                break
            
            # 这里应该调用 LLM 进行优化
            # 简化处理：只返回检查结果
            current_content = f"[需要 LLM 优化的内容: {result['suggestions']}]"
        
        return {
            'original_content': content,
            'final_content': current_content,
            'iterations': len(history),
            'history': history,
            'final_passed': history[-1]['passed'] if history else False,
            'final_score': history[-1]['score'] if history else 0,
        }


# ==================== 命令行接口 ====================

def main():
    """测试约束引擎功能"""
    import json
    import argparse
    
    parser = argparse.ArgumentParser(description="人设约束引擎测试")
    parser.add_argument(
        "--persona", 
        type=str, 
        default="personas/account_001.yaml",
        help="人设配置文件"
    )
    parser.add_argument(
        "--config-dir", 
        type=str, 
        default=None, 
        help="配置文件目录"
    )
    args = parser.parse_args()
    
    print("=" * 60)
    print("🎭 人设约束引擎测试")
    print("=" * 60)
    
    engine = PersonaConstraintEngine(config_dir=args.config_dir)
    
    # 加载人设
    persona = engine.load_persona(args.persona)
    persona_name = persona.get('persona', {}).get('name', '未知')
    
    print(f"\n📌 测试人设：{persona_name}")
    
    # 测试内容
    test_content = """
    姐妹们好呀✨今天分享一个职场穿搭小 tips！
    作为外企市场经理，我每天都要见客户，穿搭真的太重要了💼
    这几件单品是我通勤必备，百搭又显气质👗
    1️⃣ 白色衬衫 - 简约大方
    2️⃣ 黑色西装裤 - 显瘦显高
    3️⃣ 高跟鞋 - 提升气场
    一起变优秀💪 有什么问题评论区见~
    """
    
    print("\n📝 测试内容预览:")
    print(test_content[:200] + "...")
    
    # 执行检查
    print("\n🔍 执行约束检查...\n")
    result = engine.check_content(test_content, persona)
    
    print(f"✅ 检查结果:")
    print(f"  通过：{'是' if result['passed'] else '否'}")
    print(f"  综合分数：{result['overall_score']:.2f}")
    
    print(f"\n📊 详细检查:")
    for check_name, check_data in result['checks'].items():
        status = "✅" if check_data['passed'] else "❌"
        print(f"  {status} {check_name}: {check_data['score']:.2f}")
    
    if result['suggestions']:
        print(f"\n💡 改进建议:")
        for suggestion in result['suggestions']:
            print(f"  {suggestion}")
    
    print("\n" + "=" * 60)
    print("✅ 测试完成")
    print("=" * 60)


if __name__ == "__main__":
    exit(main())
