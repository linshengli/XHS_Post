from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from xhs_post.models import LLMPostWorkflowRequest, ReleaseCandidateWorkflowRequest, ValidationWorkflowRequest
from xhs_post.paths import resolve_base_dir, resolve_repo_root, resolve_trending_artifact_file
from xhs_post.workflows.llm_post_generation import run_llm_post_generation_workflow
from xhs_post.workflows.release_validation import run_validation_workflow
from xhs_post.workflows.topic_pipeline import run_topic_pipeline
from xhs_post.models import TopicWorkflowRequest


def _run_analysis(topic: str, repo_root: Path, base_dir: Path, analysis_output: Path) -> None:
    env = os.environ | {"XHS_POST_BASE_DIR": str(base_dir)}
    subprocess.run(
        [
            sys.executable,
            str(repo_root / "scripts" / "02_analyze_trending.py"),
            "--topic",
            topic,
            "--output",
            str(analysis_output),
        ],
        cwd=repo_root,
        env=env,
        check=True,
    )


def run_release_candidate_workflow(request: ReleaseCandidateWorkflowRequest) -> dict[str, Any]:
    repo_root = resolve_repo_root()
    base_dir = resolve_base_dir()
    analysis_output = resolve_trending_artifact_file(base_dir)

    if request.use_llm:
        _run_analysis(request.topic, repo_root, base_dir, analysis_output)
        generated_files = run_llm_post_generation_workflow(
            LLMPostWorkflowRequest(
                topic=request.topic,
                count=request.count,
                trending_input=analysis_output,
                output_dir=request.output_dir,
                raw_posts_dir=base_dir / "xhs_post_from_search" / "jsonl",
                state_file=base_dir / "state" / "generation_state.json",
                provider=request.provider,
                seed=request.seed,
            )
        )
        generation_output = request.output_dir
    else:
        topic_result = run_topic_pipeline(
            TopicWorkflowRequest(
                topic=request.topic,
                count=request.count,
                analysis_output=analysis_output,
                generation_output=request.output_dir,
                seed=request.seed,
            )
        )
        generated_files = list(Path(topic_result["generation_output"]).glob("*.md"))
        generation_output = Path(topic_result["generation_output"])

    validation_report = run_validation_workflow(
        ValidationWorkflowRequest(
            input_dir=generation_output,
            output_path=request.validation_output,
            pattern="*.md",
        )
    )
    return {
        "topic": request.topic,
        "analysis_output": str(analysis_output),
        "generation_output": str(generation_output),
        "generated_files": [str(path) for path in generated_files],
        "validation_output": str(request.validation_output),
        "validation_summary": validation_report["summary"],
    }
