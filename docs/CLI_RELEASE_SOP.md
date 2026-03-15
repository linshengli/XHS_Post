# CLI and Release SOP

## Goal

给项目增加一个统一 CLI，并把“分析 -> 生成 -> 验证”串成标准 release candidate workflow。

## Method

1. Analysis
   - 找出分散脚本的重复参数和调用链
2. Research
   - 确认现有 workflow 能直接复用哪些部分
3. Plan
   - 先做最小可跑的统一 CLI
4. Task Breakdown
   - 子命令
   - workflow request model
   - release candidate orchestration
   - 测试
5. Implement
   - 入口统一
   - 保留旧脚本兼容

## Constraints

- 优先复用 `xhs_post.workflows`
- 不破坏现有独立脚本
- 先覆盖单账号 / LLM / validate / release-candidate 主链
