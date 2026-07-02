# React 重构文档入口

本文档目录用于维护 MultiChatEval 的 React 前端重构资料。

当前边界：

- 保留原 `vue-frontend/` Vue 前端作为可运行基线。
- React 技术栈主前端位于 `frontend/`，不删除现有 Vue 基线。
- 复用现有 FastAPI API、MySQL 数据结构、认证权限模型、评分逻辑和模型级 NDJSON 渐进返回语义。
- 不借 React 重构继续开发 v2 已冻结的新功能，例如语义分析、模型推荐、运行监控、评论审核、导出和批量评测。

阶段一已完成：

- `frontend/` 使用 React 19、TypeScript、Vite、React Router 和 Vitest。
- React 前端已接入 `/api/health` 与 `/api/auth/me`，用于系统健康检查和登录态恢复。
- 新增 `scripts/start-react-local.sh`，可一键启动 MySQL、FastAPI 后端和 React 前端。

阶段二已完成：

- React 前端已接入登录、注册、退出和当前用户恢复。
- 已实现受保护业务路由、公开认证路由、基础业务布局和按角色导航。
- 管理员入口 `/models` 与 `/users` 已在前端隐藏并保护；页面内容仍是占位壳，具体业务迁移留到后续阶段。

阶段三核心工作台已完成：

- `/` 已迁移为 React 评测工作台，支持模型列表、今日 Token、公开/私有、思考模式、LLM 评审和模型级 NDJSON 渐进展示。
- 回答卡片支持 Markdown 安全渲染、`<think>` 折叠、评分详情和点赞/点踩反馈。
- 公开评论分页、发布和删除已随阶段四历史任务详情迁移。

阶段四已完成：

- `/history` 已迁移为 React 历史任务页面，支持分页、详情加载、状态标记、超时提示和公开/私有标记。
- 历史详情复用回答卡片，支持点赞/点踩、完整回答、评分详情和公开评论分页、发布、删除。
- `/models` 已迁移为管理员模型配置页面，支持配置列表、预设填充、新增、编辑、启用/禁用、删除和连接测试。
- `/users` 已迁移为管理员用户额度页面，支持查看用户今日 Token 用量并调整普通用户每日额度。
- `/feedback` 已迁移为反馈统计页面，普通用户查看个人统计，管理员查看全局模型表现、每日趋势和互动明细。

## 文档索引

- `plan.md`：React 重构阶段计划、迁移顺序和验收标准。
- `architecture.md`：React 前端架构草案、模块边界和数据流。

## 相关权威文档

- `../api.md`：后端接口说明，React 前端必须优先复用。
- `../database.md`：数据库结构说明，React 重构默认不修改。
- `../architecture.md`：当前系统架构和 Vue 基线说明。
- `../system-features-status.md`：当前已实现功能与 React 重构优先级。
- `../legacy-v2/`：v2 历史开发文档归档。
