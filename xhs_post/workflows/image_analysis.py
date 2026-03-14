from __future__ import annotations

from xhs_post.images import build_image_analysis, discover_image_files
from xhs_post.models import ImageWorkflowRequest
from xhs_post.storage import save_json


def run_image_analysis_workflow(request: ImageWorkflowRequest) -> dict:
    image_files = discover_image_files(request.images_dir)
    analysis = build_image_analysis(image_files, request.topic)
    save_json(request.output_path, analysis)
    return analysis
