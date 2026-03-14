from __future__ import annotations

from datetime import datetime
from typing import Any

from xhs_post.models import ValidationWorkflowRequest
from xhs_post.storage import save_json
from xhs_post.validation.parser import discover_posts, load_post
from xhs_post.validation.scoring import (
    calculate_total_score,
    check_body_quality,
    check_originality,
    check_tags_quality,
    check_title_quality,
)


def run_validation_workflow(request: ValidationWorkflowRequest) -> dict[str, Any]:
    post_files = discover_posts(request.input_dir, request.pattern)
    posts = [load_post(file_path) for file_path in post_files]
    originality_results = check_originality(posts)

    results = []
    for index, post in enumerate(posts):
        selected_title = post["titles"][0] if post["titles"] else ""
        title_score = check_title_quality(selected_title)
        body_score = check_body_quality(post["body"])
        tags_score = check_tags_quality(post["tags"])
        total_score = calculate_total_score(title_score, body_score, tags_score)
        results.append(
            {
                "filename": post["filename"],
                "selected_title": selected_title,
                "all_titles": post["titles"],
                "tags": post["tags"],
                "title_score": title_score,
                "body_score": body_score,
                "tags_score": tags_score,
                "total_score": total_score,
                "originality": originality_results[index],
            }
        )

    high_dup_count = sum(1 for result in originality_results if result["high_similarity_with"])
    report = {
        "report_date": datetime.now().isoformat(),
        "total_posts": len(posts),
        "summary": {
            "avg_score": round(sum(result["total_score"]["percentage"] for result in results) / len(results), 1) if results else 0.0,
            "grade_distribution": {},
            "high_dup_count": high_dup_count,
        },
        "posts": results,
    }
    for result in results:
        grade = result["total_score"]["grade"]
        report["summary"]["grade_distribution"][grade] = report["summary"]["grade_distribution"].get(grade, 0) + 1

    save_json(request.output_path, report)
    return report
