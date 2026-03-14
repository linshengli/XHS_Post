#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from _project_paths import ensure_project_root_on_path

ensure_project_root_on_path()

from xhs_post.models import TopicWorkflowRequest
from xhs_post.workflows.topic_pipeline import run_topic_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="统一执行主题分析与内容生成 workflow")
    parser.add_argument("--topic", required=True, help="主题名称")
    parser.add_argument("--count", type=int, default=10, help="生成篇数")
    parser.add_argument("--analysis-output", type=str, default=None, help="分析快照输出路径")
    parser.add_argument("--generation-output", type=str, default=None, help="生成目录")
    parser.add_argument("--seed", type=int, default=None, help="随机种子")
    args = parser.parse_args()

    result = run_topic_pipeline(
        TopicWorkflowRequest(
            topic=args.topic,
            count=args.count,
            analysis_output=Path(args.analysis_output) if args.analysis_output else None,
            generation_output=Path(args.generation_output) if args.generation_output else None,
            seed=args.seed,
        )
    )

    print("✅ workflow 完成")
    print(f"主题: {result['topic']}")
    print(f"分析输出: {result['analysis_output']}")
    print(f"生成输出: {result['generation_output']}")


if __name__ == "__main__":
    main()
