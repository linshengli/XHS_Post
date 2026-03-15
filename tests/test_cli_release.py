from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _write_repo(base_dir: Path) -> None:
    (base_dir / "config").mkdir(parents=True, exist_ok=True)
    (base_dir / "xhs_post_from_search" / "jsonl").mkdir(parents=True, exist_ok=True)
    fixture = REPO_ROOT / "tests" / "fixtures" / "search_contents_sample.jsonl"
    (base_dir / "xhs_post_from_search" / "jsonl" / fixture.name).write_text(
        fixture.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (base_dir / "config" / "generation_state.json").write_text(
        json.dumps({"used_combinations": [], "daily_history": [], "total_posts_generated": 0, "last_generation": {}}, ensure_ascii=False),
        encoding="utf-8",
    )


class CLIReleaseTests(unittest.TestCase):
    def test_release_candidate_cli_with_llm_mock(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            _write_repo(base_dir)
            output_dir = base_dir / "generated_posts" / "release"
            validation_output = base_dir / "artifacts" / "validation" / "release_candidate.json"
            env = os.environ | {"XHS_POST_BASE_DIR": str(base_dir), "XHS_POST_LLM_PROVIDER": "mock"}

            subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / "scripts" / "xhs_cli.py"),
                    "release-candidate",
                    "--topic",
                    "千岛湖亲子酒店",
                    "--count",
                    "1",
                    "--use-llm",
                    "--provider",
                    "mock",
                    "--output-dir",
                    str(output_dir),
                    "--validation-output",
                    str(validation_output),
                ],
                cwd=REPO_ROOT,
                env=env,
                text=True,
                capture_output=True,
                check=True,
            )

            self.assertEqual(len(list(output_dir.glob("*.md"))), 1)
            self.assertTrue(validation_output.exists())


if __name__ == "__main__":
    unittest.main()
