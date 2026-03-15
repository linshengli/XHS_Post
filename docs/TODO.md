# XHS_Post TODO

## Current State

已完成：
- [x] 公共 module 已建立：`xhs_post.topic`、`xhs_post.storage`、`xhs_post.images`
- [x] 基础 workflow 已建立：主题分析、单账号生成、多账号编排、图片分析、发布前验证、酒店植入优化
- [x] 真实 LLM provider 抽象已接入：OpenAI、Anthropic、Tongyi/Bailian
- [x] 图片方案已接入两条链路：本地图库分析 + 从爬取数据 `image_list` 提图
- [x] PR 前 CI 已覆盖基础 lint/test 框架与端到端样例

不再作为待办：
- [x] “LLM 未真正接入”
- [x] “图片仅是文字建议”
- [x] “多账号矩阵完全未实现”

## P0: Stabilize Production Path

- [ ] 用真实 secrets 跑通 OpenAI / Anthropic / Tongyi 的在线集成测试
- [ ] 为 LLM 请求补重试、超时分级、速率限制和 provider fallback
- [ ] 为 LLM 输出补更强的 JSON 兜底解析和字段校验
- [ ] 建立正文/标题相似度去重，替代目前只有图片组合去重的做法
- [ ] 为方案 A 的爬取图片补版权与来源治理策略
- [ ] 让多账号 workflow 也能消费真实 LLM 和真实图片分配，而不是只做静态编排

## P1: Normalize Data and Workflow Boundaries

- [ ] 清理 `.bak`、临时脚本、无归属入口，减少脚本层重复逻辑
- [ ] 把运行态文件从 `config/` 拆到 `state/` 或 `artifacts/`
- [ ] 统一分析快照、生成结果、验证报告的 metadata 结构
- [ ] 为 persona、分析快照、生成产物补 schema 校验
- [ ] 把散落脚本继续收敛到统一 CLI / workflow 入口
- [ ] 建立统一 `release_candidate` workflow，串联生成、验证、优化、再验证

## P1: Improve Matrix Operation

- [ ] 把 4 类账号的人设差异真正落实到标题、正文、标签、图片、发布时间
- [ ] 增加多账号差异化回归测试，防止不同账号内容趋同
- [ ] 对账号 registry 里的发布频率和内容角度做自动排期输出
- [ ] 给多账号生成增加账号级去重，而不是只在单篇维度去重

## P2: Automation and Feedback Loop

- [ ] 为热点抓取和生成流程补定时调度
- [ ] 生成发布排期表和人工发布 checklist，作为无官方 API 条件下的替代自动化
- [ ] 补发布后效果追踪：点赞、收藏、评论、发布时间、主题
- [ ] 基于历史表现反哺选题、角度和图片策略
- [ ] 扩大主题测试集，验证“亲子酒店 / 千岛湖 / 西双版纳”之外的通用性

## Deferred Evaluation

- [ ] 在 persona schema 稳定后评估引入 Pydantic
- [ ] 在 workflow 命令树稳定后评估引入 Typer
- [ ] 在 shell 流程稳定后评估迁移到 Python workflow runner
