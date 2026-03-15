#!/usr/bin/env python3
"""05_optimize_hotel_insertion.py - 酒店植入优化脚本."""

import argparse
from pathlib import Path
from _project_paths import ensure_project_root_on_path, resolve_base_dir

ensure_project_root_on_path()

from xhs_post.models import HotelOptimizationWorkflowRequest
from xhs_post.paths import ensure_runtime_layout, resolve_validation_report_dir
from xhs_post.workflows.hotel_optimization import run_hotel_optimization_workflow

BASE_DIR = resolve_base_dir()
ensure_runtime_layout(BASE_DIR)
VALIDATION_DIR = resolve_validation_report_dir(BASE_DIR)


def main():
    parser = argparse.ArgumentParser(description='酒店植入优化脚本')
    parser.add_argument('--input-dir', type=str, required=True, help='输入目录（草稿）')
    parser.add_argument('--output-dir', type=str, required=True, help='输出目录（优化后）')
    parser.add_argument('--personas-dir', type=str, default=str(BASE_DIR / 'config' / 'personas'), help='人设配置目录')
    parser.add_argument('--report', type=str, default=None, help='可选报告输出路径')
    
    args = parser.parse_args()
    
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    personas_dir = Path(args.personas_dir)
    report_file = Path(args.report) if args.report else VALIDATION_DIR / f"hotel_optimization_{input_dir.name}.json"
    
    print("=" * 60)
    print("🎯 酒店植入优化脚本")
    print("=" * 60)
    print(f"输入目录：{input_dir}")
    print(f"输出目录：{output_dir}")
    print(f"人设目录：{personas_dir}")
    print()

    report = run_hotel_optimization_workflow(
        HotelOptimizationWorkflowRequest(
            input_dir=input_dir,
            output_dir=output_dir,
            personas_dir=personas_dir,
            report_path=report_file,
        )
    )

    print("=" * 60)
    print("📊 处理完成！")
    print("=" * 60)
    print(f"总文件数：{report['total_files']}")
    print(f"发现问题的文件：{report['files_with_issues']}")
    print(f"已优化的文件：{report['files_optimized']}")
    print(f"报告已保存到：{report_file}")


if __name__ == "__main__":
    main()
