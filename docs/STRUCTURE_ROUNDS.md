# Structure Rounds

## Round 1
- Analysis: 目录边界模糊，缺少统一路径协议。
- Research: `scripts/*` 和 `xhs_post/*` 各自拼路径。
- Plan: 先补共享路径 helper。
- Implemented: 扩展 `xhs_post.paths`，增加 `config/state/artifacts` 目录解析。

## Round 2
- Analysis: 需要把结构优化和代码状态对齐到文档。
- Research: 现有 TODO 偏旧，缺少结构专项 SOP。
- Plan: 新增结构化 SOP 文档。
- Implemented: 新增 `docs/STRUCTURE_SOP.md` 和本轮记录文档。

## Round 3
- Analysis: LLM workflow 仍默认依赖 `config/` 下的运行态。
- Research: `generate_posts_llm.py` 直接读取旧路径。
- Plan: 接入新的 `state/` 和 `artifacts/trending/` helper，并兼容旧文件。
- Implemented: `generate_posts_llm.py` 改为优先使用 `state/` 与 `artifacts/`。

## Round 4
- Analysis: 热点分析结果仍写进 `config/trending_analysis.json`。
- Research: 下游脚本主要依赖默认文件名。
- Plan: 新默认写入 `artifacts/trending/current.json`，同时镜像旧路径。
- Implemented: `02_analyze_trending.py` 已写入 `artifacts/trending/` 并保留旧路径兼容。

## Round 5
- Analysis: 图片分析结果仍写进 `config/image_analysis.json`。
- Research: 生成脚本仍会消费旧文件名。
- Plan: 新默认写入 `artifacts/images/image_analysis.json`，同时镜像旧路径。
- Implemented: `01_analyze_images.py` 已切到 `artifacts/images/`。

## Round 6
- Analysis: 质量报告默认写到输入目录内，和产物混放。
- Research: 验证 workflow 本身已经支持自定义输出。
- Plan: 将默认报告路径切到 `artifacts/validation/`。
- Implemented: `04_validate_and_score.py` 已默认写入 `artifacts/validation/`。

## Round 7
- Analysis: 酒店优化报告和优化内容混在同一输出目录。
- Research: workflow 只支持固定输出到 `output_dir/optimization_report.json`。
- Plan: 给 workflow 增加 `report_path`，将报告独立到 `artifacts/validation/`。
- Implemented: `models.py`、`hotel_optimization.py`、`05_optimize_hotel_insertion.py` 已完成对齐。

## Round 8
- Analysis: 旧 `config/*` 运行态不能自动迁到新目录。
- Research: 多个入口都需要同样的兼容逻辑。
- Plan: 增加共享迁移 helper 和一个同步脚本。
- Implemented: 扩展 `storage.py` 的 seed/mirror helper，并新增 `07_sync_runtime_layout.py`。

## Round 9
- Analysis: 传统生成脚本仍然绑定旧路径。
- Research: `03_generate_posts.py` 只需要改常量和启动时 seed，不用碰生成逻辑。
- Plan: 将传统生成入口接入新路径 helper。
- Implemented: `03_generate_posts.py` 已优先使用 `state/` 与 `artifacts/`。

## Round 10
- Analysis: 结构层改动涉及多入口，需要集中验证。
- Research: 需要 helper 单测 + 脚本 smoke。
- Plan: 补 runtime layout 测试并跑一条新旧路径兼容 smoke。
- Implemented: 新增 `tests/test_runtime_layout.py`，并验证 `state/`、`artifacts/` 与旧 `config/*` 镜像同时生效。
