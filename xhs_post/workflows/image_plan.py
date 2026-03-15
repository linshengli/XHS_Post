from __future__ import annotations

from typing import Any

from xhs_post.images import load_image_analysis, select_images_for_post
from xhs_post.models import ImagePlanWorkflowRequest
from xhs_post.storage import save_json


def run_image_plan_workflow(request: ImagePlanWorkflowRequest) -> dict[str, Any]:
    image_analyses = load_image_analysis(request.image_analysis_path)
    selected_images, combination_id = select_images_for_post(
        topic=request.topic,
        angle=request.angle,
        image_analyses=image_analyses,
        count=request.count,
    )
    plan = {
        "topic": request.topic,
        "angle": request.angle,
        "selected_images": selected_images,
        "combination_id": combination_id,
        "total_selected": len(selected_images),
    }
    save_json(request.output_path, plan)
    return plan
