# React 前端架构草案

最后更新：2026-07-02

## 架构原则

React 前端是现有 Vue 前端的并行重构版本。它复用现有后端能力，不引入新的后端业务范围。

核心原则：

- API 优先复用：以 `docs/api.md` 为接口边界。
- 数据结构不变：以 `docs/database.md` 为持久化边界。
- 行为对齐 Vue：以现有 `frontend/` 页面为交互基线。
- 渐进迁移：React 与 Vue 在迁移期并行存在。
- 最小新增依赖：只引入 React 工程必要依赖，避免为未实现功能提前选型。

## 建议模块边界

```text
React 前端
  ├── 路由层
  ├── 认证与用户状态
  ├── API 客户端
  ├── 评测工作台
  ├── 历史任务
  ├── 管理员模型配置
  ├── 用户额度管理
  ├── 反馈统计
  └── 通用展示组件
FastAPI API
MySQL
```

## 数据流

### 认证

1. React 应用启动后请求 `GET /api/auth/me`。
2. 后端通过 HttpOnly Cookie JWT 恢复用户。
3. 前端根据用户角色控制路由访问和导航显示。

### 模型级渐进评测

1. 前端请求 `GET /api/models/available` 获取可评测模型。
2. 用户提交问题、模型列表、公开/私有模式、LLM Judge 开关和思考模式。
3. 前端通过 `fetch` 调用 `POST /api/evaluation/tasks/stream`。
4. 前端使用 `ReadableStream`、`TextDecoder` 和按行缓冲解析 NDJSON。
5. 按 `task_started`、`model_response`、`task_completed` 更新页面状态。

### 安全渲染

模型回答仍按以下链路处理：

```text
模型输出
  ↓
Markdown 解析
  ↓
DOMPurify 清洗
  ↓
React 渲染
```

`<think>...</think>` 和未闭合 `<think>` 内容需要折叠为思考过程，正式回答单独展示。

## 路由建议

React 路由应覆盖现有 Vue 路由能力：

- `/login`：登录。
- `/register`：注册。
- `/`：多模型评测工作台。
- `/models`：管理员模型配置。
- `/users`：管理员用户额度。
- `/history`：历史任务。
- `/feedback`：反馈统计。

## 验收重点

- 登录态恢复和角色隔离正确。
- `POST /api/evaluation/tasks/stream` 的 NDJSON 分片解析可靠。
- Markdown 与思考过程渲染行为与 Vue 版本一致。
- 点赞、点踩、评论和评分详情与后端状态一致。
- 管理员页面不对普通用户暴露。
- React 重构不改变后端接口、数据库表和评分公式。
