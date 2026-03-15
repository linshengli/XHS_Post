from __future__ import annotations

import random
from datetime import datetime
from pathlib import Path
from typing import Any

from xhs_post.dedup import build_content_signature, find_similar_signature
from xhs_post.images import select_crawled_images_for_post
from xhs_post.llm import generate_structured_post
from xhs_post.models import LLMPostWorkflowRequest
from xhs_post.storage import load_json, load_jsonl_files, save_json
from xhs_post.topic import expand_keywords, filter_posts_by_source_keyword


def _build_prompt(topic: str, angle: str, features: dict[str, Any]) -> str:
    value_points = features.get("value_points", [])[:5]
    scenes = features.get("scenes", [])[:3]
    tags = features.get("tags", [])[:8]
    return "\n".join(
        [
            "请输出 JSON，包含 title, content, tags 三个字段。",
            f"主题：{topic}",
            f"角度：{angle}",
            f"价值点：{value_points}",
            f"场景：{scenes}",
            f"参考标签：{tags}",
            "要求：标题 20 字以内；正文适合小红书图文；tags 返回数组。",
        ]
    )


def _format_post_markdown(post: dict[str, Any]) -> str:
    lines = [
        "# 🔥 标题选项 (1 个)",
        f"1. {post['title']}",
        "",
        "## 🏷️ 推荐标签",
        " ".join(post["tags"]),
        "",
        "## 📸 配图",
    ]
    for index, image in enumerate(post["images"], 1):
        lines.append(f"{index}. [{image['role']}] {image['path']} ({image.get('theme', '未标注')})")
    lines.extend(
        [
            "",
            "## ✍️ 正文",
            "",
            post["content"],
            "",
            "## ⏰ 最佳发布时间",
            random.choice(["早上 7:30-9:00 (早高峰)", "中午 12:00-14:00 (午休)", "晚上 18:00-20:00 (晚高峰)"]),
            "",
            "---",
            f"*生成时间：{datetime.now().isoformat()}*",
            f"*主题：{post['topic']}*",
            f"*角度：{post['angle']}*",
            f"*Provider：{post['provider']}*",
        ]
    )
    return "\n".join(lines)


def run_llm_post_generation_workflow(request: LLMPostWorkflowRequest) -> list[Path]:
    if request.seed is not None:
        random.seed(request.seed)

    trending_data = load_json(request.trending_input)
    state = load_json(request.state_file) if request.state_file else {}
    content_signatures = list(state.get("content_signatures", []))
    raw_posts = filter_posts_by_source_keyword(load_jsonl_files(request.raw_posts_dir), request.topic)
    features = trending_data.get("features", {})
    angles = ["保姆级攻略", "避坑指南", "实测体验", "本地人推荐", "带娃攻略"]
    request.output_dir.mkdir(parents=True, exist_ok=True)

    output_files = []
    for index in range(1, request.count + 1):
        response: dict[str, Any] | None = None
        angle = angles[(index - 1) % len(angles)]
        for attempt in range(request.max_attempts_per_post):
            angle = angles[(index - 1 + attempt) % len(angles)]
            candidate = generate_structured_post(_build_prompt(request.topic, angle, features), provider=request.provider)
            signature = build_content_signature(candidate["title"], candidate["content"])
            duplicate = find_similar_signature(
                signature,
                content_signatures,
                threshold=request.similarity_threshold,
            )
            if duplicate:
                continue
            candidate["_signature"] = signature
            response = candidate
            break
        if response is None:
            raise RuntimeError(f"Failed to generate unique content for post {index}")

        tags = response.get("tags") or [f"#{keyword}" for keyword in expand_keywords(request.topic)[:5]]
        if isinstance(tags, str):
            tags = tags.split()
        images = select_crawled_images_for_post(raw_posts)
        content_signatures.append(response["_signature"])
        post = {
            "title": response["title"],
            "content": response["content"],
            "tags": tags,
            "images": images,
            "topic": request.topic,
            "angle": angle,
            "provider": response.get("_provider", request.provider or "unknown"),
        }
        output_file = request.output_dir / f"{request.topic}_{index:02d}.md"
        output_file.write_text(_format_post_markdown(post), encoding="utf-8")
        output_files.append(output_file)

    if request.state_file:
        state["content_signatures"] = content_signatures[-200:]
        state["last_generation"] = {
            "topic": request.topic,
            "count": len(output_files),
            "generated_at": datetime.now().isoformat(),
        }
        save_json(request.state_file, state)

    return output_files
