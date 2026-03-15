from __future__ import annotations

import json
import os
import random
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


class LLMError(RuntimeError):
    pass


def _load_openclaw_config() -> dict[str, Any]:
    """从 OpenClaw 配置文件中读取 API 配置"""
    config_path = Path.home() / ".openclaw" / "openclaw.json"
    if not config_path.exists():
        return {}
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        providers = config.get("models", {}).get("providers", {})
        bailian = providers.get("bailian", {})
        
        return {
            "api_key": bailian.get("apiKey"),
            "base_url": bailian.get("baseUrl"),
            "models": [m.get("id") for m in bailian.get("models", [])],
        }
    except (json.JSONDecodeError, KeyError):
        return {}


def _get_bailian_api_key() -> str | None:
    """获取 Bailian API key（优先环境变量，其次 OpenClaw 配置）"""
    # 优先使用环境变量
    api_key = os.environ.get("BAILIAN_API_KEY") or os.environ.get("DASHSCOPE_API_KEY")
    if api_key:
        return api_key
    
    # 从 OpenClaw 配置读取
    openclaw_config = _load_openclaw_config()
    return openclaw_config.get("api_key")


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


def _anthropic_style_request(base_url: str, api_key: str, model: str, prompt: str) -> dict[str, Any]:
    """支持 Anthropic 兼容的 API（如 Bailian Anthropic 代理）"""
    payload = {
        "model": model,
        "max_tokens": 2000,
        "system": "你是小红书图文笔记写作助手。请直接返回 JSON 格式的内容，包含 title、content、tags 三个字段。",
        "messages": [{"role": "user", "content": prompt}],
    }
    data = _post_json(
        f"{base_url.rstrip('/')}/messages",
        {"x-api-key": api_key, "anthropic-version": "2023-06-01"},
        payload,
    )
    content_blocks = data.get("content", [])
    if not content_blocks:
        raise LLMError("Anthropic-style response missing content")
    return _extract_json_payload(content_blocks[0]["text"])


def _smart_llm_request(base_url: str, api_key: str, model: str, prompt: str) -> dict[str, Any]:
    """根据 base_url 自动选择 API 格式"""
    # 如果 base_url 包含 "anthropic"，使用 Anthropic 兼容格式
    if "anthropic" in base_url.lower():
        return _anthropic_style_request(base_url, api_key, model, prompt)
    # 否则使用 OpenAI 兼容格式
    return _openai_compatible_request(base_url, api_key, model, prompt)


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


def _openclaw_cli_request(prompt: str, model: str = "bailian/qwen3.5-plus") -> dict[str, Any]:
    """通过 OpenClaw CLI 调用 LLM"""
    import subprocess
    
    # 构建提示词，明确要求返回纯 JSON
    enhanced_prompt = f"""{prompt}

重要：请直接返回 JSON 对象，不要使用 markdown 代码块包裹。"""
    
    try:
        result = subprocess.run(
            ["openclaw", "agent", "--agent", "main", "--message", enhanced_prompt, "--local"],
            capture_output=True,
            text=True,
            timeout=180,  # 增加到 3 分钟
        )
        
        if result.returncode != 0:
            raise LLMError(f"OpenClaw CLI failed: {result.stderr}")
        
        # 提取输出内容（跳过配置警告）
        output_lines = result.stdout.strip().split('\n')
        content_lines = []
        for line in output_lines:
            # 跳过配置警告和调试信息
            if any(skip in line for skip in ['Config', '\x1b[', '[plugins]', '[33m', '[31m', '[35m', '[39m']):
                continue
            if line.strip():
                content_lines.append(line)
        
        content = '\n'.join(content_lines)
        
        # 尝试解析 JSON
        try:
            return _extract_json_payload(content)
        except:
            pass
        
        # 如果不是 JSON，构建一个结构化响应
        topic = "主题"
        angle = "经验分享"
        for line in prompt.splitlines():
            if line.startswith("主题："):
                topic = line.replace("主题：", "").strip()
            if line.startswith("角度："):
                angle = line.replace("角度：", "").strip()
        
        # 清理内容，移除 markdown 代码块标记
        clean_content = content.replace('```json', '').replace('```', '').strip()
        
        # 尝试再次解析
        try:
            return _extract_json_payload(clean_content)
        except:
            pass
        
        # 最后使用内容作为正文
        lines = [l.strip() for l in clean_content.split('\n') if l.strip()]
        title = lines[0][:50] if lines else f"{topic}｜{angle}"
        
        return {
            "title": title,
            "content": clean_content,
            "tags": [f"#{topic.replace(' ', '')}", f"#{angle.replace(' ', '')}", "#小红书图文"],
        }
        
    except subprocess.TimeoutExpired:
        raise LLMError("OpenClaw CLI timeout")
    except FileNotFoundError:
        raise LLMError("OpenClaw CLI not found")


def generate_structured_post(prompt: str, provider: str | None = None) -> dict[str, Any]:
    provider_name = (provider or os.environ.get("XHS_POST_LLM_PROVIDER") or "openclaw").lower()  # 默认使用 openclaw

    try:
        if provider_name == "mock":
            return _mock_response(prompt)
        if provider_name == "openclaw":
            # 使用 OpenClaw CLI 调用（推荐方式）
            return _openclaw_cli_request(prompt)
        if provider_name == "openai":
            api_key = os.environ["OPENAI_API_KEY"]
            model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
            base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
            return _openai_compatible_request(base_url, api_key, model, prompt)
        if provider_name in {"qwen", "dashscope", "tongyi", "bailian"}:
            # 优先使用 OpenClaw CLI
            return _openclaw_cli_request(prompt)
        if provider_name == "anthropic":
            api_key = os.environ["ANTHROPIC_API_KEY"]
            model = os.environ.get("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest")
            return _anthropic_request(api_key, model, prompt)
    except KeyError as exc:
        raise LLMError(f"Missing API key for provider: {provider_name}") from exc
    except (urllib.error.URLError, json.JSONDecodeError) as exc:
        raise LLMError(f"LLM request failed for provider: {provider_name}") from exc

    raise LLMError(f"Unsupported provider: {provider_name}")
