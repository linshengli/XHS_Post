#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多账号内容生成器 - Multi-Account Content Generator
功能:
1. 人设化 Prompt 构建
2. LLM 调用集成 (使用 Qwen3.5)
3. 约束检查 + 迭代优化

使用示例:
    generator = MultiAccountContentGenerator()
    content = generator.generate_content(topic, persona, angle)
"""

import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import subprocess


class MultiAccountContentGenerator:
    """
    多账号内容生成器
    
    核心功能:
    1. 根据人设构建个性化的 Prompt
    2. 调用 Qwen3.5 LLM 生成内容
    3. 使用约束引擎进行迭代优化
    """
    
    def __init__(self, config_dir: str = None):
        """
        初始化生成器
        
        Args:
            config_dir: 配置文件目录
        """
        if config_dir is None:
            self.config_dir = Path(__file__).parent.parent / "config"
        else:
            self.config_dir = Path(config_dir)
        
        # 导入约束引擎
        from engines.constraint_engine import PersonaConstraintEngine
        self.constraint_engine = PersonaConstraintEngine(config_dir=str(self.config_dir))
        
        # LLM 配置
        self.llm_config = {
            'provider': 'qwen',
            'model': 'qwen3.5-plus',
            'temperature': 0.7,
            'max_tokens': 2000,
        }
        
        # 标题公式模板
        self.title_templates = {
            'numeric': "{number}个{topic}技巧，{benefit}",
            'contrast': "别再{old_way}了，{new_way}才是王道",
            'pain_point': "{pain}？{solution}看这一篇就够了",
            'curiosity': "没想到{topic}还能这样，{surprise}",
            'value': "{topic}全攻略，建议收藏！",
            'question': "{topic}到底该怎么选？{answer}",
            'exclamation': "{topic}也太{emotion}了吧！",
        }
    
    def load_persona(self, persona_file: str) -> Dict:
        """加载人设配置文件"""
        file_path = self.config_dir / persona_file
        if not file_path.exists():
            raise FileNotFoundError(f"Persona file not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def build_persona_prompt(self, persona: Dict, topic: str, angle: str) -> str:
        """
        构建人设化的 Prompt
        
        Args:
            persona: 人设配置
            topic: 内容主题
            angle: 内容角度
            
        Returns:
            完整的 Prompt 字符串
        """
        persona_info = persona.get('persona', {})
        
        # 提取人设信息
        name = persona_info.get('name', '博主')
        nickname = persona_info.get('nickname', name)
        demographics = persona_info.get('demographics', {})
        tone = persona_info.get('tone', {})
        expressions = persona_info.get('expressions', {})
        content_domains = persona_info.get('content_domains', {})
        
        # 构建系统提示
        system_prompt = f"""你是一位小红书博主，人设如下：

【基本信息】
- 名字：{name}
- 昵称：{nickname}
- 年龄：{demographics.get('age_range', '')}
- 职业：{demographics.get('occupation', '')}
- 城市：{demographics.get('location', '')}
- 性格：{tone.get('style', '')}

【内容风格】
- 语调：{tone.get('formality', 'semi-formal')}
- 能量水平：{tone.get('energy_level', 'medium')}
- 表情符号密度：{tone.get('emoji_density', 0.3)}
- 常用表情：{', '.join(tone.get('preferred_emojis', [])[:5])}

【内容领域】
- 主要：{', '.join(content_domains.get('primary', []))}
- 次要：{', '.join(content_domains.get('secondary', []))}

【常用表达】
- 开场白：{expressions.get('greetings', ['大家好'])[0]}
- 结尾：{expressions.get('endings', ['谢谢观看'])[0]}
- 过渡：{expressions.get('transitions', ['接下来'])[0]}

【禁用词】
请避免使用：{', '.join(persona_info.get('forbidden_words', []))}"""

        # 构建用户提示
        user_prompt = f"""请为小红书平台创作一篇笔记，要求如下：

【主题】{topic}

【内容角度】{angle}

【输出格式】
1. 标题 (20 字以内，吸引眼球，使用 emoji)
2. 正文 (300-800 字，分段清晰，多用 emoji)
3. 标签 (5-10 个，用逗号分隔)

【具体要求】
- 符合{demographics.get('age_range', '')}{demographics.get('occupation', '')}的身份和口吻
- 使用{tone.get('style', '')}的语调
- 适当使用表情符号 (密度约{tone.get('emoji_density', 0.3)})
- 内容实用、有价值
- 结尾引导互动 (点赞、收藏、评论)

