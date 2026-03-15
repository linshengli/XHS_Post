from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from engines.constraint_engine import PersonaConstraintEngine
from engines.hot_topic_matcher import HotTopicPersonaMatcher
from generators.multi_account_generator import MultiAccountContentGenerator


REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = REPO_ROOT / "config"


class LegacyCompatTests(unittest.TestCase):
    def test_hot_topic_matcher_facade(self) -> None:
        matcher = HotTopicPersonaMatcher(config_dir=str(CONFIG_DIR))
        matches = matcher.match_topic_to_personas("千岛湖亲子酒店", ["personas/account_001_qiandaohe_guide.yaml"])
        self.assertTrue(matches)
        self.assertEqual(matches[0]["topic"], "千岛湖亲子酒店")

    def test_constraint_engine_facade(self) -> None:
        engine = PersonaConstraintEngine(config_dir=str(CONFIG_DIR))
        persona = engine.load_persona("personas/account_001_qiandaohe_guide.yaml")
        result = engine.check_content("千岛湖旅游攻略，记得点赞收藏。", persona)
        self.assertIn("passed", result)
        self.assertIn("overall_score", result)

    def test_multi_account_generator_facade(self) -> None:
        generator = MultiAccountContentGenerator(config_dir=str(CONFIG_DIR))
        result = generator.generate_content(
            topic="千岛湖旅游攻略",
            persona_file="personas/account_001_qiandaohe_guide.yaml",
            angle="经验分享",
        )
        self.assertIn("title", result)
        self.assertIn("constraint_result", result)
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = generator.save_content(result, tmpdir)
            self.assertTrue(Path(output_file).exists())


if __name__ == "__main__":
    unittest.main()
