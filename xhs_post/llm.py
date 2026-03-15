from __future__ import annotations

import json
import os
import random
import urllib.error
import urllib.request
from typing import Any


class LLMError(RuntimeError):
    pass


def _extract_json_payload(content: str) -> dict[str, Any]:
    text = content.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if len(lines) >= 3 and lines[0].startswith("```") and lines[-1].strip() == "```":
            text = "\n".join(lines[1:-1]).strip()
            if text.lower().startswith("json"):
                text = text[4:].strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        return json.loads(text[start : end + 1])


def _post_json(url: str, headers: dict[str, str], payload: dict[str, Any]) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={**headers, "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def _mock_response(prompt: str) -> dict[str, Any]:
    angle = "经验分享"
    topic = "主题"
    for line in prompt.splitlines():
        if line.startswith("主题："):
            topic = line.replace("主题：", "").strip()
        if line.startswith("角度："):
            angle = line.replace("角度：", "").strip()
    seed = sum(ord(char) for char in topic + angle)
    random.seed(seed)
    return {
        "title": f"{topic}｜{angle}，这篇直接抄作业",
        "content": f"这篇围绕 {topic} 的 {angle} 展开。\n\n先说结论：把路线、住宿和带娃节奏拆开看，行程就会轻松很多。\n\n我会优先看真实体验、场景适配和时间成本，而不是只看营销词。\n\n如果你也准备去，建议先收藏，再按自己的节奏微调。",
        "tags": [f"#{topic.replace(' ', '')}", f"#{angle.replace(' ', '')}", "#小红书图文", "#出行攻略", "#真实体验"],
    }


def _openai_compatible_request(base_url: str, api_key: str, model: str, prompt: str) -> dict[str, Any]:
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "你是小红书图文笔记写作助手，请返回 JSON。"},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
    }
    data = _post_json(
        f"{base_url.rstrip('/')}/chat/completions",
        {"Authorization": f"Bearer {api_key}"},
        payload,
    )
    content = data["choices"][0]["message"]["content"]
    return _extract_json_payload(content)


def _anthropic_request(api_key: str, model: str, prompt: str) -> dict[str, Any]:
    payload = {
        "model": model,
        "max_tokens": 1200,
        "system": "你是小红书图文笔记写作助手，请返回 JSON。",
        "messages": [{"role": "user", "content": prompt}],
    }
    data = _post_json(
        "https://api.anthropic.com/v1/messages",
        {"x-api-key": api_key, "anthropic-version": "2023-06-01"},
        payload,
    )
    content_blocks = data.get("content", [])
    if not content_blocks:
        raise LLMError("Anthropic response missing content")
    return _extract_json_payload(content_blocks[0]["text"])


def generate_structured_post(prompt: str, provider: str | None = None) -> dict[str, Any]:
    provider_name = (provider or os.environ.get("XHS_POST_LLM_PROVIDER") or "mock").lower()

    try:
        if provider_name == "mock":
            return _mock_response(prompt)
        if provider_name == "openai":
            api_key = os.environ["OPENAI_API_KEY"]
            model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
            base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
            return _openai_compatible_request(base_url, api_key, model, prompt)
        if provider_name in {"qwen", "dashscope", "tongyi"}:
            api_key = os.environ.get("BAILIAN_API_KEY") or os.environ["DASHSCOPE_API_KEY"]
            model = os.environ.get("QWEN_MODEL", "qwen3.5-plus")
            base_url = os.environ.get("BAILIAN_BASE_URL") or os.environ.get(
                "QWEN_BASE_URL",
                "https://dashscope.aliyuncs.com/compatible-mode/v1",
            )
            return _openai_compatible_request(base_url, api_key, model, prompt)
        if provider_name == "anthropic":
            api_key = os.environ["ANTHROPIC_API_KEY"]
            model = os.environ.get("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest")
            return _anthropic_request(api_key, model, prompt)
    except KeyError as exc:
        raise LLMError(f"Missing API key for provider: {provider_name}") from exc
    except (urllib.error.URLError, json.JSONDecodeError) as exc:
        raise LLMError(f"LLM request failed for provider: {provider_name}") from exc

    raise LLMError(f"Unsupported provider: {provider_name}")