请开始创作："""

        return f"{system_prompt}\n\n{user_prompt}"
    
    def call_llm(self, prompt: str) -> str:
        """
        调用 LLM 生成内容
        
        使用 OpenClaw 环境的 Qwen3.5 模型
        
        Args:
            prompt: 完整的 Prompt
            
        Returns:
            LLM 生成的内容
        """
        # 方法 1: 使用 subprocess 调用 OpenClaw 的 CLI (如果可用)
        # 方法 2: 使用 API 直接调用
        # 这里使用模拟方式，实际需要集成 OpenClaw 的 LLM 调用
        
        try:
            # 尝试使用 OpenClaw 的消息工具调用 LLM
            # 这里简化处理，返回一个占位符
            # 实际应该调用 OpenClaw 的 LLM 接口
            
            # 模拟 LLM 调用 (实际使用时替换为真实调用)
            response = self._mock_llm_response(prompt)
            return response
            
        except Exception as e:
            print(f"⚠️  LLM 调用失败：{e}")
            return None
    
    def _mock_llm_response(self, prompt: str) -> str:
        """
        模拟 LLM 响应 (用于测试)
        
        实际使用时应该替换为真实的 LLM 调用
        """
        # 从 prompt 中提取主题和角度
        import re
        
        topic_match = re.search(r'【主题】(.+)', prompt)
        angle_match = re.search(r'【内容角度】(.+)', prompt)
        name_match = re.search(r'名字：(.+)', prompt)
        
        topic = topic_match.group(1).strip() if topic_match else "主题"
        angle = angle_match.group(1).strip() if angle_match else "分享"
        name = name_match.group(1).strip() if name_match else "博主"
        
        # 生成模拟内容
        mock_content = f"""{topic}｜{angle}✨

家人们好呀！今天想跟大家聊聊{topic}这个话题～

作为{name}，我在这方面真的踩过不少坑😭 
现在终于总结出了一套实用的方法！

📝 重点来啦：

1️⃣ 第一点很重要的内容
这里详细说明一下，给到大家实用的建议💡

2️⃣ 第二点关键技巧
这个是我亲测有效的，一定要试试！

3️⃣ 第三点注意事项
避坑指南，千万别踩雷⚠️

💬 碎碎念：
其实{topic}真的没有想象中那么难，
关键是找到对的方法，然后坚持下去～

大家有什么{topic}相关的问题，
欢迎在评论区问我哦！👇

觉得有用记得点赞 + 收藏⭐
不然划走就找不到啦～

