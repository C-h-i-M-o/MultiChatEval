# 系统架构说明

MultiChatEval 采用前后端分离架构。当前主前端为 `frontend/` React 19 + TypeScript + Vite 应用，已完成对原 Vue 前端的功能替代；`vue-frontend/` 仅作为历史版本保留。v2 已冻结，后续新功能和样式维护默认在 React 前端推进，并复用同一套 FastAPI API、MySQL 数据结构和评分逻辑。

```text
React 前端（当前主前端）
  ↓
FastAPI API
  ├── Auth / RBAC
  ├── Token Quota Service
  ├── Feedback Stats Service
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

1. 用户注册或登录，后端通过 HttpOnly Cookie JWT 恢复当前用户。
2. 用户输入问题，选择多个模型和公开或私有模式。
3. 后端检查普通用户今日剩余额度，再创建评测任务。
4. 后端从数据库读取已启用的模型配置，并发请求模型。
5. 系统持久化模型回答、四类 Token 与费用、参数快照、总 Token 流水、规则评分和可选 LLM Judge 结果。
6. 前端展示评测结果，登录用户提交归属于自己的反馈和评论。

## 认证与权限层

- 开放注册用户默认为普通用户。
- 密码使用 Argon2 哈希，登录态使用写入 HttpOnly Cookie 的短期 JWT。
- `get_current_user` 负责认证，`require_admin` 负责管理员授权。
- 普通用户通过精简接口读取可评测模型，完整模型配置接口仅管理员可访问。
- 反馈统计使用个人与管理员双端点：普通用户只能读取本人任务表现与本人互动汇总，管理员端点通过 `require_admin` 返回全局聚合和互动明细。
- 公开任务对所有登录用户可见；私有任务仅创建者可见。
- 对无权访问的私有任务或回答返回 404，避免资源枚举。

## 第一版边界

当前主流程已支持逐 token 流式请求和规则评分。前端通过 NDJSON 增量事件实时展示各模型回答；单个模型回答完成后显示“评分中……”，评分和持久化完成后再展示最终分数、Token、成本和反馈入口。

## 前端展示层

当前前端展示层采用 React Router 多路由结构，统一业务布局位于 `frontend/src/layout/AppLayout.tsx`。登录和注册页面使用独立布局；业务导航根据当前用户角色显示。React 替代 Vue 的阶段文档保留在 `docs/react-rewrite/`，后续功能状态以本文档和 `docs/system-features-status.md` 为准。

当前 React 展示层包含：

- `/` 对应 `frontend/src/pages/EvaluationPage.tsx`，用于完成问题输入、模型选择、任务提交和结果对比。
- `/login` 和 `/register` 对应 `frontend/src/pages/AuthPage.tsx`，用于登录和开放注册。
- `/models` 对应 `frontend/src/pages/ModelConfigsPage.tsx`，仅管理员用于通过供应商预设或空白模板维护 OpenAI-compatible 模型。
- `/users` 对应 `frontend/src/pages/AdminUsersPage.tsx`，用于查看今日 Token 用量并调整普通用户每日额度。
- `/history` 对应 `frontend/src/pages/HistoryPage.tsx`，用于分页查看最近评测任务，并可点击任务加载完整回答和评分详情。
- `/feedback` 对应 `frontend/src/pages/FeedbackStatsPage.tsx`，所有登录用户均可进入；页面根据角色展示个人统计或管理员全局统计。
- Ant Design 在应用入口启用中文语言配置，历史任务和反馈统计分页使用中文交互。
- 模型选择项从后端模型配置接口动态加载，直接显示具体模型名。
- 评测结果和历史详情复用 `frontend/src/components/ModelResponseCard.tsx` 展示模型回答、评分和反馈操作。
- 评测页四个模型固定为两行两列，五至九个模型采用平衡分行并保证每行铺满；容器查询会根据结果区实际宽度降为两列或单列。
- 摘要卡或列表行展示模型名称、调用状态、最终分、耗时、输出 Token、总费用和回答预览；总费用悬停或聚焦时展示四项明细。
- GSAP 动画集中封装在 `frontend/src/animations/pageMotion.ts`，负责页面入场、等待卡替换、回答卡片和详情弹窗动效；组件卸载时清理动画上下文，并根据 `prefers-reduced-motion` 降低动画强度。
- 桌面端侧边栏固定在可视区域内；移动端使用深色抽屉导航，保持与桌面端一致的品牌底色和高对比文字。
- `ModelResponseCard` 负责卡片内 Markdown 流式渲染、底部感知自动滚动、完整回答弹窗中的 Markdown、指标、评分条、点赞/点踩、评分明细和公开评论展示。
- 模型调用期间展示等待卡片、耗时计数和占位动画；单个模型完成后立即替换为真实回答卡片。
- 评测表单提供全局“思考模式”开关，所有已选模型使用相同开关状态，不提供思考程度选择。
- `frontend/src/components/MarkdownRenderer.tsx` 负责将模型输出渲染为安全的 HTML，并支持 `$...$` / `$$...$$` 数学公式。
- `MarkdownRenderer` 会把 `<think>...</think>` 中的内容默认展开展示为“思考过程”，让思考过程和最终回答都能在流式响应中同步更新。

## 模型调用层

后端通过 `OpenAICompatibleClient` 统一调用兼容 `/chat/completions` 协议的模型服务。模型配置来自 `model_providers` 和 `model_configs`，评测任务使用 `model_configs.id` 选择模型。

系统不再自动创建内置供应商。管理员从 DeepSeek、MiniMax、GLM、Qwen、Xiaomi MiMo、OpenAI 预设或 OpenAI-compatible 空白模板创建配置。普通用户只读取管理员启用且已配置密钥的模型精简列表。API Key 当前以 `plain:` 版本化明文格式保存，所有业务逻辑通过密钥 helper 读取，未来可以升级为 `enc:v1:` 加密格式而不改变接口。

适配器归一化输入、输出、缓存命中和缓存创建四类 Token，并按模型保存的每百万 Token 单价计算费用。模型回答同时保存不含 API Key 的参数与价格快照，避免配置更新后历史费用失去依据。

`TokenQuotaService` 按北京时间自然日检查和累计普通用户总 Token。任务创建前只检查是否仍有余额，不预占最大输出；每个回答持久化时写入流水并原子更新每日汇总。管理员不受额度限制。

后端在每次评测请求中会先把系统内置提示词拼接到用户原始问题前，再发送给模型；任务记录、历史详情和接口响应中的 `prompt` 仍保留用户原始问题。随后后端统一追加思考模式参数。关闭思考模式时，所有模型请求都会发送 `thinking.type=disabled`；开启思考模式时，所有模型请求都会发送 `thinking.type=enabled`。这里发送的是嵌套 JSON 字段 `thinking.type`，不是 `thinkingmode`。第一版不传递思考程度参数。如果某个 OpenAI-compatible 供应商不支持 `thinking` 字段并返回错误，该失败只展示在对应模型卡片中，不影响其他模型继续返回。MiniMax 等供应商即使收到 `thinking.type=disabled`，也可能仍在返回内容中包含 `<think>` 或 reasoning 字段，前端会按当前渲染规则默认展开展示。

为了让前端尽早展示模型生成过程，后端提供 `POST /api/evaluation/tasks/stream`。该接口使用 NDJSON 返回多模型逐 token 事件：模型生成中持续返回 `model_delta`，单个模型回答结束后返回 `model_answer_completed` 让前端展示“评分中……”，评分和持久化完成后再返回最终 `model_response`。旧的 `POST /api/evaluation/tasks` 仍保留一次性返回完整任务结果。

两个创建接口都会写入真实任务、模型回答和规则评分。规则评分器会先从评分输入中移除完整的 `<think>...</think>` 区块；遇到未闭合的 `<think>` 时忽略该标签及其后续内容，因此只有最终回答参与规则评分。原始回答仍完整写入数据库并通过接口返回，前端可继续默认展开展示思考过程。规则评分器采用轻量本地多信号评分：相关性由字符 n-gram 相似度、关键词覆盖、意图覆盖、回答聚焦度、显式要求对齐和离题惩罚共同计算；安全性由危险输出控制、拒答质量、高风险领域谨慎性和隐私/凭据保护共同计算。评分过程不依赖外部语义模型或下载。可选 LLM Judge 有效时，基础分由规则分 60% 和 Judge 分 40% 合成。`GET /api/evaluation/tasks` 提供分页历史列表，`GET /api/evaluation/tasks/{taskId}` 从数据库返回完整任务详情、任务创建/完成时间，并携带每条回答的反馈状态。反馈接口会对 `user_feedback` 执行互斥状态式新增、切换或取消。

新反馈写入当前登录用户 ID，demo-v1 旧匿名反馈继续保留在 `user_id = 0`。同一用户对同一回答只能保留一个当前反馈，重复点击相同类型会取消，点击另一类型会在点赞和点踩之间切换。没有反馈时最终分等于基础分；存在反馈时，点赞比例映射为 0–10 的反馈分，并以 10% 权重计入 `final_score`。反馈接口返回更新后的反馈状态和评分，前端同步刷新卡片。

公开评论使用独立的 `user_comments` 表和分页接口，不嵌入任务详情响应，避免评论增长导致历史任务载荷持续膨胀。评论支持发布和按归属硬删除，不支持编辑；评论不参与评分。新评论归属当前登录用户，只有作者可以删除。

`FeedbackStatsService` 直接聚合已持久化的任务、回答、评分、点赞、点踩和评论，不建立预聚合表。个人统计按 `evaluation_tasks.user_id` 限定本人任务，同时单独按互动记录的 `user_id` 统计本人操作；管理员统计覆盖公开、私有和历史匿名数据。评分与调用使用回答创建时间，点赞、点踩和评论使用各自创建时间，7 天和 30 天边界按北京时间自然日计算。各数据源分别聚合后再按模型和日期合并，避免多表联接导致重复计数。本阶段没有表结构变化或数据库迁移。
