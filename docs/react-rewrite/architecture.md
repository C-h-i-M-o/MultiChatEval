# React 前端架构草案

最后更新：2026-07-03

## 架构原则

React 前端已经成为当前主前端。它复用现有后端能力，不引入新的后端业务范围；原 Vue 前端仅作为历史版本保留。

核心原则：

- API 优先复用：以 `docs/api.md` 为接口边界。
- 数据结构不变：以 `docs/database.md` 为持久化边界。
- 行为对齐历史版本：核心业务路径与原 `vue-frontend/` 页面保持一致。
- 主前端明确：后续新功能和样式维护默认在 `frontend/` 推进。
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

当前 React 主前端目录：

```text
frontend/
  src/
    api/client.ts              类型化 API 客户端、认证请求、评测流、管理页和反馈统计请求
    animations/                GSAP 页面入场、结果卡片和弹窗动画封装
    assets/                    React 前端品牌图标与静态视觉资产
    components/                Markdown 渲染、评分条、回答卡片、评论面板和组件库弹窗
    features/auth/             登录态恢复、认证上下文和错误识别
    features/evaluation/       评测类型、NDJSON 状态合并和回答内容处理
    features/history/          历史任务状态、时间和反馈合并工具
    features/navigation/       导航项和路由访问判断
    layout/AppLayout.tsx       登录后业务布局
    pages/                     登录注册、评测、历史、模型配置、用户额度和反馈统计页面
    routes/RouteGuards.tsx     公开路由和受保护路由
    App.tsx                    路由声明
    main.tsx                   React 挂载与 BrowserRouter
    styles.css                 认证页和基础布局样式
  vite.config.ts               Vite React 插件、Tailwind 插件与 /api 开发代理
  package.json                 pnpm 脚本和依赖
```

## 数据流

### 认证

1. React 应用启动后请求 `GET /api/auth/me`。
2. 后端通过 HttpOnly Cookie JWT 恢复用户。
3. 未登录用户访问业务页会跳转到 `/login?redirect=...`。
4. 登录或注册成功后，前端跳回原始业务路径或默认工作台。
5. 已登录用户访问 `/login` 或 `/register` 会回到工作台。
6. 普通用户无法看到或访问 `/models`、`/users` 管理员入口。

### 逐 token 流式评测

1. 前端请求 `GET /api/models/available` 获取可评测模型。
2. 用户提交问题、模型列表、公开/私有模式、LLM Judge 开关和思考模式。
3. 前端通过 `fetch` 调用 `POST /api/evaluation/tasks/stream`。
4. 前端使用 `ReadableStream`、`TextDecoder` 和按行缓冲解析 NDJSON。
5. 按 `task_started`、`model_delta`、`model_answer_completed`、`model_response`、`task_completed` 更新页面状态。

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

`<think>...</think>` 和未闭合 `<think>` 内容需要默认展开展示为思考过程，正式回答单独展示。

## 视觉与动效

React 前端保留原 Vue 版本的深色侧栏、浅色网格背景和金色品牌强调，并通过 `frontend/src/assets/logo.png` 统一登录页、侧栏和 favicon 的品牌图标。GSAP 动画集中封装在 `frontend/src/animations/`，用于页面入场、模型回答卡片渐进展示和完整回答弹窗；实现必须提供 `prefers-reduced-motion` 降级，避免影响减少动态效果偏好的用户。

## 路由建议

React 路由已经覆盖原 Vue 路由能力：

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
- Markdown、数学公式与思考过程渲染行为由 React 主前端维护，思考过程默认展开。
- 点赞、点踩和评分详情与后端状态一致。
- 公开评论交互已随历史任务详情迁移。
- 管理员页面不对普通用户暴露。
- React 替代过程不改变后端接口、数据库表和评分公式。
- 阶段五收尾验收以 `docs/react-rewrite/acceptance.md` 和 `scripts/verify-react-rewrite.sh` 为准。
