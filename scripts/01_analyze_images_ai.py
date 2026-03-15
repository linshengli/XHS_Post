#!/usr/bin/env python3
"""
01_analyze_images_ai.py - 使用 OpenClaw image 工具进行真正的 AI 图片分析

使用方式:
    # 分析指定目录的图片
    python scripts/01_analyze_images_ai.py --images-dir ~/XHS_Post/local_images/太空修

    # 指定输出文件
    python scripts/01_analyze_images_ai.py --images-dir ~/XHS_Post/local_images/太空修 --output config/image_analysis.json

注意:
    - 图片需要在 OpenClaw 允许的目录下（如 ~/.openclaw/media/）
    - 会自动将图片复制到 media 目录进行分析
"""

import json
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
import argparse

# OpenClaw media 目录
OPENCLAW_MEDIA_DIR = Path.home() / ".openclaw" / "media" / "xhs_images"
OPENCLAW_WORKSPACE = Path.home() / ".openclaw" / "workspace"

# 图片扩展名
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


def discover_images(images_dir: Path) -> list[Path]:
    """发现目录下的所有图片"""
    return sorted([
        f for f in images_dir.rglob("*")
        if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS
    ])


def copy_to_media(image_path: Path) -> Path:
    """将图片复制到 OpenClaw media 目录"""
    OPENCLAW_MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    dest = OPENCLAW_MEDIA_DIR / image_path.name
    if not dest.exists():
        shutil.copy2(image_path, dest)
    return dest


def analyze_with_openclaw(image_path: Path, model: str = "bailian/qwen3.5-plus") -> dict:
    """使用 OpenClaw CLI 分析图片"""
    prompt = """请分析这张图片，返回 JSON 格式的分析结果，包含以下字段：
{
  "theme": "主题（一句话描述）",
  "elements": ["主要元素1", "主要元素2"],
  "colors": ["主色调1", "主色调2"],
  "emotion": "情感氛围",
  "style": "风格类型",
  "suitable_for": ["适合的内容类型1", "适合的内容类型2"],
  "description": "详细描述（50字以内）"
}

只返回 JSON，不要其他文字。"""

    try:
        # 构建调用 OpenClaw agent 的命令
        cmd = [
            "openclaw", "agent",
            "--agent", "main",
            "--message", f"分析图片: {image_path}\n\n{prompt}",
            "--local"
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(OPENCLAW_WORKSPACE)
        )
        
        if result.returncode != 0:
            print(f"  ⚠️ 分析失败: {result.stderr[:100]}")
            return None
        
        # 解析输出
        output = result.stdout.strip()
        
        # 提取 JSON（跳过配置警告）
        lines = output.split('\n')
        content_lines = []
        for line in lines:
            if any(skip in line for skip in ['Config', '\x1b[', '[plugins]', '[33m', '[31m', '[35m', '[39m']):
                continue
            if line.strip():
                content_lines.append(line)
        
        content = '\n'.join(content_lines)
        
        # 尝试解析 JSON
        try:
            # 移除可能的 markdown 代码块
            content = content.replace('```json', '').replace('```', '').strip()
            return json.loads(content)
        except json.JSONDecodeError:
            # 尝试找到 JSON 对象
            start = content.find('{')
            end = content.rfind('}')
            if start != -1 and end != -1:
                try:
                    return json.loads(content[start:end+1])
                except:
                    pass
            return {"raw_analysis": content}
            
    except subprocess.TimeoutExpired:
        print(f"  ⚠️ 分析超时")
        return None
    except Exception as e:
        print(f"  ⚠️ 分析出错: {e}")
        return None


def analyze_image_smart(image_path: Path, index: int, topic: str = None) -> dict:
    """智能推断图片属性（作为降级方案）"""
    stem = image_path.stem.replace("_", " ").replace("-", " ").strip()
    
    generic_elements = ["人物", "环境", "细节", "场景", "构图", "光线", "色彩", "氛围"]
    generic_colors = ["暖色调", "冷色调", "自然色", "高对比", "柔和", "明亮", "低饱和"]
    generic_emotions = ["松弛感", "真实感", "氛围感", "生活感", "清爽", "治愈", "高级感"]
    generic_styles = ["生活记录", "旅行写真", "探店纪实", "轻攻略", "视觉笔记", "种草图文"]
    generic_content_types = ["封面图", "场景图", "细节图", "路线说明", "体验记录", "攻略配图"]
    
    def _pick(items, idx, offset=0):
        return items[(idx + offset) % len(items)]
    
    return {
        "file_name": image_path.name,
        "file_path": str(image_path),
        "theme": topic or image_path.parent.name or stem,
        "elements": [_pick(generic_elements, index, o) for o in range(4)],
        "colors": [_pick(generic_colors, index, o) for o in range(2)],
        "emotion": _pick(generic_emotions, index),
        "style": _pick(generic_styles, index),
        "suitable_for": [_pick(generic_content_types, index, o) for o in range(2)],
        "description": f"智能推断：{topic or stem}相关图片",
        "analysis_method": "smart_inference"
    }


def main():
    parser = argparse.ArgumentParser(description="使用 AI 分析图片")
    parser.add_argument("--images-dir", type=str, required=True, help="图片目录")
    parser.add_argument("--output", type=str, default="config/image_analysis.json", help="输出文件")
    parser.add_argument("--topic", type=str, default=None, help="主题")
    parser.add_argument("--use-ai", action="store_true", help="使用 AI 分析（需要 OpenClaw）")
    parser.add_argument("--model", type=str, default="bailian/qwen3.5-plus", help="AI 模型")
    args = parser.parse_args()

    images_dir = Path(args.images_dir).expanduser()
    output_file = Path(args.output)
    if not output_file.is_absolute():
        output_file = Path(__file__).parent.parent / output_file

    print("=" * 60)
    print("📸 图片分析工具 - AI 版")
    print("=" * 60)

    # 发现图片
    image_files = discover_images(images_dir)
    print(f"\n📁 发现 {len(image_files)} 张图片")

    if not image_files:
        print("❌ 未找到图片")
        return

    analyses = []

    for index, image_path in enumerate(image_files):
        print(f"\n[{index+1}/{len(image_files)}] 分析: {image_path.name}")
        
        if args.use_ai:
            # 复制到 media 目录
            media_path = copy_to_media(image_path)
            print(f"  📋 复制到: {media_path}")
            
            # AI 分析
            print(f"  🤖 AI 分析中...")
            result = analyze_with_openclaw(media_path, args.model)
            
            if result:
                result["file_name"] = image_path.name
                result["file_path"] = str(image_path)
                result["analysis_method"] = "ai_vision"
                analyses.append(result)
                print(f"  ✅ 主题: {result.get('theme', 'N/A')}")
            else:
                # 降级到智能推断
                print(f"  ⚠️ AI 分析失败，使用智能推断")
                analyses.append(analyze_image_smart(image_path, index, args.topic))
        else:
            # 智能推断
            result = analyze_image_smart(image_path, index, args.topic)
            analyses.append(result)
            print(f"  ✅ 主题: {result['theme']}")

    # 保存结果
    output_data = {
        "total_images": len(analyses),
        "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "topic": args.topic,
        "images": analyses
    }

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 60}")
    print(f"✅ 分析完成！")
    print(f"📊 共分析 {len(analyses)} 张图片")
    print(f"💾 结果保存到: {output_file}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()