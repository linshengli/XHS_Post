#!/usr/bin/env python3
"""
下载小红书图片到本地 - 解决图片链接失效问题

用法:
    python scripts/download_images.py --input-dir generated_posts/2026-03-15
    python scripts/download_images.py --topic "千岛湖好玩的地方"
"""

import argparse
import subprocess
import sys
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
IMAGES_DIR = BASE_DIR / "local_images"


def extract_image_urls_from_markdown(md_file: Path) -> list[str]:
    """从 Markdown 文件中提取图片 URL"""
    urls = []
    content = md_file.read_text(encoding='utf-8')
    
    # 匹配 Markdown 图片格式：![alt](url)
    import re
    pattern = r'!\[.*?\]\((https?://[^\s\)]+)\)'
    matches = re.findall(pattern, content)
    urls.extend(matches)
    
    return urls


def download_image(url: str, output_dir: Path, topic: str = None) -> Path | None:
    """下载单张图片"""
    try:
        # 创建 topic 子目录
        if topic:
            topic_dir = output_dir / topic.replace("/", "_").replace("\\", "_")
            topic_dir.mkdir(parents=True, exist_ok=True)
        else:
            topic_dir = output_dir
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"img_{timestamp}_{url.split('/')[-1][:30]}.jpg"
        output_path = topic_dir / filename
        
        # 使用 curl 下载
        result = subprocess.run(
            ["curl", "-L", "-o", str(output_path), url],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0 and output_path.exists():
            print(f"✅ 下载：{filename}")
            return output_path
        else:
            print(f"❌ 失败：{url}")
            if output_path.exists():
                output_path.unlink()
            return None
            
    except Exception as e:
        print(f"❌ 错误：{e}")
        return None


def download_images_for_topic(topic: str, count: int = 10) -> list[Path]:
    """为指定主题下载图片（从热点分析中获取）"""
    from xhs_post.storage import load_json
    
    # 加载热点分析
    analysis_file = BASE_DIR / "artifacts" / "trending" / "current.json"
    if not analysis_file.exists():
        print(f"❌ 热点分析文件不存在：{analysis_file}")
        return []
    
    data = load_json(analysis_file)
    images = data.get("images", [])
    
    if not images:
        print("⚠️  热点分析中没有图片数据")
        return []
    
    downloaded = []
    for img in images[:count]:
        url = img.get("url") or img.get("path")
        if url and url.startswith("http"):
            path = download_image(url, IMAGES_DIR, topic)
            if path:
                downloaded.append(path)
    
    return downloaded


def main():
    parser = argparse.ArgumentParser(description="下载小红书图片到本地")
    parser.add_argument("--topic", "-t", type=str, help="主题名称")
    parser.add_argument("--input-dir", type=Path, help="包含 Markdown 文件的目录")
    parser.add_argument("--output-dir", type=Path, default=IMAGES_DIR, help="输出目录")
    parser.add_argument("--count", "-c", type=int, default=20, help="最多下载图片数量")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("📥 下载小红书图片")
    print("=" * 60)
    
    IMAGES_DIR = args.output_dir
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    
    downloaded = []
    
    # 模式 1: 从 Markdown 文件下载
    if args.input_dir:
        print(f"📁 输入目录：{args.input_dir}")
        md_files = list(args.input_dir.glob("*.md"))
        
        for md_file in md_files:
            print(f"\n处理：{md_file.name}")
            urls = extract_image_urls_from_markdown(md_file)
            print(f"  找到 {len(urls)} 个图片链接")
            
            for url in urls[:args.count]:
                path = download_image(url, IMAGES_DIR, md_file.stem)
                if path:
                    downloaded.append(path)
    
    # 模式 2: 从热点分析下载
    if args.topic:
        print(f"\n🎯 主题：{args.topic}")
        topic_downloaded = download_images_for_topic(args.topic, args.count)
        downloaded.extend(topic_downloaded)
    
    print("\n" + "=" * 60)
    print(f"✅ 完成！共下载 {len(downloaded)} 张图片")
    print(f"📂 位置：{IMAGES_DIR}")
    
    if downloaded:
        print("\n💡 下一步:")
        print(f"   python scripts/01_analyze_images.py --images-dir {IMAGES_DIR} --topic \"{args.topic or 'xxx'}\"")


if __name__ == "__main__":
    main()
