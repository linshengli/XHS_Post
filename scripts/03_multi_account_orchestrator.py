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
from pathlib import Path

from _project_paths import ensure_project_root_on_path, resolve_base_dir

ensure_project_root_on_path()

from xhs_post.models import MultiAccountWorkflowRequest
from xhs_post.workflows.multi_account import run_multi_account_workflow

BASE_DIR = resolve_base_dir()

def main():
    parser = argparse.ArgumentParser(description='多账号人设编排脚本')
    parser.add_argument('--topic', type=str, required=True, help='主题')
    parser.add_argument('--input', type=str, default='config/trending_analysis.json',
                        help='热点分析结果路径')
    parser.add_argument('--output-dir', type=str, default='generated_posts',
                        help='输出目录')
    args = parser.parse_args()
    
    result = run_multi_account_workflow(
        MultiAccountWorkflowRequest(
            topic=args.topic,
            input_path=(BASE_DIR / args.input).resolve(),
            output_dir=(BASE_DIR / args.output_dir).resolve(),
            personas_dir=(BASE_DIR / "config" / "personas").resolve(),
        )
    )

    print("✅ 多账号编排完成!")
    print(f"主题: {result['topic']}")
    print(f"账号数: {len(result['accounts'])}")
    print(f"预览:\n{result['telegram_preview']}")

if __name__ == '__main__':
    main()
