from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def write_llm_repo(base_dir: Path) -> None:
    (base_dir / "config").mkdir(parents=True, exist_ok=True)
    (base_dir / "generated_posts").mkdir(parents=True, exist_ok=True)
    (base_dir / "xhs_post_from_search" / "jsonl").mkdir(parents=True, exist_ok=True)
    fixture = REPO_ROOT / "tests" / "fixtures" / "search_contents_sample.jsonl"
    (base_dir / "xhs_post_from_search" / "jsonl" / "search_contents_sample.jsonl").write_text(
        fixture.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (base_dir / "config" / "generation_state.json").write_text(
        json.dumps({"used_combinations": [], "daily_history": [], "total_posts_generated": 0, "last_generation": {}}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def run_script(script_name: str, *args: str, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / script_name), *args],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )


def test_llm_generation_uses_mock_provider_and_crawled_images(tmp_path: Path):
    write_llm_repo(tmp_path)
    env = os.environ | {"XHS_POST_BASE_DIR": str(tmp_path), "XHS_POST_LLM_PROVIDER": "mock"}

    run_script("02_analyze_trending.py", "--topic", "千岛湖亲子酒店", env=env)
    output_dir = tmp_path / "generated_posts" / "llm"
    run_script(
        "generate_posts_llm.py",
        "--topic",
        "千岛湖亲子酒店",
        "--count",
        "1",
        "--input",
        str(tmp_path / "config" / "trending_analysis.json"),
        "--output-dir",
        str(output_dir),
        "--provider",
        "mock",
        "--seed",
        "1",
        env=env,
    )

    generated_file = next(output_dir.glob("*.md"))
    content = generated_file.read_text(encoding="utf-8")
    assert "https://img.example.com/hotel-cover.jpg" in content
    assert "## 📸 配图" in content
    assert "#千岛湖亲子酒店" in content
    assert "*Provider：mock*" in content
