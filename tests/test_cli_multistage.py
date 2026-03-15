from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class CLIMultiStageTests(unittest.TestCase):
    def test_cli_multistage_flow(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            (base_dir / "config").mkdir(parents=True, exist_ok=True)
            (base_dir / "xhs_post_from_search" / "jsonl").mkdir(parents=True, exist_ok=True)
            (base_dir / "local_images" / "topic_a").mkdir(parents=True, exist_ok=True)
            fixture = REPO_ROOT / "tests" / "fixtures" / "search_contents_sample.jsonl"
            (base_dir / "xhs_post_from_search" / "jsonl" / fixture.name).write_text(
                fixture.read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            (base_dir / "config" / "generation_state.json").write_text(
                json.dumps({"used_combinations": [], "daily_history": [], "total_posts_generated": 0, "last_generation": {}}, ensure_ascii=False),
                encoding="utf-8",
            )
            (base_dir / "local_images" / "topic_a" / "sample.jpg").write_text("fake", encoding="utf-8")

            env = os.environ | {"XHS_POST_BASE_DIR": str(base_dir), "XHS_POST_LLM_PROVIDER": "mock"}

            def run_cli(*args: str) -> None:
                subprocess.run(
                    [sys.executable, str(REPO_ROOT / "scripts" / "xhs_cli.py"), *args],
                    cwd=REPO_ROOT,
                    env=env,
                    text=True,
                    capture_output=True,
                    check=True,
                )

            run_cli("analyze", "--topic", "千岛湖亲子酒店")
            run_cli("analyze-images", "--topic", "千岛湖亲子酒店", "--images-dir", str(base_dir / "local_images"))
            run_cli("image-plan", "--topic", "千岛湖亲子酒店")
            run_cli("draft-requirements", "--topic", "千岛湖亲子酒店")
            run_cli(
                "release-candidate",
                "--topic",
                "千岛湖亲子酒店",
                "--count",
                "1",
                "--use-llm",
                "--provider",
                "mock",
                "--output-dir",
                str(base_dir / "generated_posts" / "release"),
                "--validation-output",
                str(base_dir / "artifacts" / "validation" / "release.json"),
            )
            run_cli(
                "validate",
                "--input-dir",
                str(base_dir / "generated_posts" / "release"),
                "--output",
                str(base_dir / "artifacts" / "validation" / "validate.json"),
            )

            self.assertTrue((base_dir / "artifacts" / "trending" / "current.json").exists())
            self.assertTrue((base_dir / "artifacts" / "images" / "image_analysis.json").exists())
            self.assertTrue((base_dir / "artifacts" / "validation" / "image_plan.json").exists())
            self.assertTrue((base_dir / "artifacts" / "validation" / "draft_requirements.md").exists())
            self.assertTrue((base_dir / "artifacts" / "validation" / "release.json").exists())
            self.assertTrue((base_dir / "artifacts" / "validation" / "validate.json").exists())


if __name__ == "__main__":
    unittest.main()
