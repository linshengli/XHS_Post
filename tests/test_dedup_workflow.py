from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from xhs_post.dedup import build_content_signature, content_similarity, find_similar_signature
from xhs_post.models import LLMPostWorkflowRequest
from xhs_post.workflows.llm_post_generation import run_llm_post_generation_workflow


class DedupWorkflowTests(unittest.TestCase):
    def test_content_similarity_detects_near_duplicates(self) -> None:
        left = build_content_signature("千岛湖攻略", "路线安排轻松，适合第一次去。")
        right = build_content_signature("千岛湖攻略", "路线安排轻松，很适合第一次去。")

        self.assertGreaterEqual(content_similarity(left, right), 0.82)
        self.assertIsNotNone(find_similar_signature(left, [right], threshold=0.82))

    def test_llm_workflow_retries_when_candidate_is_too_similar(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            (base_dir / "config").mkdir(parents=True, exist_ok=True)
            (base_dir / "xhs_post_from_search" / "jsonl").mkdir(parents=True, exist_ok=True)
            (base_dir / "generated_posts" / "llm").mkdir(parents=True, exist_ok=True)

            (base_dir / "config" / "trending_analysis.json").write_text(
                json.dumps({"topic": "千岛湖旅游攻略", "features": {"tags": ["千岛湖"]}}, ensure_ascii=False),
                encoding="utf-8",
            )
            (base_dir / "config" / "generation_state.json").write_text(
                json.dumps(
                    {
                        "content_signatures": [
                            build_content_signature("旧标题", "重复正文"),
                        ]
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            (base_dir / "xhs_post_from_search" / "jsonl" / "sample.jsonl").write_text(
                '{"title":"样例","source_keyword":"千岛湖","image_list":"https://img.example.com/1.jpg"}\n',
                encoding="utf-8",
            )

            responses = iter(
                [
                    {"title": "旧标题", "content": "重复正文", "tags": ["千岛湖旅游攻略"], "_provider": "mock"},
                    {"title": "新标题", "content": "新的独特正文", "tags": ["千岛湖旅游攻略"], "_provider": "mock"},
                ]
            )

            with patch(
                "xhs_post.workflows.llm_post_generation.generate_structured_post",
                side_effect=lambda *args, **kwargs: next(responses),
            ):
                output_files = run_llm_post_generation_workflow(
                    LLMPostWorkflowRequest(
                        topic="千岛湖旅游攻略",
                        count=1,
                        trending_input=base_dir / "config" / "trending_analysis.json",
                        output_dir=base_dir / "generated_posts" / "llm",
                        raw_posts_dir=base_dir / "xhs_post_from_search" / "jsonl",
                        state_file=base_dir / "config" / "generation_state.json",
                        provider="mock",
                        similarity_threshold=0.82,
                        max_attempts_per_post=2,
                    )
                )

            self.assertEqual(len(output_files), 1)
            content = output_files[0].read_text(encoding="utf-8")
            self.assertIn("新标题", content)
            state = json.loads((base_dir / "config" / "generation_state.json").read_text(encoding="utf-8"))
            self.assertEqual(len(state["content_signatures"]), 2)


if __name__ == "__main__":
    unittest.main()
