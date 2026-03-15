from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from xhs_post.models import HotelOptimizationWorkflowRequest
from xhs_post.storage import save_json
from xhs_post.validation.hotel import find_matching_persona, load_persona_map, optimize_content


def run_hotel_optimization_workflow(request: HotelOptimizationWorkflowRequest) -> dict[str, Any]:
    personas = load_persona_map(request.personas_dir)
    request.output_dir.mkdir(parents=True, exist_ok=True)
    draft_files = sorted(request.input_dir.glob("*.md"))
    results: list[dict[str, Any]] = []

    for draft_file in draft_files:
        persona_config = find_matching_persona(draft_file.name, personas)
        if not persona_config:
            continue

        content = draft_file.read_text(encoding="utf-8")
        result = optimize_content(content, persona_config)
        output_file = request.output_dir / draft_file.name
        output_file.write_text(result["optimized_content"], encoding="utf-8")
        result["input_file"] = str(draft_file)
        result["output_file"] = str(output_file)
        results.append(result)

    report = {
        "processed_at": datetime.now().isoformat(),
        "total_files": len(results),
        "files_with_issues": sum(1 for result in results if result["issues"]),
        "files_optimized": sum(1 for result in results if result["optimizations"]),
        "results": results,
    }
    report_path = request.report_path or (request.output_dir / "optimization_report.json")
    save_json(report_path, report)
    return report
