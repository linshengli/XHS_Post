from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from xhs_post.paths import ensure_runtime_layout
from xhs_post.storage import mirror_json_to_legacy, seed_file_from_legacy


class RuntimeLayoutTests(unittest.TestCase):
    def test_ensure_runtime_layout_creates_state_and_artifacts_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = ensure_runtime_layout(Path(tmpdir))
            self.assertTrue(paths["state"].exists())
            self.assertTrue(paths["artifacts"].exists())
            self.assertTrue(paths["trending"].parent.exists())
            self.assertTrue(paths["images"].parent.exists())

    def test_seed_and_mirror_legacy_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            legacy = base / "config" / "generation_state.json"
            target = base / "state" / "generation_state.json"
            legacy.parent.mkdir(parents=True, exist_ok=True)
            legacy.write_text(json.dumps({"hello": "world"}, ensure_ascii=False), encoding="utf-8")

            seed_file_from_legacy(target, legacy, default_data={"fallback": True})
            self.assertEqual(json.loads(target.read_text(encoding="utf-8"))["hello"], "world")

            target.write_text(json.dumps({"synced": True}, ensure_ascii=False), encoding="utf-8")
            mirror_json_to_legacy(target, legacy)
            self.assertTrue(json.loads(legacy.read_text(encoding="utf-8"))["synced"])


if __name__ == "__main__":
    unittest.main()
