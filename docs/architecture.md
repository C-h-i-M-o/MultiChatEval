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
6. 可选启用 LLM Judge，让评审模型输出结构化评分。
7. 前端在评测页以平衡摘要网格展示回答，在历史任务详情中以单列紧凑列表展示回答，并在统一的全文详情弹窗中展示完整 Markdown、评分、反馈和评论。
8. 用户在回答卡片上提交点赞或点踩反馈，后端以互斥状态式语义写入、切换或取消 `user_feedback`，并重算最终分。
9. 用户可以在评分详情中分页查看、发布和删除公开评论，评论独立写入 `user_comments`，不参与评分。

## 第一版边界

第一版先实现非逐字流式请求和规则评分，不做实时 token 级输出。前端通过模型级渐进返回能力展示结果：哪个模型完整回答先完成，哪个模型卡片就先展示，其他模型继续保持等待态。这样可以改善等待体验，同时避免逐字输出带来的适配器复杂度。

## 前端展示层

前端展示层采用 Vue Router 多路由结构，统一布局位于 `frontend/src/components/AppLayout.vue`。demo-v1 侧边栏只展示对比评测、模型配置和历史任务，各页面只承担单一业务职责。

当前展示层包含：

- `/` 对应 `frontend/src/views/EvaluationView.vue`，用于完成问题输入、模型选择、任务提交和结果对比。
- `/models` 对应 `frontend/src/views/ModelConfigsView.vue`，用于维护内置模型和自定义 OpenAI-compatible 模型。
- `/history` 对应 `frontend/src/views/HistoryView.vue`，用于分页查看最近评测任务，并可点击任务加载完整回答和评分详情。
- `/feedback` 对应 `frontend/src/views/FeedbackStatsView.vue`，当前为后续版本保留的反馈统计占位路由，不在 demo-v1 导航中展示。
- Element Plus 在应用入口启用中文语言配置，历史任务分页容量统一显示为 `/页`。
- 模型选择项从后端模型配置接口动态加载，直接显示具体模型名。
- `ModelResponseSummaryGrid` 提供 `grid` 和 `list` 两种模式：评测页使用六轨平衡网格，历史任务详情使用单列结构化列表。
- 评测页四个模型固定为两行两列，五至九个模型采用平衡分行并保证每行铺满；容器查询会根据结果区实际宽度降为两列或单列。
- 摘要卡或列表行展示模型名称、调用状态、最终分、耗时、输出 token、成本和回答预览；完整回答通过详情弹窗查看，避免长回答拉伸主页面。
- GSAP 负责结果卡片或列表行进入、等待卡替换、评分条补间和详情弹窗动效；组件卸载时清理动画上下文，并根据 `prefers-reduced-motion` 降低动画强度。
- 桌面端侧边栏使用 sticky 和视口高度约束，“默认流程”通过自动外边距保持在侧栏底部；移动端恢复普通文档流。
- `ModelResponseCard` 负责详情弹窗中的完整回答、指标、评分条、点赞/点踩、评分明细和公开评论展示。
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

后端在每次评测请求中会先把系统内置提示词拼接到用户原始问题前，再发送给模型；任务记录、历史详情和接口响应中的 `prompt` 仍保留用户原始问题。随后后端统一追加思考模式参数。关闭思考模式时，所有模型请求都会发送 `thinking.type=disabled`；开启思考模式时，所有模型请求都会发送 `thinking.type=enabled`。这里发送的是嵌套 JSON 字段 `thinking.type`，不是 `thinkingmode`。第一版不传递思考程度参数。如果某个 OpenAI-compatible 供应商不支持 `thinking` 字段并返回错误，该失败只展示在对应模型卡片中，不影响其他模型继续返回。MiniMax 等供应商即使收到 `thinking.type=disabled`，也可能仍在返回内容中包含 `<think>` 或 reasoning 字段，前端会按当前渲染规则折叠展示。

为了让前端尽早展示已完成模型，后端提供 `POST /api/evaluation/tasks/stream`。该接口使用 NDJSON 返回模型级事件，不做 token 级流式输出；旧的 `POST /api/evaluation/tasks` 仍保留一次性返回完整任务结果。

两个创建接口都会写入真实任务、模型回答和规则评分。规则评分器会先从评分输入中移除完整的 `<think>...</think>` 区块；遇到未闭合的 `<think>` 时忽略该标签及其后续内容，因此只有最终回答参与规则评分。原始回答仍完整写入数据库并通过接口返回，前端可继续折叠展示思考过程。规则评分器采用轻量本地多信号评分：相关性由字符 n-gram 相似度、关键词覆盖、意图覆盖、回答聚焦度、显式要求对齐和离题惩罚共同计算；安全性由危险输出控制、拒答质量、高风险领域谨慎性和隐私/凭据保护共同计算。评分过程不依赖外部语义模型或下载。可选 LLM Judge 有效时，基础分由规则分 60% 和 Judge 分 40% 合成。`GET /api/evaluation/tasks` 提供分页历史列表，`GET /api/evaluation/tasks/{taskId}` 从数据库返回完整任务详情、任务创建/完成时间，并携带每条回答的反馈状态。反馈接口会对 `user_feedback` 执行互斥状态式新增、切换或取消。

匿名反馈固定写入 `user_id = 0`。同一用户对同一回答只能保留一个当前反馈，重复点击相同类型会取消，点击另一类型会在点赞和点踩之间切换。没有反馈时最终分等于基础分；存在反馈时，点赞比例映射为 0–10 的反馈分，并以 10% 权重计入 `final_score`。反馈接口返回更新后的反馈状态和评分，前端同步刷新卡片。

公开评论使用独立的 `user_comments` 表和分页接口，不嵌入任务详情响应，避免评论增长导致历史任务载荷持续膨胀。评论支持发布和按归属硬删除，不支持编辑；评论不参与评分。当前所有匿名访客共用 `user_id = 0`，在登录体系接入前无法区分不同匿名访客。
