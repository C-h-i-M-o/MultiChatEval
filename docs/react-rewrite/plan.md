# React 前端重构计划

最后更新：2026-07-03

## 目标

React 技术栈前端已经完成对原 Vue 前端的功能替代。本文档保留阶段计划、迁移顺序和落地结果，作为后续维护与面试说明的工程证据链；后续新功能和样式优化默认在 `frontend/` React 主前端推进。

## 非目标

- 不继续开发 v2 已冻结的新功能。
- 不重写后端 API、数据库结构、评分公式或权限模型。
- 不把模型级 NDJSON 渐进返回改成逐字 Token 流式输出。
- 不删除 `vue-frontend/` 历史版本，除非后续单独任务明确要求。

## 阶段计划

### 阶段 1：React 工程初始化（已完成）

- 新建独立 React 前端目录。
- 明确包管理、构建命令、路由方案、状态管理、API 封装和样式方案。
- 接入基础登录态恢复、错误提示和开发代理。
- 新增 React 主前端一键全栈启动脚本。

验收标准：

- React 前端可以独立安装依赖、启动开发服务和完成构建。
- Vue 前端仍可作为历史版本启动。
- React 前端可以调用 `/api/health` 和 `/api/auth/me`。

落地结果：

- React 前端目录为 `frontend/`。
- 技术栈为 React 19、TypeScript、Vite、React Router、Vitest、Tailwind CSS、Ant Design、Recharts 和 GSAP。
- `pnpm test` 覆盖阶段一 API 客户端。
- `pnpm build` 可完成 TypeScript 严格检查和 Vite 生产构建。
- `scripts/start-local.sh` 可启动 React 主前端全栈项目。

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
- 阶段二完成时业务页仍为占位壳，真实业务页面已在阶段三和阶段四迁移完成。

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
- 公开评论分页、发布和删除已随阶段四历史任务详情迁移。

### 阶段 4：管理与历史页面（已完成）

- 迁移管理员模型配置页面。
- 迁移管理员用户额度页面。
- 迁移历史任务分页、详情加载和反馈评论操作。
- 迁移反馈统计页面。

验收标准：

- 管理员可以维护模型配置和用户额度。
- 历史任务公开/私有可见性与后端权限一致。
- 反馈统计按用户角色展示正确范围。

已落地内容：

- `/history` 已从占位壳替换为 React 历史任务页面。
- React API 客户端已接入 `GET /api/evaluation/tasks`、`GET /api/evaluation/tasks/{taskId}`、`GET/POST /api/evaluation/responses/{responseId}/comments` 和 `DELETE /api/evaluation/comments/{commentId}`。
- 历史页支持分页、每页数量切换、详情加载、公开/私有标记、任务状态标记和超时未完成提示。
- 历史详情复用 React 回答卡片，支持点赞/点踩反馈、完整回答展开、评分详情和公开评论分页、发布、删除。
- `/models` 已迁移为管理员模型配置页面，支持列表、预设填充、新增、编辑、启用/禁用、删除和连接测试。
- `/users` 已迁移为管理员用户额度页面，支持查看用户今日 Token 用量并调整普通用户每日额度。
- `/feedback` 已迁移为按角色分流的反馈统计页面，普通用户查看个人统计，管理员查看全局模型表现、每日趋势和互动明细。

### 阶段 5：并行验收与收尾（已完成）

- 建立 React 前端构建、基础测试和手工验收清单。
- 对比 Vue 与 React 的核心业务路径。
- 确认 Vue 前端继续作为历史版本保留，是否移除留待后续单独任务决策。

验收标准：

- React 前端核心路径通过本地验证。
- 文档、启动方式和验收命令同步。
- Vue 前端保留为历史版本，是否移除不在本阶段默认执行。

已落地内容：

- 新增 `docs/react-rewrite/acceptance.md`，记录自动验收命令、React 手工核心路径和 Vue 历史版本保留决策。
- 新增 `scripts/verify-react-rewrite.sh`，统一执行后端测试、React 测试、React 构建、Vue 测试、Vue 构建和 `git diff --check`。
- 明确阶段五不删除 `vue-frontend/`，Vue 前端继续作为历史版本保留。
