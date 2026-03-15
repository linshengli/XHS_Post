#!/usr/bin/env python3
"""
下载小红书图片到本地 - 解决图片链接失效问题

用法:
    python scripts/download_images.py --input-dir generated_posts/2026-03-15
    python xhs.py download-images --topic "千岛湖好玩的地方" --count 30
"""

import argparse
import subprocess
import re
import sys
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
LOCAL_IMAGES_DIR = BASE_DIR / "local_images"

# 添加项目路径
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "scripts"))


def extract_image_urls_from_markdown(md_file: Path) -> list[str]:
    """从 Markdown 文件中提取图片 URL"""
    urls = []
    content = md_file.read_text(encoding='utf-8')
    
    # 匹配 Markdown 图片格式：![alt](url)
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


def download_images_from_crawled(topic: str, count: int = 10, output_dir: Path = None) -> list[Path]:
    """从爬取的原始数据中提取并下载图片"""
    from xhs_post.storage import load_jsonl_files
    from xhs_post.topic import filter_posts_by_source_keyword
    
    if output_dir is None:
        output_dir = LOCAL_IMAGES_DIR
    
    # 加载爬取的数据
    jsonl_dir = BASE_DIR / "xhs_post_from_search" / "jsonl"
    if not jsonl_dir.exists():
        print(f"❌ 爬取数据目录不存在：{jsonl_dir}")
        return []
    
    print(f"📂 加载爬取数据：{jsonl_dir}")
    posts = load_jsonl_files(jsonl_dir)
    
    # 筛选主题相关
    filtered = filter_posts_by_source_keyword(posts, topic)
    print(f"   找到 {len(filtered)} 篇相关笔记")
    
    if not filtered:
        print("⚠️  没有相关笔记")
        return []
    
    # 提取图片 URL
    downloaded = []
    for post in filtered[:count * 2]:  # 多遍历一些以确保下载足够数量
        image_data = post.get('image_list') or post.get('images_list') or post.get('images', [])
        if not image_data:
            continue
        
        # image_list 可能是字符串或列表
        if isinstance(image_data, str):
            image_urls = [image_data]
        elif isinstance(image_data, list):
            image_urls = image_data
        else:
            continue
        
        for img in image_urls[:3]:  # 每篇最多下载 3 张
            if len(downloaded) >= count:
                break
            
            # 图片 URL 可能是 dict 或 string
            if isinstance(img, dict):
                url = img.get('url') or img.get('url_default') or img.get('path')
            else:
                url = img
            
            if url and url.startswith("http"):
                path = download_image(url, output_dir, topic)
                if path:
                    downloaded.append(path)
        
        if len(downloaded) >= count:
            break
    
    return downloaded


def download_images_for_topic(topic: str, count: int = 10, output_dir: Path = None) -> list[Path]:
    """为指定主题下载图片"""
    # 尝试从爬取数据下载
    return download_images_from_crawled(topic, count, output_dir)


def main():
    parser = argparse.ArgumentParser(description="下载小红书图片到本地")
    parser.add_argument("--topic", "-t", type=str, help="主题名称")
    parser.add_argument("--input-dir", type=Path, help="Markdown 文件目录")
    parser.add_argument("--output-dir", "-o", type=Path, default=LOCAL_IMAGES_DIR, help="输出目录")
    parser.add_argument("--count", "-c", type=int, default=20, help="最多下载数量")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("📥 下载小红书图片")
    print("=" * 60)
    
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    
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
                path = download_image(url, output_dir, md_file.stem)
                if path:
                    downloaded.append(path)
    
    # 模式 2: 从热点分析下载
    if args.topic:
        print(f"\n🎯 主题：{args.topic}")
        topic_downloaded = download_images_for_topic(args.topic, args.count, output_dir)
        downloaded.extend(topic_downloaded)
    
    print("\n" + "=" * 60)
    print(f"✅ 完成！共下载 {len(downloaded)} 张图片")
    print(f"📂 位置：{output_dir}")
    
    if downloaded:
        print("\n💡 下一步:")
        topic_str = args.topic or 'xxx'
        print(f"   python scripts/01_analyze_images.py --images-dir {output_dir} --topic \"{topic_str}\"")


if __name__ == "__main__":
    main()
