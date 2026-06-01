# 系统架构说明

MultiChatEval 采用前后端分离架构：

```text
Vue 前端
  ↓
FastAPI API
  ↓
Evaluation Service
  ├── Model Adapter Layer
  ├── Objective Metrics Evaluator
  ├── Rule-based Evaluator
  ├── LLM Judge Evaluator
  └── User Feedback Collector
  ↓
MySQL
```

## 核心流程

1. 用户输入问题，选择多个模型。
2. 后端创建评测任务。
3. 后端从数据库读取已启用的模型配置，并发请求 DeepSeek、MiniMax、GLM 或用户自定义 OpenAI-compatible 模型。
4. 系统记录回答内容、响应时间、token 数、成本估算和错误状态。
5. 规则评分器计算相关性、完整性、清晰度、语言一致性和格式符合度。
6. 可选启用 LLM Judge，让评审模型输出结构化评分。
7. 前端以自适应卡片、Markdown 回答内容和评分条展示对比结果。
8. 用户提交点赞、点踩、采纳或评论反馈。

## 第一版边界

第一版先实现非逐字流式请求和规则评分，不做实时 token 级输出。前端通过模型级渐进返回能力展示结果：哪个模型完整回答先完成，哪个模型卡片就先展示，其他模型继续保持等待态。这样可以改善等待体验，同时避免逐字输出带来的适配器复杂度。

## 前端展示层

前端主界面位于 `frontend/src/views/EvaluationWorkspace.vue`，用于完成问题输入、模型选择、任务提交和结果对比。

当前展示层包含：

- 模型选择项从后端模型配置接口动态加载，直接显示具体模型名。
- 侧边栏“模型配置”用于维护内置模型和自定义 OpenAI-compatible 模型。
- 结果卡片根据返回模型数量自适应布局。
- 模型调用期间展示等待卡片、耗时计数和占位动画；单个模型完成后立即替换为真实回答卡片。
- 评测表单提供全局“思考模式”开关，所有已选模型使用相同开关状态，不提供思考程度选择。
- `MarkdownRenderer` 负责将模型输出渲染为安全的 HTML。
- `MarkdownRenderer` 会把 `<think>...</think>` 中的内容折叠为“思考过程”，让最终回答更清晰。

## 模型调用层

后端通过 `OpenAICompatibleClient` 统一调用兼容 `/chat/completions` 协议的模型服务。模型配置来自 `model_providers` 和 `model_configs`，评测任务使用 `model_configs.id` 选择模型。

系统内置三家供应商：

- `deepseek-v4-flash`
- `MiniMax-M2.5`
- `glm-4.7`

用户需要在模型配置页为内置模型填写自己的 API Key，也可以新增其他 OpenAI-compatible 供应商模型。系统不会从 `.env` 读取内置模型 API Key。API Key 当前以 `plain:` 版本化明文格式保存，所有业务逻辑通过密钥 helper 读取，未来可以升级为 `enc:v1:` 加密格式而不改变接口。

后端在每次评测请求中统一追加思考模式参数。关闭思考模式时，所有模型请求都会发送 `thinking.type=disabled`；开启思考模式时，所有模型请求都会发送 `thinking.type=enabled`。第一版不传递思考程度参数。如果某个 OpenAI-compatible 供应商不支持 `thinking` 字段并返回错误，该失败只展示在对应模型卡片中，不影响其他模型继续返回。

为了让前端尽早展示已完成模型，后端提供 `POST /api/evaluation/tasks/stream`。该接口使用 NDJSON 返回模型级事件，不做 token 级流式输出；旧的 `POST /api/evaluation/tasks` 仍保留一次性返回完整任务结果。
