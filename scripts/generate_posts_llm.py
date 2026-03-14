#!/usr/bin/env python3
"""小红书笔记自动生成脚本 - LLM 原创版."""

import argparse
from datetime import datetime
from pathlib import Path

from _project_paths import ensure_project_root_on_path, resolve_base_dir

ensure_project_root_on_path()

from xhs_post.models import LLMPostWorkflowRequest
from xhs_post.workflows.llm_post_generation import run_llm_post_generation_workflow

BASE_DIR = resolve_base_dir()
CONFIG_FILE = BASE_DIR / "config" / "trending_analysis.json"
RAW_POSTS_DIR = BASE_DIR / "xhs_post_from_search" / "jsonl"
OUTPUT_DIR = BASE_DIR / "generated_posts" / datetime.now().strftime("%Y-%m-%d")

def main():
    parser = argparse.ArgumentParser(description="小红书笔记自动生成 - LLM 原创版")
    parser.add_argument("--topic", type=str, required=True, help="生成笔记的主题")
    parser.add_argument("--count", type=int, default=8, help="生成笔记数量（默认：8）")
    parser.add_argument("--input", type=str, default=str(CONFIG_FILE), help="热点分析结果")
    parser.add_argument("--output-dir", type=str, default=str(OUTPUT_DIR), help="输出目录")
    parser.add_argument("--provider", type=str, default=None, help="LLM provider: openai/anthropic/qwen/mock")
    parser.add_argument("--seed", type=int, default=None, help="随机种子")
    args = parser.parse_args()

    print("=" * 60)
    print("📝 小红书笔记自动生成 - LLM 原创版")
    print("=" * 60)
    print(f"\n🎯 生成主题：{args.topic}")
    print(f"📊 生成数量：{args.count} 篇\n")
    output_files = run_llm_post_generation_workflow(
        LLMPostWorkflowRequest(
            topic=args.topic,
            count=args.count,
            trending_input=Path(args.input),
            output_dir=Path(args.output_dir),
            raw_posts_dir=RAW_POSTS_DIR,
            provider=args.provider,
            seed=args.seed,
        )
    )
    print(f"✅ 完成！共生成 {len(output_files)} 篇原创笔记")
    print(f"📂 保存位置：{args.output_dir}")

if __name__ == "__main__":
    main()
