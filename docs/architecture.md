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
2. 后端创建评测任务，并写入 `evaluation_tasks`。
3. 后端从数据库读取已启用的模型配置，并发请求 DeepSeek、MiniMax、GLM 或用户自定义 OpenAI-compatible 模型。
4. 系统将每个模型的回答内容、响应时间、token 数、成本估算和错误状态写入 `model_responses`。
5. 规则评分器计算相关性、完整性、清晰度、格式符合度和安全性，并写入 `evaluation_results`。
6. 可选启用 LLM Judge，使用用户单独指定的已配置模型对成功回答输出结构化 JSON 评分。
7. 前端以自适应卡片、Markdown 回答内容、评分条和评分详情弹窗展示对比结果。
8. 用户在评测页或历史任务详情页提交点赞、点踩反馈，后端写入 `user_feedback`。

## 第一版边界

第一版先实现非逐字流式请求和规则评分，不做实时 token 级输出。前端通过模型级渐进返回能力展示结果：哪个模型完整回答先完成，哪个模型卡片就先展示，其他模型继续保持等待态。这样可以改善等待体验，同时避免逐字输出带来的适配器复杂度。

## 前端展示层

前端展示层采用 Vue Router 多路由结构，统一布局位于 `frontend/src/components/AppLayout.vue`。侧边栏导航负责在对比评测、模型配置、历史任务和反馈统计之间切换，各页面只承担单一业务职责。

当前展示层包含：

- `/` 对应 `frontend/src/views/EvaluationView.vue`，用于完成问题输入、模型选择、任务提交和结果对比。
- `/models` 对应 `frontend/src/views/ModelConfigsView.vue`，用于维护内置模型和自定义 OpenAI-compatible 模型。
- `/history` 对应 `frontend/src/views/HistoryView.vue`，用于分页查看最近评测任务，并可点击任务加载完整回答和评分详情。
- `/feedback` 对应 `frontend/src/views/FeedbackStatsView.vue`，当前为反馈统计占位页。
- 模型选择项从后端模型配置接口动态加载，直接显示具体模型名。
- 结果卡片根据返回模型数量自适应布局。
- `ModelResponseCard` 复用展示评测结果和历史任务详情中的模型回答、指标、评分条和点赞/点踩按钮。
- `ModelResponseCard` 的评分详情弹窗展示规则分、LLM Judge 分、最终分、维度权重、评审理由和用户反馈摘要。
- 模型调用期间展示等待卡片、耗时计数和占位动画；单个模型完成后立即替换为真实回答卡片。
- 评测表单提供全局“思考模式”开关，所有已选模型使用相同开关状态，不提供思考程度选择。
- 评测表单提供“LLM 评审”开关，开启后必须选择一个已配置 API Key 的模型作为评审模型。
- `MarkdownRenderer` 负责将模型输出渲染为安全的 HTML。
- `MarkdownRenderer` 会把 `<think>...</think>` 中的内容折叠为“思考过程”，让最终回答更清晰。

## 模型调用层

后端通过 `OpenAICompatibleClient` 统一调用兼容 `/chat/completions` 协议的模型服务。模型配置来自 `model_providers` 和 `model_configs`，评测任务使用 `model_configs.id` 选择模型。

系统内置三家供应商：

- `deepseek-v4-flash`
- `MiniMax-M2.5`
- `glm-4.7`

用户需要在模型配置页为内置模型填写自己的 API Key，也可以新增其他 OpenAI-compatible 供应商模型。系统不会从 `.env` 读取内置模型 API Key。API Key 当前以 `plain:` 版本化明文格式保存，所有业务逻辑通过密钥 helper 读取，未来可以升级为 `enc:v1:` 加密格式而不改变接口。

后端在每次评测请求中会先把系统内置提示词拼接到用户原始问题前，要求模型直接作答，并在除专业名词和特殊情况外使用中文回答问题；任务记录、历史详情和接口响应中的 `prompt` 仍保留用户原始问题。随后后端统一追加思考模式参数。关闭思考模式时，所有模型请求都会发送 `thinking.type=disabled`；开启思考模式时，所有模型请求都会发送 `thinking.type=enabled`。这里发送的是嵌套 JSON 字段 `thinking.type`，不是 `thinkingmode`。第一版不传递思考程度参数。如果某个 OpenAI-compatible 供应商不支持 `thinking` 字段并返回错误，该失败只展示在对应模型卡片中，不影响其他模型继续返回。MiniMax 等供应商即使收到 `thinking.type=disabled`，也可能仍在返回内容中包含 `<think>` 或 reasoning 字段，前端会按当前渲染规则折叠展示。

为了让前端尽早展示已完成模型，后端提供 `POST /api/evaluation/tasks/stream`。该接口使用 NDJSON 返回模型级事件，不做 token 级流式输出；旧的 `POST /api/evaluation/tasks` 仍保留一次性返回完整任务结果。

两个创建接口都会写入真实任务、模型回答和评分结果。规则评分先计算本地 `rule_score`。LLM Judge 第一版参考 promptfoo、FastChat MT-Bench 和 OpenCompass 的做法，作为独立评审器叠加在规则评分之后：前端开启“LLM 评审”时必须选择一个评审模型，后端复用该模型的 OpenAI-compatible 配置，对每条成功回答要求输出 JSON，解析 `score`、优点、缺点、推荐理由和维度分。最终分为 `0.60 × 规则分 + 0.40 × Judge 分`；未启用 Judge 或 Judge 失败时最终分保留规则分，失败原因写入评分详情。`GET /api/evaluation/tasks` 提供分页历史列表，`GET /api/evaluation/tasks/{taskId}` 从数据库返回完整任务详情，并包含每条回答的点赞/点踩状态。

用户反馈接口 `POST /api/evaluation/responses/{responseId}/feedback` 复用 `user_feedback` 表。匿名用户固定写入 `user_id = 0`；同一用户对同一回答只能保留一个当前反馈，重复点击相同类型会取消，点击另一类型会切换。当前反馈只用于展示和后续推荐基础数据，不参与 `final_score` 计算。
