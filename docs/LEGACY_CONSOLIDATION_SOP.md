# Legacy Consolidation SOP

## Goal

把 `engines/` 和 `generators/` 从“主实现层”降级为“兼容层”，让真正的实现统一回收至 `xhs_post/`。

## Method

每轮都按以下步骤执行：

1. Analysis
   - 识别一个遗留模块的真实调用面
2. Research
   - 找到 `xhs_post/` 中已存在的等价能力
3. Plan
   - 设计最小兼容 facade
4. Task Breakdown
   - 拆成 1-3 个不破坏 CLI 的动作
5. Implement
   - 迁移实现
   - 保留旧类名 / 旧入口
   - 增加兼容测试

## Constraints

- 优先保留旧 API 名称
- 不再向 `engines/` 和 `generators/` 添加新的核心逻辑
- 新逻辑必须放在 `xhs_post/`
