#!/usr/bin/env python3
"""小红书笔记质量验证与评分脚本."""

import argparse
from pathlib import Path
from datetime import datetime
from _project_paths import ensure_project_root_on_path, resolve_base_dir

ensure_project_root_on_path()

from xhs_post.models import ValidationWorkflowRequest
from xhs_post.workflows.release_validation import run_validation_workflow

BASE_DIR = resolve_base_dir()


def main():
    parser = argparse.ArgumentParser(description="小红书笔记质量验证与评分")
    parser.add_argument("--input-dir", type=str, default=str(BASE_DIR / "generated_posts" / "2026-03-15"))
    parser.add_argument("--output", type=str, default=None)
    parser.add_argument("--pattern", type=str, default="*.md")
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_file = Path(args.output) if args.output else input_dir / "quality_report.json"

    print("=" * 60)
    print("📊 小红书笔记质量验证与评分报告")
    print("=" * 60)
    print(f"检查目录：{input_dir}")
    print(f"检查时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    report = run_validation_workflow(
        ValidationWorkflowRequest(
            input_dir=input_dir,
            output_path=output_file,
            pattern=args.pattern,
        )
    )
    posts_data = report["posts"]
    if not posts_data:
        print("❌ 未找到任何笔记文件！")
        return

    print(f"📁 加载 {len(posts_data)} 篇笔记\n")

    print("🔍 检查内容重复度...")
    high_dup_count = report["summary"]["high_dup_count"]
    print(f"⚠️ 发现 {high_dup_count} 篇笔记存在高重复度问题\n")

    for index, result in enumerate(posts_data, 1):
        print(f"[{index}/{len(posts_data)}] {result['filename']}")
        total_score = result["total_score"]
        status = "✅" if total_score["percentage"] >= 70 else "⚠️"
        print(f"  {status} 总分：{total_score['total']}/{total_score['max']} ({total_score['percentage']}%) - 等级：{total_score['grade']}")
        if result["title_score"]["issues"]:
            print(f"     标题问题：{', '.join(result['title_score']['issues'])}")
        if result["body_score"]["issues"]:
            print(f"     正文问题：{', '.join(result['body_score']['issues'])}")
        if result["tags_score"]["issues"]:
            print(f"     标签问题：{', '.join(result['tags_score']['issues'])}")
        print()

    print("=" * 60)
    print("📊 总体统计")
    print("=" * 60)
    print(f"平均分数：{report['summary']['avg_score']}%")
    print(f"等级分布：{report['summary']['grade_distribution']}")
    print(f"高重复度笔记：{high_dup_count} 篇")
    print()
    print(f"💾 完整报告已保存到：{output_file}")

    print("\n" + "=" * 60)
    print("💡 改进建议")
    print("=" * 60)

    all_titles = [result['selected_title'] for result in posts_data]
    if len(set(all_titles)) == 1:
        print("❌ 严重问题：所有笔记标题完全相同！需要修复生成脚本")

    if high_dup_count > 0:
        print(f"⚠️ {high_dup_count} 篇笔记内容重复度过高，需要增加差异化")

    common_issues = {}
    for result in posts_data:
        for issue in result['title_score']['issues'] + result['body_score']['issues'] + result['tags_score']['issues']:
            common_issues[issue] = common_issues.get(issue, 0) + 1

    if common_issues:
        print("\n常见问题 TOP 5:")
        for issue, count in sorted(common_issues.items(), key=lambda x: -x[1])[:5]:
            print(f"  - {issue} ({count}篇)")

if __name__ == "__main__":
    main()
