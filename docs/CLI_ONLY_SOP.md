# CLI-Only SOP

## Goal

把 `xhs_cli` 变成唯一推荐入口，同时保留老脚本作为兼容 wrapper。

## Scope

CLI 需要覆盖：
- 热点分析
- 图像分析
- 图像方案优化 / 选图规划
- 生成 note
- 评分
- 验证 note
- 生成 draft requirements

## Method

1. Analysis
2. Research
3. Plan
4. Task Breakdown
5. Implement

## Constraints

- 不删旧脚本，但让它们退化为 wrapper
- CLI 逻辑放在 `xhs_post/cli.py`
- 必须有多阶段 CLI smoke test
