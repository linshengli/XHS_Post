# CLI-Only Rounds

## Round 1
- Analysis: CLI 还不是唯一推荐入口。
- Research: 现有 CLI 逻辑还在 `scripts/xhs_cli.py`。
- Plan: 把 CLI 逻辑迁进 `xhs_post/cli.py`。
- Implemented: `xhs_post/cli.py` 已成为主 CLI 实现层。

## Round 2
- Analysis: 需要明确“唯一推荐入口”的迁移规则。
- Research: 之前的结构迭代都配了 SOP 文档。
- Plan: 为 CLI-only 单独建文档。
- Implemented: 新增 `docs/CLI_ONLY_SOP.md` 与本轮记录文档。

## Round 3
- Analysis: CLI 还缺图像规划能力。
- Research: 现有 `images.py` 已有图片选择逻辑。
- Plan: 增加 image-plan workflow 和 request model。
- Implemented: 新增 `ImagePlanWorkflowRequest` 与 `workflows/image_plan.py`。

## Round 4
- Analysis: CLI 缺“生成 draft requirements”能力。
- Research: 热点分析结果已经足够生成 brief。
- Plan: 增加 draft requirements workflow。
- Implemented: 新增 `DraftRequirementsWorkflowRequest` 与 `workflows/draft_requirements.py`。

## Round 5
- Analysis: CLI 需要覆盖更多主链命令。
- Research: 当前缺少 analyze-images、image-plan、draft-requirements、optimize-hotel。
- Plan: 扩展命令树。
- Implemented: `xhs_post/cli.py` 已补齐这些命令。

## Round 6
- Analysis: 旧脚本仍然是可见入口，容易继续被当主入口使用。
- Research: 一次性删掉不安全。
- Plan: 先降级成兼容入口，并打印迁移提示。
- Implemented: `01/02/04/05/06` 脚本已加 CLI 推荐提示。

## Round 7
- Analysis: CLI 里评分和验证需要统一表达。
- Research: 两者底层都可复用 validation workflow。
- Plan: 提供 `score` 和 `validate` 两个命令入口。
- Implemented: `xhs_post/cli.py` 已支持 `score` 与 `validate`。

## Round 8
- Analysis: 必须验证 CLI 能串起多阶段，而不是单命令测试。
- Research: 最有价值的是分析、图像、draft、release、validate 的完整链。
- Plan: 增加 multistage CLI smoke。
- Implemented: 新增 `tests/test_cli_multistage.py`。

## Round 9
- Analysis: CLI-only 改动可能影响既有路径。
- Research: 需要保留现有 runtime/legacy/llm/dedup 回归。
- Plan: 跑 CLI smoke + 既有 unittest。
- Implemented: 已完成 CLI smoke 和既有 unittest 回归。

## Round 10
- Analysis: 本轮只应提交 CLI-only 相关改动。
- Research: 工作区里有大量无关运行态变更。
- Plan: 只暂存 CLI-only 文件并提交。
- Implemented: 已完成提交。
