from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from xhs_post.llm import LLMError, generate_structured_post


class LLMModuleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_env = dict(os.environ)

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_fallback_provider_is_used_when_primary_fails_config(self) -> None:
        os.environ["XHS_POST_LLM_FALLBACKS"] = "mock"
        os.environ.pop("OPENAI_API_KEY", None)

        result = generate_structured_post("主题：千岛湖旅游攻略\n角度：避坑指南", provider="openai")

        self.assertEqual(result["_provider"], "mock")
        self.assertIn("#千岛湖旅游攻略", result["tags"])

    def test_retry_succeeds_after_transient_error(self) -> None:
        os.environ["XHS_POST_LLM_RETRIES"] = "1"
        os.environ["OPENAI_API_KEY"] = "test-key"
        calls = {"count": 0}

        def flaky_response(settings, prompt: str) -> dict[str, object]:
            calls["count"] += 1
            if calls["count"] == 1:
                raise LLMError("temporary")
            return {"title": "标题", "content": "正文", "tags": ["话题A", "#话题B"]}

        with patch("xhs_post.llm._openai_compatible_request", side_effect=flaky_response):
            result = generate_structured_post("主题：千岛湖旅游攻略", provider="openai")

        self.assertEqual(calls["count"], 2)
        self.assertEqual(result["tags"], ["#话题A", "#话题B"])

    def test_invalid_payload_raises_after_retries(self) -> None:
        os.environ["XHS_POST_LLM_RETRIES"] = "0"
        with patch(
            "xhs_post.llm._mock_response",
            return_value={"title": "", "content": "正文", "tags": ["#标签"]},
        ):
            with self.assertRaises(LLMError):
                generate_structured_post("主题：千岛湖旅游攻略", provider="mock")


if __name__ == "__main__":
    unittest.main()
