#!/usr/bin/env python3
"""
XHS_Post CLI - 统一命令行入口

用法:
  xhs analyze --topic "亲子酒店"           # 分析热点数据
  xhs generate --topic "亲子酒店" --count 8  # 生成笔记
  xhs validate --input-dir generated_posts/2026-03-15  # 验证笔记
  xhs optimize --input-dir xxx --output-dir yyy  # 酒店植入优化
  xhs pipeline --topic "亲子酒店"          # 完整流程（分析 + 生成）
  xhs multi-account --topic "亲子酒店"     # 多账号编排
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

# 添加项目路径
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR / "scripts"))
sys.path.insert(0, str(BASE_DIR))

from _project_paths import ensure_project_root_on_path, resolve_base_dir

ensure_project_root_on_path()

from xhs_post.logger import get_logger
from xhs_post.paths import (
    ensure_runtime_layout,
    resolve_config_dir,
    resolve_generation_state_file,
    resolve_trending_artifact_file,
    resolve_validation_report_dir,
)
from xhs_post.storage import seed_file_from_legacy
from xhs_post.models import (
    LLMPostWorkflowRequest,
    ValidationWorkflowRequest,
    HotelOptimizationWorkflowRequest,
    MultiAccountWorkflowRequest,
)
from xhs_post.workflows.llm_post_generation import run_llm_post_generation_workflow
from xhs_post.workflows.release_validation import run_validation_workflow
from xhs_post.workflows.hotel_optimization import run_hotel_optimization_workflow
from xhs_post.workflows.multi_account import run_multi_account_workflow

logger = get_logger('xhs.cli')


# ==================== 命令实现 ====================

def cmd_analyze(args):
    """分析热点数据 - 委托到 02_analyze_trending.py"""
    import subprocess
    script = BASE_DIR / "scripts/02_analyze_trending.py"
    cmd = [sys.executable, str(script), "--topic", args.topic]
    if args.keywords:
        cmd.extend(["--keywords", args.keywords])
    result = subprocess.run(cmd, cwd=BASE_DIR)
    return result.returncode


def cmd_generate(args):
    """生成笔记"""
    BASE_DIR = resolve_base_dir()
    ensure_runtime_layout(BASE_DIR)
    
    config_file = resolve_trending_artifact_file(BASE_DIR)
    legacy_config_file = resolve_config_dir(BASE_DIR) / "trending_analysis.json"
    state_file = resolve_generation_state_file(BASE_DIR)
    legacy_state_file = resolve_config_dir(BASE_DIR) / "generation_state.json"
    raw_posts_dir = BASE_DIR / "xhs_post_from_search" / "jsonl"
    output_dir = Path(args.output_dir) if args.output_dir else BASE_DIR / "generated_posts" / datetime.now().strftime("%Y-%m-%d")
    
    print("=" * 60)
    print("📝 小红书笔记生成")
    print("=" * 60)
    print(f"🎯 主题：{args.topic}")
    print(f"📊 数量：{args.count} 篇")
    print(f"📂 输出：{output_dir}")
    print()
    
    # 初始化状态文件
    seed_file_from_legacy(state_file, legacy_state_file, default_data={
        "used_combinations": [],
        "daily_history": [],
        "total_posts_generated": 0,
        "last_generation": {},
        "content_signatures": []
    })
    seed_file_from_legacy(config_file, legacy_config_file, default_data={})
    
    # 获取热点分析输入文件（使用 getattr 兼容 pipeline 调用）
    trending_input = getattr(args, 'input', None)
    
    # 执行工作流
    output_files = run_llm_post_generation_workflow(
        LLMPostWorkflowRequest(
            topic=args.topic,
            count=args.count,
            trending_input=Path(trending_input) if trending_input else config_file,
            output_dir=output_dir,
            raw_posts_dir=raw_posts_dir,
            state_file=state_file,
            provider=getattr(args, 'provider', None),
            seed=getattr(args, 'seed', None),
        )
    )
    
    print(f"\n✅ 完成！生成 {len(output_files)} 篇笔记")
    print(f"📂 位置：{output_dir}")
    return 0


def cmd_validate(args):
    """验证笔记质量"""
    BASE_DIR = resolve_base_dir()
    ensure_runtime_layout(BASE_DIR)
    
    input_dir = Path(args.input_dir)
    output_file = Path(args.output) if args.output else resolve_validation_report_dir(BASE_DIR) / f"quality_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    print("=" * 60)
    print("📊 笔记质量验证")
    print("=" * 60)
    print(f"📁 目录：{input_dir}")
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
        return 1
    
    print(f"📄 检查 {len(posts_data)} 篇笔记\n")
    
    high_dup_count = report["summary"]["high_dup_count"]
    print(f"⚠️  高重复度：{high_dup_count} 篇\n")
    
    for idx, result in enumerate(posts_data, 1):
        total_score = result["total_score"]
        status = "✅" if total_score["percentage"] >= 70 else "⚠️"
        print(f"{idx}. {result['filename'][:40]} - {status} {total_score['percentage']}%")
    
    print(f"\n📊 平均分：{report['summary']['avg_score']}%")
    print(f"💾 报告：{output_file}")
    return 0


def cmd_optimize(args):
    """酒店植入优化"""
    BASE_DIR = resolve_base_dir()
    ensure_runtime_layout(BASE_DIR)
    
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    personas_dir = Path(args.personas_dir) if args.personas_dir else BASE_DIR / "config" / "personas"
    report_file = Path(args.report) if args.report else resolve_validation_report_dir(BASE_DIR) / f"hotel_optimization_{input_dir.name}.json"
    
    print("=" * 60)
    print("🎯 酒店植入优化")
    print("=" * 60)
    print(f"📥 输入：{input_dir}")
    print(f"📤 输出：{output_dir}")
    print()
    
    report = run_hotel_optimization_workflow(
        HotelOptimizationWorkflowRequest(
            input_dir=input_dir,
            output_dir=output_dir,
            personas_dir=personas_dir,
            report_path=report_file,
        )
    )
    
    print(f"\n✅ 处理完成")
    print(f"📄 总文件：{report['total_files']}")
    print(f"🔧 已优化：{report['files_optimized']}")
    print(f"💾 报告：{report_file}")
    return 0


def cmd_multi_account(args):
    """多账号编排"""
    BASE_DIR = resolve_base_dir()
    ensure_runtime_layout(BASE_DIR)
    
    input_file = Path(args.input) if args.input else BASE_DIR / "config" / "trending_analysis.json"
    output_dir = Path(args.output_dir) if args.output_dir else BASE_DIR / "generated_posts"
    personas_dir = BASE_DIR / "config" / "personas"
    
    print("=" * 60)
    print("👥 多账号内容编排")
    print("=" * 60)
    print(f"🎯 主题：{args.topic}")
    print()
    
    result = run_multi_account_workflow(
        MultiAccountWorkflowRequest(
            topic=args.topic,
            input_path=input_file,
            output_dir=output_dir,
            personas_dir=personas_dir,
        )
    )
    
    print(f"\n✅ 编排完成")
    print(f"👥 账号数：{len(result['accounts'])}")
    print(f"\n📱 Telegram 预览:\n{result['telegram_preview']}")
    return 0


def cmd_pipeline(args):
    """完整流程：分析 + 生成 + 酒店植入"""
    print("=" * 60)
    print("🚀 执行完整流程：分析 → 生成 → 酒店植入")
    print("=" * 60)
    print(f"🎯 主题：{args.topic}")
    print()
    
    # Step 1: 分析
    print("📊 Step 1/3: 热点分析...")
    if cmd_analyze(args) != 0:
        print("❌ 分析失败")
        return 1
    
    # Step 2: 生成
    print("\n📝 Step 2/3: 生成笔记...")
    if cmd_generate(args) != 0:
        print("❌ 生成失败")
        return 1
    
    # Step 3: 酒店植入优化（自动）
    print("\n🏨 Step 3/3: 酒店植入优化...")
    BASE_DIR = resolve_base_dir()
    output_dir = Path(args.output_dir) if args.output_dir else BASE_DIR / "generated_posts" / datetime.now().strftime("%Y-%m-%d")
    personas_dir = BASE_DIR / "config" / "personas"
    
    if personas_dir.exists():
        from xhs_post.models import HotelOptimizationWorkflowRequest
        from xhs_post.workflows.hotel_optimization import run_hotel_optimization_workflow
        
        optimized_dir = output_dir.parent / f"{output_dir.name}_optimized"
        report_file = output_dir.parent / "hotel_optimization_report.json"
        
        try:
            report = run_hotel_optimization_workflow(
                HotelOptimizationWorkflowRequest(
                    input_dir=output_dir,
                    output_dir=optimized_dir,
                    personas_dir=personas_dir,
                    report_path=report_file,
                )
            )
            print(f"✅ 酒店植入完成")
            print(f"   优化文件：{report['files_optimized']}/{report['total_files']}")
            print(f"   输出目录：{optimized_dir}")
        except Exception as e:
            print(f"⚠️  酒店植入跳过：{e}")
    else:
        print("⚠️  无人设配置，跳过酒店植入")
    
    return 0


def cmd_download_images(args):
    """下载图片"""
    import subprocess
    script = BASE_DIR / "scripts/download_images.py"
    cmd = [sys.executable, str(script)]
    
    if args.topic:
        cmd.extend(["--topic", args.topic])
    if args.input_dir:
        cmd.extend(["--input-dir", str(args.input_dir)])
    if args.output_dir:
        cmd.extend(["--output-dir", str(args.output_dir)])
    if args.count:
        cmd.extend(["--count", str(args.count)])
    
    result = subprocess.run(cmd, cwd=BASE_DIR)
    return result.returncode


def cmd_clean(args):
    """清理临时文件"""
    import shutil
    
    BASE_DIR = resolve_base_dir()
    
    print("=" * 60)
    print("🧹 清理临时文件")
    print("=" * 60)
    
    dirs_to_clean = [
        BASE_DIR / "__pycache__",
        BASE_DIR / ".cache",
        BASE_DIR / "logs",
    ]
    
    for dir_path in dirs_to_clean:
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"✓ 清理：{dir_path}")
    
    print("\n✅ 清理完成")
    return 0


# ==================== CLI 入口 ====================

def main():
    parser = argparse.ArgumentParser(
        description="XHS_Post - 小红书笔记自动生成系统",
        prog="xhs"
    )
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # analyze 命令
    p_analyze = subparsers.add_parser("analyze", help="分析热点数据")
    p_analyze.add_argument("--topic", "-t", type=str, required=True, help="主题关键词")
    p_analyze.add_argument("--keywords", "-k", type=str, help="自定义关键词扩展")
    p_analyze.set_defaults(func=cmd_analyze)
    
    # generate 命令
    p_gen = subparsers.add_parser("generate", help="生成笔记")
    p_gen.add_argument("--topic", "-t", type=str, required=True, help="主题")
    p_gen.add_argument("--count", "-c", type=int, default=8, help="生成数量")
    p_gen.add_argument("--input", "-i", type=str, help="热点分析输入")
    p_gen.add_argument("--output-dir", "-o", type=str, help="输出目录")
    p_gen.add_argument("--provider", type=str, help="LLM provider")
    p_gen.add_argument("--seed", type=int, help="随机种子")
    p_gen.set_defaults(func=cmd_generate)
    
    # validate 命令
    p_val = subparsers.add_parser("validate", help="验证笔记质量")
    p_val.add_argument("--input-dir", type=str, required=True, help="输入目录")
    p_val.add_argument("--output", "-o", type=str, help="输出报告路径")
    p_val.add_argument("--pattern", type=str, default="*.md", help="文件匹配模式")
    p_val.set_defaults(func=cmd_validate)
    
    # optimize 命令
    p_opt = subparsers.add_parser("optimize", help="酒店植入优化")
    p_opt.add_argument("--input-dir", type=str, required=True, help="输入目录")
    p_opt.add_argument("--output-dir", type=str, required=True, help="输出目录")
    p_opt.add_argument("--personas-dir", type=str, help="人设配置目录")
    p_opt.add_argument("--report", type=str, help="报告输出路径")
    p_opt.set_defaults(func=cmd_optimize)
    
    # multi-account 命令
    p_multi = subparsers.add_parser("multi-account", help="多账号编排")
    p_multi.add_argument("--topic", "-t", type=str, required=True, help="主题")
    p_multi.add_argument("--input", "-i", type=str, help="热点分析输入")
    p_multi.add_argument("--output-dir", "-o", type=str, help="输出目录")
    p_multi.set_defaults(func=cmd_multi_account)
    
    # pipeline 命令
    p_pipe = subparsers.add_parser("pipeline", help="完整流程（分析 + 生成 + 酒店植入）")
    p_pipe.add_argument("--topic", "-t", type=str, required=True, help="主题")
    p_pipe.add_argument("--count", "-c", type=int, default=8, help="生成数量")
    p_pipe.add_argument("--keywords", "-k", type=str, help="自定义关键词")
    p_pipe.add_argument("--output-dir", "-o", type=str, help="输出目录")
    p_pipe.set_defaults(func=cmd_pipeline)
    
    # download-images 命令
    p_dl = subparsers.add_parser("download-images", help="下载小红书图片到本地")
    p_dl.add_argument("--topic", "-t", type=str, help="主题名称")
    p_dl.add_argument("--input-dir", type=Path, help="Markdown 文件目录")
    p_dl.add_argument("--output-dir", "-o", type=Path, help="输出目录")
    p_dl.add_argument("--count", "-c", type=int, default=20, help="最多下载数量")
    p_dl.set_defaults(func=cmd_download_images)
    
    # clean 命令
    p_clean = subparsers.add_parser("clean", help="清理临时文件")
    p_clean.set_defaults(func=cmd_clean)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
