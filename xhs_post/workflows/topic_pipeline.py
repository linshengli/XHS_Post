from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from xhs_post.models import TopicWorkflowRequest
from xhs_post.paths import resolve_base_dir, resolve_repo_root


def _run_command(command: list[str], env: dict[str, str], cwd: Path) -> None:
    subprocess.run(command, cwd=cwd, env=env, check=True)


def run_topic_pipeline(request: TopicWorkflowRequest) -> dict[str, str]:
    repo_root = resolve_repo_root()
    base_dir = resolve_base_dir()
    scripts_dir = repo_root / "scripts"

    analysis_output = request.analysis_output or (
        base_dir / "config" / f"trending_analysis_{request.topic}.json"
    )
    generation_output = request.generation_output or (base_dir / "generated_posts")

    env = os.environ | {"XHS_POST_BASE_DIR": str(base_dir)}

    _run_command(
        [
            sys.executable,
            str(scripts_dir / "02_analyze_trending.py"),
            "--topic",
            request.topic,
            "--output",
            str(analysis_output),
        ],
        env,
        repo_root,
    )

    generate_command = [
        sys.executable,
        str(scripts_dir / "03_generate_posts.py"),
        "--topic",
        request.topic,
        "--count",
        str(request.count),
        "--input",
        str(analysis_output),
        "--output-dir",
        str(generation_output),
    ]
    if request.seed is not None:
        generate_command.extend(["--seed", str(request.seed)])

    _run_command(generate_command, env, repo_root)

    return {
        "topic": request.topic,
        "analysis_output": str(analysis_output),
        "generation_output": str(generation_output),
    }
