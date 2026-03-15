# CLI and Release Rounds

## Round 1
- Analysis: 入口脚本过多，调用链分散。
- Research: 现有 workflow 已能覆盖分析、生成、验证。
- Plan: 为 CLI/release 建立单独 SOP。
- Implemented: 新增 CLI/release SOP 文档。

## Round 2
- Analysis: release 主链缺少统一输入模型。
- Research: 现有 models 只覆盖单独 workflow。
- Plan: 增加 release candidate request model。
- Implemented: `models.py` 新增 `ReleaseCandidateWorkflowRequest`。

## Round 3
- Analysis: topic pipeline 默认分析输出仍偏旧。
- Research: 结构优化后应优先写入 `artifacts/trending`。
- Plan: 更新 topic pipeline 默认分析路径。
- Implemented: `topic_pipeline.py` 已默认写入 `artifacts/trending/`。

## Round 4
- Analysis: 缺少把分析、生成、验证串起来的标准 workflow。
- Research: 现有 analysis / llm / validation 能直接复用。
- Plan: 新增 release candidate orchestration。
- Implemented: 新增 `xhs_post/workflows/release_candidate.py`。

## Round 5
- Analysis: 入口脚本过多，不利于后续自动化。
- Research: `argparse` 足够承载一个统一子命令树。
- Plan: 新增统一 CLI 脚本。
- Implemented: 新增 `scripts/xhs_cli.py`。

## Round 6
- Analysis: CLI 需要先覆盖最常用的分析/传统生成入口。
- Research: 旧脚本仍可作为兼容底座。
- Plan: 先转调旧脚本，保留行为稳定。
- Implemented: `xhs_cli.py` 已接入 `analyze` 和 `generate`。

## Round 7
- Analysis: 统一 CLI 如果缺少 LLM/validate/release 主链，价值有限。
- Research: 这些链路已有 workflow 可直接调用。
- Plan: 直接接 workflow，不再套脚本。
- Implemented: `xhs_cli.py` 已接入 `llm-generate`、`validate`、`release-candidate`。

## Round 8
- Analysis: shell daily pipeline 仍维护自己的脚本拼装。
- Research: 单账号主链可以转调统一 CLI。
- Plan: 让 shell 入口在单账号模式下使用 `xhs_cli.py`。
- Implemented: `run_daily_pipeline.sh` 已接入统一 CLI。

## Round 9
- Analysis: 需要验证新 CLI 不是空壳。
- Research: 最有价值的是 `release-candidate --use-llm` 的 smoke。
- Plan: 增加 CLI release smoke 测试。
- Implemented: 新增 `tests/test_cli_release.py`。

## Round 10
- Analysis: 需要集中验证 CLI 和既有回归。
- Research: 至少要跑 py_compile + unified CLI unittest + existing unittests。
- Plan: 执行回归并提交。
- Implemented: 已完成 CLI smoke、legacy/runtime/llm/dedup 回归验证并提交。
