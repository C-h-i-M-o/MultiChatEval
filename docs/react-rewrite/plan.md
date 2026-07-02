# React 前端重构计划

最后更新：2026-07-03

## 目标

在保留现有 Vue 前端可运行的前提下，新建 React 技术栈前端，并逐步迁移当前已实现业务页面。重构目标是为面试和后续维护提供 React 工程证据链，不扩大后端功能范围。

## 非目标

- 不继续开发 v2 已冻结的新功能。
- 不重写后端 API、数据库结构、评分公式或权限模型。
- 不把模型级 NDJSON 渐进返回改成逐字 Token 流式输出。
- 不在迁移初期删除现有 Vue 前端。

## 阶段计划

### 阶段 1：React 工程初始化（已完成）

- 新建独立 React 前端目录。
- 明确包管理、构建命令、路由方案、状态管理、API 封装和样式方案。
- 接入基础登录态恢复、错误提示和开发代理。
- 新增 React 版本一键全栈启动脚本。

验收标准：

- React 前端可以独立安装依赖、启动开发服务和完成构建。
- Vue 前端仍可按原方式启动。
- React 前端可以调用 `/api/health` 和 `/api/auth/me`。

落地结果：

- React 前端目录为 `frontend/`。
- 技术栈为 React 19、TypeScript、Vite、React Router 和 Vitest。
- `pnpm test` 覆盖阶段一 API 客户端。
- `pnpm build` 可完成 TypeScript 严格检查和 Vite 生产构建。
- `scripts/start-react-local.sh` 可启动 React 版本全栈项目。

### 阶段 2：认证与基础布局（已完成）

- 迁移登录、注册、退出和当前用户恢复。
- 实现业务布局和基于角色的导航可见性。
- 保持普通用户与管理员入口隔离。

验收标准：

- 普通用户和管理员登录后看到正确导航。
- 未登录访问业务页会进入认证流程。
- 管理员专属入口不会对普通用户展示。

落地结果：

- API 客户端新增 `POST /api/auth/login`、`POST /api/auth/register` 和 `POST /api/auth/logout`。
- `AuthProvider` 负责 HttpOnly Cookie 登录态恢复、登录、注册和退出。
- `/login` 与 `/register` 为公开认证路由，已登录用户会回到工作台。
- `/`、`/history`、`/feedback` 为登录后可访问路由；`/models` 与 `/users` 仅管理员可见且可访问。
- 当前业务页为阶段二占位壳，评测工作台真实迁移进入阶段三。

### 阶段 3：评测工作台（核心迁移已完成）

- 迁移模型列表加载、问题输入、公开/私有选择、LLM Judge 开关和全局思考模式开关。
- 迁移 `POST /api/evaluation/tasks/stream` 的 NDJSON 读取和模型级渐进展示。
- 迁移 Markdown 渲染、DOMPurify 清洗、`<think>` 折叠和点赞/点踩反馈操作。

验收标准：

- 多模型评测可以按模型完成顺序渐进展示。
- 单个模型失败不影响其他模型展示。
- 回答详情、评分和点赞/点踩行为与 Vue 版本核心路径一致。

落地结果：

- `/` 已从阶段占位壳替换为 React 评测工作台。
- API 客户端新增 `GET /api/models/available`、`GET /api/token-usage/me/today`、`POST /api/evaluation/tasks/stream` 和 `POST /api/evaluation/responses/{responseId}/feedback`。
- React 工作台已支持可用模型加载、默认模型选择、今日 Token 用量展示、公开/私有评测、思考模式、LLM 评审模型选择和模型级等待卡片。
- NDJSON 读取使用 `ReadableStream`、`TextDecoder` 和按行缓冲解析；`model_response` 会替换对应模型等待卡片，其他模型继续等待。
- 回答卡片已支持摘要、关键指标、成本、三项评分条、全文展开、Markdown 安全渲染、`<think>` 折叠、评分命中项和点赞/点踩反馈。
- 公开评论分页、发布和删除暂未在 React 工作台迁移，随阶段四历史任务详情和统一回答详情一起迁移。

### 阶段 4：管理与历史页面

- 迁移管理员模型配置页面。
- 迁移管理员用户额度页面。
- 迁移历史任务分页、详情加载和反馈评论操作。
- 迁移反馈统计页面。

验收标准：

- 管理员可以维护模型配置和用户额度。
- 历史任务公开/私有可见性与后端权限一致。
- 反馈统计按用户角色展示正确范围。

### 阶段 5：并行验收与收尾

- 建立 React 前端构建、基础测试和手工验收清单。
- 对比 Vue 与 React 的核心业务路径。
- 决定 Vue 前端继续保留为历史实现，还是在后续单独任务中移除。

验收标准：

- React 前端核心路径通过本地验证。
- 文档、启动方式和验收命令同步。
- 是否移除 Vue 前端有明确单独决策，不在本阶段默认执行。
