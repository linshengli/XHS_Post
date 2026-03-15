# Structure SOP

## Goal

把项目目录从“配置、状态、产物混放”逐步推进到更明确的结构：
- `config/` 只放静态配置
- `state/` 放运行态
- `artifacts/` 放分析快照、图片分析、验证报告
- `xhs_post/` 作为唯一主实现层

## Method

每轮都按同一套 SOP 执行：

1. Analysis
   - 确认当前边界问题和本轮最小切片
2. Research
   - 确认现有代码入口、依赖路径和兼容面
3. Plan
   - 定义只影响一小块的变更
4. Task Breakdown
   - 拆成 1-3 个可验证动作
5. Implement
   - 落代码
   - 做最小验证
   - 记录结果

## Constraints

- 先兼容旧路径，再切默认路径
- 优先改共享 helper，不在脚本里散落新路径逻辑
- 每轮只推进一个明确切片
