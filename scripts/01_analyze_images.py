#!/usr/bin/env python3
"""
01_analyze_images.py - 使用 Vision AI 识别本地图片内容
输出：config/image_analysis.json

注意：图片分析需要 OpenClaw image 工具支持。
如果 image 工具不可用，将使用基于文件名的智能推断生成分析数据。
"""

from pathlib import Path

import argparse

from _project_paths import ensure_project_root_on_path, resolve_base_dir

ensure_project_root_on_path()

from xhs_post.models import ImageWorkflowRequest
from xhs_post.paths import ensure_runtime_layout, resolve_config_dir, resolve_image_analysis_artifact_file
from xhs_post.storage import mirror_json_to_legacy
from xhs_post.workflows.image_analysis import run_image_analysis_workflow


BASE_DIR = resolve_base_dir()
ensure_runtime_layout(BASE_DIR)
IMAGES_DIR = BASE_DIR / "local_images"
OUTPUT_FILE = resolve_image_analysis_artifact_file(BASE_DIR)
LEGACY_OUTPUT_FILE = resolve_config_dir(BASE_DIR) / "image_analysis.json"

def main():
    parser = argparse.ArgumentParser(description="图片分析 workflow")
    parser.add_argument("--images-dir", type=str, default=str(IMAGES_DIR), help="图片目录")
    parser.add_argument("--output", type=str, default=str(OUTPUT_FILE), help="输出 JSON 路径")
    parser.add_argument("--topic", type=str, default=None, help="可选主题，用于增强图片标签")
    args = parser.parse_args()

    images_dir = Path(args.images_dir)
    output_file = Path(args.output)

    print("=" * 60)
    print("📸 小红书图片分析工具")
    print("=" * 60)
    output_data = run_image_analysis_workflow(
        ImageWorkflowRequest(
            images_dir=images_dir,
            output_path=output_file,
            topic=args.topic,
        )
    )
    if output_file == OUTPUT_FILE:
        mirror_json_to_legacy(output_file, LEGACY_OUTPUT_FILE)

    print(f"\n{'=' * 60}")
    print(f"✅ 图片分析完成！")
    print(f"📊 共分析 {output_data['total_images']} 张图片")
    print(f"📁 图片目录：{images_dir}")
    print(f"💾 结果已保存到：{output_file}")
    print(f"{'=' * 60}")

    return output_data

if __name__ == "__main__":
    main()
