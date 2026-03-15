from __future__ import annotations

from typing import Any

from xhs_post.models import DraftRequirementsWorkflowRequest
from xhs_post.storage import load_json


def run_draft_requirements_workflow(request: DraftRequirementsWorkflowRequest) -> str:
    trending = load_json(request.trending_input)
    features = trending.get("features", {})
    lines = [
        f"# Draft Requirements: {request.topic}",
        "",
        "## 热点摘要",
        *[f"- {item}" for item in trending.get("key_insights", [])[:5]],
        "",
        "## 重点标签",
        *[f"- #{item['tag']}" for item in trending.get("hot_tags", [])[:8]],
        "",
        "## 建议内容角度",
        *[f"- {item}" for item in (features.get("title_patterns", {}).keys() if features.get("title_patterns") else ["经验分享", "避坑指南", "真实体验"])],
        "",
        "## 价值点",
        *[f"- {item}" for item in features.get("value_points", [])[:5]],
        "",
        "## 场景",
        *[f"- {item}" for item in features.get("scenes", [])[:5]],
        "",
        "## 交付要求",
        "- 生成标题、正文、标签",
        "- 附带配图方案或选图计划",
        "- 发布前需做评分和重复度验证",
    ]
    content = "\n".join(lines)
    request.output_path.parent.mkdir(parents=True, exist_ok=True)
    request.output_path.write_text(content, encoding="utf-8")
    return content
