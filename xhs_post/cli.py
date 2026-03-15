from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from xhs_post.models import (
    DraftRequirementsWorkflowRequest,
    ImagePlanWorkflowRequest,
    LLMPostWorkflowRequest,
    ReleaseCandidateWorkflowRequest,
    ValidationWorkflowRequest,
)
from xhs_post.paths import (
    ensure_runtime_layout,
    resolve_config_dir,
    resolve_base_dir,
    resolve_image_analysis_artifact_file,
    resolve_trending_artifact_file,
    resolve_validation_report_dir,
)
from xhs_post.models import HotelOptimizationWorkflowRequest
from xhs_post.workflows.draft_requirements import run_draft_requirements_workflow
from xhs_post.workflows.image_plan import run_image_plan_workflow
from xhs_post.workflows.llm_post_generation import run_llm_post_generation_workflow
from xhs_post.workflows.release_candidate import run_release_candidate_workflow
from xhs_post.workflows.release_validation import run_validation_workflow
from xhs_post.workflows.hotel_optimization import run_hotel_optimization_workflow


def _run_script(script_name: str, *args: str) -> None:
    base_dir = resolve_base_dir()
    repo_root = Path(__file__).resolve().parent.parent
    env = os.environ | {"XHS_POST_BASE_DIR": str(base_dir)}
    subprocess.run([sys.executable, str(repo_root / "scripts" / script_name), *args], cwd=repo_root, env=env, check=True)


def build_parser(base_dir: Path) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="XHS_Post 统一 CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze_parser = subparsers.add_parser("analyze")
    analyze_parser.add_argument("--topic", required=True)
    analyze_parser.add_argument("--output", default=str(resolve_trending_artifact_file(base_dir)))

    image_parser = subparsers.add_parser("analyze-images")
    image_parser.add_argument("--topic", default=None)
    image_parser.add_argument("--images-dir", default=str(base_dir / "local_images"))
    image_parser.add_argument("--output", default=str(resolve_image_analysis_artifact_file(base_dir)))

    image_plan_parser = subparsers.add_parser("image-plan")
    image_plan_parser.add_argument("--topic", required=True)
    image_plan_parser.add_argument("--angle", default=None)
    image_plan_parser.add_argument("--count", type=int, default=4)
    image_plan_parser.add_argument("--input", default=str(resolve_image_analysis_artifact_file(base_dir)))
    image_plan_parser.add_argument("--output", default=str(resolve_validation_report_dir(base_dir) / "image_plan.json"))

    generate_parser = subparsers.add_parser("generate")
    generate_parser.add_argument("--topic", required=True)
    generate_parser.add_argument("--count", type=int, default=10)
    generate_parser.add_argument("--output-dir", default=str(base_dir / "generated_posts"))

    llm_parser = subparsers.add_parser("llm-generate")
    llm_parser.add_argument("--topic", required=True)
    llm_parser.add_argument("--count", type=int, default=8)
    llm_parser.add_argument("--provider", default=None)
    llm_parser.add_argument("--output-dir", default=str(base_dir / "generated_posts" / "llm"))
    llm_parser.add_argument("--seed", type=int, default=None)

    draft_parser = subparsers.add_parser("draft-requirements")
    draft_parser.add_argument("--topic", required=True)
    draft_parser.add_argument("--input", default=str(resolve_trending_artifact_file(base_dir)))
    draft_parser.add_argument("--output", default=str(resolve_validation_report_dir(base_dir) / "draft_requirements.md"))

    score_parser = subparsers.add_parser("score")
    score_parser.add_argument("--input-dir", required=True)
    score_parser.add_argument("--output", default=None)

    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--input-dir", required=True)
    validate_parser.add_argument("--output", default=None)

    optimize_parser = subparsers.add_parser("optimize-hotel")
    optimize_parser.add_argument("--input-dir", required=True)
    optimize_parser.add_argument("--output-dir", required=True)
    optimize_parser.add_argument("--report", default=str(resolve_validation_report_dir(base_dir) / "hotel_optimization_cli.json"))
    optimize_parser.add_argument("--personas-dir", default=str(resolve_config_dir(base_dir) / "personas"))

    release_parser = subparsers.add_parser("release-candidate")
    release_parser.add_argument("--topic", required=True)
    release_parser.add_argument("--count", type=int, default=8)
    release_parser.add_argument("--use-llm", action="store_true")
    release_parser.add_argument("--provider", default=None)
    release_parser.add_argument("--output-dir", default=str(base_dir / "generated_posts" / datetime.now().strftime("%Y-%m-%d")))
    release_parser.add_argument("--validation-output", default=str(resolve_validation_report_dir(base_dir) / "release_candidate.json"))
    release_parser.add_argument("--seed", type=int, default=None)

    return parser


def main() -> None:
    base_dir = resolve_base_dir()
    ensure_runtime_layout(base_dir)
    parser = build_parser(base_dir)
    args = parser.parse_args()

    if args.command == "analyze":
        _run_script("02_analyze_trending.py", "--topic", args.topic, "--output", args.output)
        return

    if args.command == "analyze-images":
        _run_script("01_analyze_images.py", "--images-dir", args.images_dir, "--output", args.output, *(["--topic", args.topic] if args.topic else []))
        return

    if args.command == "image-plan":
        result = run_image_plan_workflow(
            ImagePlanWorkflowRequest(
                topic=args.topic,
                image_analysis_path=Path(args.input),
                output_path=Path(args.output),
                angle=args.angle,
                count=args.count,
            )
        )
        print(result)
        return

    if args.command == "generate":
        _run_script("03_generate_posts.py", "--topic", args.topic, "--count", str(args.count), "--output-dir", args.output_dir)
        return

    if args.command == "llm-generate":
        result = run_llm_post_generation_workflow(
            LLMPostWorkflowRequest(
                topic=args.topic,
                count=args.count,
                trending_input=resolve_trending_artifact_file(base_dir),
                output_dir=Path(args.output_dir),
                raw_posts_dir=base_dir / "xhs_post_from_search" / "jsonl",
                state_file=base_dir / "state" / "generation_state.json",
                provider=args.provider,
                seed=args.seed,
            )
        )
        print(f"generated={len(result)}")
        return

    if args.command == "draft-requirements":
        content = run_draft_requirements_workflow(
            DraftRequirementsWorkflowRequest(
                topic=args.topic,
                trending_input=Path(args.input),
                output_path=Path(args.output),
            )
        )
        print(content.splitlines()[0])
        return

    if args.command in {"score", "validate"}:
        output = Path(args.output) if args.output else resolve_validation_report_dir(base_dir) / f"{args.command}_report.json"
        report = run_validation_workflow(
            ValidationWorkflowRequest(
                input_dir=Path(args.input_dir),
                output_path=output,
                pattern="*.md",
            )
        )
        print(report["summary"])
        return

    if args.command == "optimize-hotel":
        report = run_hotel_optimization_workflow(
            HotelOptimizationWorkflowRequest(
                input_dir=Path(args.input_dir),
                output_dir=Path(args.output_dir),
                personas_dir=Path(args.personas_dir),
                report_path=Path(args.report),
            )
        )
        print(report["files_optimized"])
        return

    result = run_release_candidate_workflow(
        ReleaseCandidateWorkflowRequest(
            topic=args.topic,
            count=args.count,
            output_dir=Path(args.output_dir),
            validation_output=Path(args.validation_output),
            use_llm=args.use_llm,
            provider=args.provider,
            seed=args.seed,
        )
    )
    print(result)