#{topic.replace(' ', '')} #{angle.replace(' ', '')} #干货分享 #实用技巧 #经验分享 #小红书助手 #热门推荐"""

        return mock_content
    
    def parse_llm_response(self, response: str) -> Dict[str, str]:
        """
        解析 LLM 响应，提取标题、正文、标签
        
        Args:
            response: LLM 生成的原始内容
            
        Returns:
            解析后的内容字典
        """
        lines = response.strip().split('\n')
        
        title = ""
        content_lines = []
        tags = ""
        in_content = True
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 检测标签行
            if line.startswith('#') and len(line) > 1:
                if not tags:
                    tags = line
                else:
                    tags += " " + line
                in_content = False
                continue
            
            # 第一行通常是标题
            if not title and in_content:
                title = line
                in_content = False
                continue
            
            # 其他是正文
            if in_content:
                content_lines.append(line)
        
        content = '\n'.join(content_lines)
        
        return {
            'title': title,
            'content': content,
            'tags': tags,
            'raw': response,
        }
    
    def generate_content(
        self, 
        topic: str, 
        persona_file: str, 
        angle: str = "经验分享",
        max_iterations: int = 2
    ) -> Dict[str, Any]:
        """
        生成单个账号的内容
        
        Args:
            topic: 内容主题
            persona_file: 人设配置文件
            angle: 内容角度
            max_iterations: 最大迭代优化次数
            
        Returns:
            生成结果字典
        """
        # 加载人设
        persona = self.load_persona(persona_file)
        persona_info = persona.get('persona', {})
        persona_name = persona_info.get('name', '未知')
        
        print(f"🎨 为人设 [{persona_name}] 生成内容...")
        print(f"   主题：{topic}")
        print(f"   角度：{angle}")
        
        # 构建 Prompt
        prompt = self.build_persona_prompt(persona, topic, angle)
        
        # 调用 LLM
        llm_response = self.call_llm(prompt)
        
        if not llm_response:
            return {
                'success': False,
                'error': 'LLM 调用失败',
                'persona_name': persona_name,
            }
        
        # 解析响应
        parsed = self.parse_llm_response(llm_response)
        
        # 约束检查
        full_content = f"{parsed['title']}\n{parsed['content']}"
        constraint_result = self.constraint_engine.check_content(full_content, persona)
        
        result = {
            'success': True,
            'persona_name': persona_name,
            'persona_id': persona_info.get('id'),
            'topic': topic,
            'angle': angle,
            'title': parsed['title'],
            'content': parsed['content'],
            'tags': parsed['tags'],
            'constraint_check': constraint_result,
            'passed_constraints': constraint_result['passed'],
            'constraint_score': constraint_result['overall_score'],
            'iterations': 1,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        
        # 如果未通过约束检查，尝试迭代优化
        if not constraint_result['passed'] and max_iterations > 1:
            print(f"⚠️  内容未通过约束检查，尝试优化...")
            
            for i in range(1, max_iterations):
                # 构建优化 Prompt
                suggestions = constraint_result['suggestions']
                optimize_prompt = f"""请根据以下建议优化内容：

{chr(10).join(suggestions)}

原内容：
{full_content}

请在保持原意的基础上，按照建议优化内容，使其符合人设约束。"""
                
                # 调用 LLM 优化
                optimized_response = self.call_llm(optimize_prompt)
                
                if optimized_response:
                    parsed = self.parse_llm_response(optimized_response)
                    full_content = f"{parsed['title']}\n{parsed['content']}"
                    constraint_result = self.constraint_engine.check_content(full_content, persona)
                    
                    result['iterations'] = i + 1
                    result['title'] = parsed['title']
                    result['content'] = parsed['content']
                    result['tags'] = parsed['tags']
                    result['constraint_check'] = constraint_result
                    result['passed_constraints'] = constraint_result['passed']
                    result['constraint_score'] = constraint_result['overall_score']
                    
                    if constraint_result['passed']:
                        print(f"✅ 第{i+1}次迭代后通过约束检查")
                        break
        
        print(f"✅ 内容生成完成，约束评分：{result['constraint_score']:.2f}")
        return result
    
    def generate_multi_account_content(
        self, 
        topic: str, 
        persona_files: List[str],
        angles_per_account: Dict[str, str] = None
    ) -> List[Dict[str, Any]]:
        """
        为多个账号生成差异化内容
        
        Args:
            topic: 内容主题
            persona_files: 人设配置文件列表
            angles_per_account: 每个账号的内容角度 (可选)
            
        Returns:
            生成结果列表
        """
        results = []
        
        for pf in persona_files:
            try:
                # 加载人设获取角度
                persona = self.load_persona(pf)
                persona_info = persona.get('persona', {})
                persona_id = persona_info.get('id')
                
                # 获取该账号的内容角度
                angle = "经验分享"  # 默认
                if angles_per_account and persona_id in angles_per_account:
                    angle = angles_per_account[persona_id]
                else:
                    # 从人设配置中获取首选角度
                    content_angles = persona_info.get('content_angles', [])
                    if content_angles:
                        angle = content_angles[0]
                
                # 生成内容
                result = self.generate_content(topic, pf, angle)
                results.append(result)
                
            except Exception as e:
                print(f"❌ 生成 {pf} 内容失败：{e}")
                results.append({
                    'success': False,
                    'error': str(e),
                    'persona_file': pf,
                })
        
        return results
    
    def save_content(self, content_result: Dict, output_dir: str = None) -> str:
        """
        保存生成的内容到文件
        
        Args:
            content_result: 生成结果
            output_dir: 输出目录
            
        Returns:
            保存的文件路径
        """
        if output_dir is None:
            output_dir = Path(__file__).parent.parent / "output"
        else:
            output_dir = Path(output_dir)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        persona_id = content_result.get('persona_id', 'unknown')
        filename = f"{persona_id}_{timestamp}.md"
        filepath = output_dir / filename
        
        # 构建 Markdown 内容
        md_content = f"""# {content_result.get('title', 'Untitled')}

**人设**: {content_result.get('persona_name', '')}
**主题**: {content_result.get('topic', '')}
**角度**: {content_result.get('angle', '')}
**生成时间**: {content_result.get('timestamp', '')}

---

{content_result.get('content', '')}

---

**标签**: {content_result.get('tags', '')}

---

## 约束检查
- 通过：{'是' if content_result.get('passed_constraints', False) else '否'}
- 评分：{content_result.get('constraint_score', 0):.2f}
- 迭代次数：{content_result.get('iterations', 1)}
"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        return str(filepath)


# ==================== 命令行接口 ====================

def main():
    """测试生成器功能"""
    import argparse
    
    parser = argparse.ArgumentParser(description="多账号内容生成器测试")
    parser.add_argument("--topic", type=str, default="职场穿搭", help="内容主题")
    parser.add_argument("--persona", type=str, default="personas/account_001.yaml", help="人设文件")
    parser.add_argument("--config-dir", type=str, default=None, help="配置文件目录")
    args = parser.parse_args()
    
    print("=" * 60)
    print("🎨 多账号内容生成器测试")
    print("=" * 60)
    
    generator = MultiAccountContentGenerator(config_dir=args.config_dir)
    
    # 生成内容
    result = generator.generate_content(
        topic=args.topic,
        persona_file=args.persona,
        angle="经验分享"
    )
    
    if result['success']:
        print("\n✅ 生成成功!\n")
        print(f"标题：{result['title']}")
        print(f"\n内容预览:")
        print(result['content'][:300] + "...")
        print(f"\n标签：{result['tags']}")
        print(f"\n约束检查:")
        print(f"  通过：{'是' if result['passed_constraints'] else '否'}")
        print(f"  评分：{result['constraint_score']:.2f}")
        print(f"  迭代：{result['iterations']}次")
    else:
        print(f"\n❌ 生成失败：{result.get('error', '未知错误')}")
    
    print("\n" + "=" * 60)
    print("✅ 测试完成")
    print("=" * 60)


if __name__ == "__main__":
    exit(main())
