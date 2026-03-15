# Legacy Consolidation Rounds

## Round 1
- Analysis: 旧模块仍然存在实际代码，不只是空壳。
- Research: `engines/*` 与 `generators/*` 只有极少引用。
- Plan: 先以兼容 facade 收口，而不是直接删除。
- Implemented: 确认收口范围为热点匹配、人设约束、多账号生成。

## Round 2
- Analysis: 缺少结构化迁移记录。
- Research: 之前的结构改造已有 SOP 文档模式。
- Plan: 为 legacy consolidation 建立独立 SOP。
- Implemented: 新增 `docs/LEGACY_CONSOLIDATION_SOP.md` 和本轮记录文档。

## Round 3
- Analysis: 热点匹配逻辑在旧引擎里仍是独立实现。
- Research: 新版匹配能力已存在于 `xhs_post.workflows.multi_account`。
- Plan: 提炼共享 matching helper。
- Implemented: 新增 `xhs_post/matching.py`。

## Round 4
- Analysis: 旧热点匹配引擎应退化为兼容层。
- Research: 旧类名 `HotTopicPersonaMatcher` 仍有兼容价值。
- Plan: 保留旧类名，内部改用 `xhs_post`。
- Implemented: 重写 `engines/hot_topic_matcher.py` 为 facade。

## Round 5
- Analysis: 旧约束引擎仍然承载主逻辑。
- Research: 约束检查可迁入 `xhs_post.validation`。
- Plan: 把人设约束实现移到新版 validation 模块。
- Implemented: 新增 `xhs_post/validation/persona_constraints.py`。

## Round 6
- Analysis: 旧约束引擎只需保留兼容入口。
- Research: 旧类名 `PersonaConstraintEngine` 被 generator 使用。
- Plan: 让旧类继承新版 service。
- Implemented: 重写 `engines/constraint_engine.py` 为兼容壳。

## Round 7
- Analysis: 旧多账号生成器仍有一整套独立逻辑。
- Research: 需要接到新版 LLM 和 persona loader。
- Plan: 把 generator 降级为 facade。
- Implemented: 重写 `generators/multi_account_generator.py` 为兼容 facade。

## Round 8
- Analysis: facade 需要保证 `calculate_persona_match()` 不偏离传入 persona。
- Research: 初版 facade 还存在取第一个匹配结果的问题。
- Plan: 针对单 persona 做精确匹配。
- Implemented: 修正 `engines/hot_topic_matcher.py` 的单 persona 路径。

## Round 9
- Analysis: 结构迁移需要兼容测试锁住旧 API。
- Research: 当前仓库缺少 legacy 兼容测试。
- Plan: 增加旧引擎/旧生成器兼容测试。
- Implemented: 新增 `tests/test_legacy_compat.py`。

## Round 10
- Analysis: 需要集中验证 facade 是否可用。
- Research: 至少需要 `py_compile` + unittest。
- Plan: 补测试、验证、提交。
- Implemented: 已完成 `py_compile`、legacy unittest、existing unittest 回归验证。
