from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def write_test_repo(base_dir: Path) -> None:
    (base_dir / "config").mkdir(parents=True, exist_ok=True)
    (base_dir / "generated_posts").mkdir(parents=True, exist_ok=True)
    (base_dir / "xhs_post_from_search" / "jsonl").mkdir(parents=True, exist_ok=True)
    (base_dir / "local_images" / "sample").mkdir(parents=True, exist_ok=True)

    fixture = REPO_ROOT / "tests" / "fixtures" / "search_contents_sample.jsonl"
    (base_dir / "xhs_post_from_search" / "jsonl" / "search_contents_sample.jsonl").write_text(
        fixture.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (base_dir / "config" / "generation_state.json").write_text(
        json.dumps(
            {
                "used_combinations": [],
                "daily_history": [],
                "total_posts_generated": 0,
                "last_generation": {},
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    for name in ["cover.jpg", "scene.jpg", "detail.jpg", "experience.jpg"]:
        (base_dir / "local_images" / "sample" / name).write_text("placeholder", encoding="utf-8")


def run_script(script_name: str, *args: str, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / script_name), *args],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )


def test_e2e_generation_for_requested_topics(tmp_path: Path):
    write_test_repo(tmp_path)
    env = os.environ | {"XHS_POST_BASE_DIR": str(tmp_path)}

    topics = ["千岛湖亲子酒店", "千岛湖旅游攻略"]
    for topic in topics:
        run_script("02_analyze_trending.py", "--topic", topic, env=env)
        output_dir = tmp_path / "generated_posts" / topic
        run_script(
            "03_generate_posts.py",
            "--topic",
            topic,
            "--count",
            "2",
            "--seed",
            "7",
            "--output-dir",
            str(output_dir),
            env=env,
        )

        generated_files = sorted(output_dir.glob("*.md"))
        assert len(generated_files) == 2
        assert topic in generated_files[0].read_text(encoding="utf-8")


def test_topic_workflow_entrypoint_runs_end_to_end(tmp_path: Path):
    write_test_repo(tmp_path)
    env = os.environ | {"XHS_POST_BASE_DIR": str(tmp_path)}
    output_dir = tmp_path / "generated_posts" / "workflow"
    analysis_output = tmp_path / "config" / "workflow.json"

    run_script(
        "06_run_topic_workflow.py",
        "--topic",
        "千岛湖旅游攻略",
        "--count",
        "1",
        "--seed",
        "9",
        "--analysis-output",
        str(analysis_output),
        "--generation-output",
        str(output_dir),
        env=env,
    )

    assert analysis_output.exists()
    assert len(list(output_dir.glob("*.md"))) == 1


def test_e2e_generation_includes_real_image_list(tmp_path: Path):
    write_test_repo(tmp_path)
    env = os.environ | {"XHS_POST_BASE_DIR": str(tmp_path)}

    run_script(
        "01_analyze_images.py",
        "--images-dir",
        str(tmp_path / "local_images"),
        "--output",
        str(tmp_path / "config" / "image_analysis.json"),
        "--topic",
        "千岛湖亲子酒店",
        env=env,
    )
    run_script("02_analyze_trending.py", "--topic", "千岛湖亲子酒店", env=env)
    output_dir = tmp_path / "generated_posts" / "with_images"
    run_script(
        "03_generate_posts.py",
        "--topic",
        "千岛湖亲子酒店",
        "--count",
        "1",
        "--seed",
        "3",
        "--output-dir",
        str(output_dir),
        env=env,
    )

    generated_file = next(output_dir.glob("*.md"))
    content = generated_file.read_text(encoding="utf-8")
    assert "## 📸 配图" in content
    assert "cover.jpg" in content or "scene.jpg" in content
