# XHS_Post TODO

## Phase 1: Stabilize Boundaries

- [x] 提取公共路径解析层，避免脚本各自处理工作目录
- [x] 增加统一 workflow 入口，支持“分析 -> 生成”的标准执行
- [x] 为主题匹配、JSON/JSONL 读写建立公共 module
- [ ] 让 `02/03/03_multi` 全面改用公共 module，移除重复逻辑
- [ ] 清理 `.bak`、临时生成态、无归属脚本

## Phase 2: Normalize Domain Model

- [ ] 统一 persona schema，给通用账号和千岛湖专题账号建立兼容层
- [ ] 把运行态文件从 `config/` 拆到 `state/` 或 `artifacts/`
- [ ] 定义分析快照、生成结果、评分报告的统一 metadata 格式
- [ ] 为配置和快照补 schema 校验

## Phase 3: Formalize Validation

- [ ] 把质量评分、人设约束、酒店植入优化收敛为 `validation` 模块
- [ ] 给“可发布”建立统一门禁，不再依赖多个脚本各自打分
- [ ] 补全多账号差异化验证与回归用例

## Phase 4: CLI and Release Workflow

- [ ] 把散落脚本收敛到统一 CLI
- [ ] 建立 `generate-samples`、`validate-release`、`multi-account-run` 等标准命令
- [ ] 在 CI 中增加 workflow 级集成测试和样例产物校验

## Phase 5: Optional Upgrades

- [ ] 评估用 Pydantic 做 schema 校验
- [ ] 评估用 Typer 替换 `argparse` 做多子命令 CLI
- [ ] 评估把每日执行从 shell 迁到 Python workflow runner
