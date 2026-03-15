from __future__ import annotations

import json
import os
import random
import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_TIMEOUT_SECONDS = 60
DEFAULT_RETRIES = 2
DEFAULT_OPENCLAW_MODEL = "bailian/qwen3.5-plus"


class LLMError(RuntimeError):
    pass


@dataclass(slots=True)
class ProviderSettings:
    provider: str
    model: str
    timeout_seconds: int
    retries: int
    base_url: str | None = None
    api_key: str | None = None


def _env_int(name: str, default: int) -> int:
    value = os.environ.get(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise LLMError(f"Invalid integer for {name}: {value}") from exc


def _load_openclaw_config() -> dict[str, Any]:
    config_path = Path.home() / ".openclaw" / "openclaw.json"
    if not config_path.exists():
        return {}
    try:
        return json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _extract_bailian_config() -> dict[str, Any]:
    config = _load_openclaw_config()
    providers = config.get("models", {}).get("providers", {})
    bailian = providers.get("bailian", {})
    return {
        "api_key": bailian.get("apiKey"),
        "base_url": bailian.get("baseUrl"),
    }


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


def _normalize_tags(raw_tags: Any) -> list[str]:
    if isinstance(raw_tags, str):
        candidates = raw_tags.replace(",", " ").split()
    elif isinstance(raw_tags, list):
        candidates = [str(item).strip() for item in raw_tags if str(item).strip()]
    else:
        candidates = []

    normalized: list[str] = []
    for tag in candidates:
        if not tag:
            continue
        normalized.append(tag if tag.startswith("#") else f"#{tag}")
    return normalized[:8]


def _validate_post_payload(payload: dict[str, Any]) -> dict[str, Any]:
    title = str(payload.get("title", "")).strip()
    content = str(payload.get("content", "")).strip()
    tags = _normalize_tags(payload.get("tags"))
    if not title:
        raise LLMError("LLM response missing title")
    if not content:
        raise LLMError("LLM response missing content")
    if not tags:
        raise LLMError("LLM response missing tags")
    return {"title": title, "content": content, "tags": tags}


def _post_json(
    url: str,
    headers: dict[str, str],
    payload: dict[str, Any],
    *,
    timeout_seconds: int,
) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={**headers, "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
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
    openings = [
        f"先说核心判断：{topic} 这类内容，最怕信息堆太满，读者反而抓不到重点。",
        f"如果你是第一次做 {topic}，最有效的方式不是抄全攻略，而是先锁定 {angle} 这个切口。",
        f"我这次重新拆了下 {topic} 的内容结构，发现真正影响体验的不是景点多少，而是 {angle} 的信息顺序。",
    ]
    focus_points = [
        "我会优先看真实体验、场景适配和时间成本。",
        "我会先筛掉营销感太重的信息，再保留真正能落地的细节。",
        "我更关注决策顺序、节奏安排和容易踩坑的环节。",
    ]
    close_lines = [
        "如果你也准备去，建议先收藏，再按自己的节奏微调。",
        "这类内容不用一次看完，先把最适合自己的部分抄走就够了。",
        "先把这一版跑通，再补细节，体验通常会稳定很多。",
    ]
    return {
        "title": f"{topic}｜{angle}，这篇直接抄作业",
        "content": "\n\n".join(
            [
                f"这篇围绕 {topic} 的 {angle} 展开。",
                openings[seed % len(openings)],
                focus_points[(seed // 3) % len(focus_points)],
                f"具体写法上，我会把 {angle} 拆成 3 段：先给结论，再讲场景，最后补执行建议。",
                close_lines[(seed // 7) % len(close_lines)],
            ]
        ),
        "tags": [
            f"#{topic.replace(' ', '')}",
            f"#{angle.replace(' ', '')}",
            "#小红书图文",
            "#出行攻略",
            "#真实体验",
        ],
    }


def _openai_compatible_request(settings: ProviderSettings, prompt: str) -> dict[str, Any]:
    if not settings.base_url or not settings.api_key:
        raise LLMError(f"Provider {settings.provider} missing base_url or api_key")
    payload = {
        "model": settings.model,
        "messages": [
            {"role": "system", "content": "你是小红书图文笔记写作助手。请只返回 JSON，包含 title、content、tags。"},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
        "response_format": {"type": "json_object"},
    }
    data = _post_json(
        f"{settings.base_url.rstrip('/')}/chat/completions",
        {"Authorization": f"Bearer {settings.api_key}"},
        payload,
        timeout_seconds=settings.timeout_seconds,
    )
    content = data["choices"][0]["message"]["content"]
    return _extract_json_payload(content)


def _anthropic_request(settings: ProviderSettings, prompt: str) -> dict[str, Any]:
    if not settings.api_key:
        raise LLMError("Anthropic provider missing api_key")
    payload = {
        "model": settings.model,
        "max_tokens": 1200,
        "system": "你是小红书图文笔记写作助手。请只返回 JSON，包含 title、content、tags。",
        "messages": [{"role": "user", "content": prompt}],
    }
    data = _post_json(
        "https://api.anthropic.com/v1/messages",
        {"x-api-key": settings.api_key, "anthropic-version": "2023-06-01"},
        payload,
        timeout_seconds=settings.timeout_seconds,
    )
    content_blocks = data.get("content", [])
    if not content_blocks:
        raise LLMError("Anthropic response missing content")
    return _extract_json_payload(content_blocks[0]["text"])


def _openclaw_cli_request(settings: ProviderSettings, prompt: str) -> dict[str, Any]:
    enhanced_prompt = (
        f"{prompt}\n\n"
        "重要：请直接返回 JSON 对象，不要使用 markdown 代码块包裹。"
    )
    try:
        result = subprocess.run(
            ["openclaw", "agent", "--agent", "main", "--message", enhanced_prompt, "--local"],
            capture_output=True,
            text=True,
            timeout=settings.timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise LLMError("OpenClaw CLI timeout") from exc
    except FileNotFoundError as exc:
        raise LLMError("OpenClaw CLI not found") from exc

    if result.returncode != 0:
        raise LLMError(f"OpenClaw CLI failed: {result.stderr.strip()}")

    output_lines = result.stdout.strip().splitlines()
    content_lines = []
    for line in output_lines:
        if any(skip in line for skip in ["Config", "\x1b[", "[plugins]", "[33m", "[31m", "[35m", "[39m"]):
            continue
        if line.strip():
            content_lines.append(line)
    content = "\n".join(content_lines)

    try:
        return _extract_json_payload(content)
    except json.JSONDecodeError:
        pass

    topic = "主题"
    angle = "经验分享"
    for line in prompt.splitlines():
        if line.startswith("主题："):
            topic = line.replace("主题：", "").strip()
        if line.startswith("角度："):
            angle = line.replace("角度：", "").strip()

    clean_content = content.replace("```json", "").replace("```", "").strip()
    return {
        "title": clean_content.splitlines()[0][:50] if clean_content else f"{topic}｜{angle}",
        "content": clean_content,
        "tags": [f"#{topic.replace(' ', '')}", f"#{angle.replace(' ', '')}", "#小红书图文"],
    }


def _resolve_requested_provider(provider: str | None) -> str:
    return (provider or os.environ.get("XHS_POST_LLM_PROVIDER") or "openclaw").lower()


def _resolve_fallback_providers(primary: str) -> list[str]:
    raw = os.environ.get("XHS_POST_LLM_FALLBACKS", "")
    providers = []
    for item in raw.split(","):
        candidate = item.strip().lower()
        if not candidate or candidate == primary or candidate in providers:
            continue
        providers.append(candidate)
    return providers


def _resolve_provider_settings(provider: str) -> ProviderSettings:
    timeout_seconds = _env_int("XHS_POST_LLM_TIMEOUT", DEFAULT_TIMEOUT_SECONDS)
    retries = _env_int("XHS_POST_LLM_RETRIES", DEFAULT_RETRIES)
    bailian = _extract_bailian_config()

    if provider == "mock":
        return ProviderSettings(provider=provider, model="mock", timeout_seconds=timeout_seconds, retries=0)
    if provider == "openclaw":
        return ProviderSettings(
            provider=provider,
            model=os.environ.get("OPENCLAW_MODEL", DEFAULT_OPENCLAW_MODEL),
            timeout_seconds=_env_int("XHS_POST_OPENCLAW_TIMEOUT", max(timeout_seconds, 120)),
            retries=retries,
        )
    if provider == "openai":
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise LLMError("Missing OPENAI_API_KEY")
        return ProviderSettings(
            provider=provider,
            model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
            base_url=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            api_key=api_key,
            timeout_seconds=timeout_seconds,
            retries=retries,
        )
    if provider in {"qwen", "dashscope", "tongyi", "bailian"}:
        api_key = os.environ.get("BAILIAN_API_KEY") or os.environ.get("DASHSCOPE_API_KEY") or bailian.get("api_key")
        if not api_key:
            raise LLMError("Missing BAILIAN_API_KEY or DASHSCOPE_API_KEY")
        return ProviderSettings(
            provider=provider,
            model=os.environ.get("QWEN_MODEL", "qwen3.5-plus"),
            base_url=os.environ.get("BAILIAN_BASE_URL")
            or os.environ.get("QWEN_BASE_URL")
            or bailian.get("base_url")
            or "https://dashscope.aliyuncs.com/compatible-mode/v1",
            api_key=api_key,
            timeout_seconds=timeout_seconds,
            retries=retries,
        )
    if provider == "anthropic":
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise LLMError("Missing ANTHROPIC_API_KEY")
        return ProviderSettings(
            provider=provider,
            model=os.environ.get("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest"),
            api_key=api_key,
            timeout_seconds=timeout_seconds,
            retries=retries,
        )
    raise LLMError(f"Unsupported provider: {provider}")


def _call_provider_once(settings: ProviderSettings, prompt: str) -> dict[str, Any]:
    if settings.provider == "mock":
        return _mock_response(prompt)
    if settings.provider == "openclaw":
        return _openclaw_cli_request(settings, prompt)
    if settings.provider == "openai":
        return _openai_compatible_request(settings, prompt)
    if settings.provider in {"qwen", "dashscope", "tongyi", "bailian"}:
        return _openai_compatible_request(settings, prompt)
    if settings.provider == "anthropic":
        return _anthropic_request(settings, prompt)
    raise LLMError(f"Unsupported provider: {settings.provider}")


def generate_structured_post(prompt: str, provider: str | None = None) -> dict[str, Any]:
    primary_provider = _resolve_requested_provider(provider)
    provider_order = [primary_provider, *_resolve_fallback_providers(primary_provider)]
    errors: list[str] = []

    for provider_name in provider_order:
        try:
            settings = _resolve_provider_settings(provider_name)
        except LLMError as exc:
            errors.append(f"{provider_name} config: {exc}")
            continue
        for attempt in range(settings.retries + 1):
            try:
                payload = _call_provider_once(settings, prompt)
                normalized = _validate_post_payload(payload)
                normalized["_provider"] = provider_name
                return normalized
            except (urllib.error.URLError, json.JSONDecodeError, KeyError, IndexError, LLMError) as exc:
                errors.append(f"{provider_name} attempt {attempt + 1}: {exc}")
                if attempt >= settings.retries:
                    break
                time.sleep(min(2**attempt, 3))

    raise LLMError("All providers failed: " + " | ".join(errors))
