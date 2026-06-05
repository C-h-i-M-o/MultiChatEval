# 系统功能与实现状态

最后更新：2026-06-04

本文档根据当前代码实现梳理 MultiChatEval 的系统功能、模块边界和完成情况。状态说明：

- 已实现：代码已经接入主流程或可直接运行。
- 部分实现：已有结构或界面，但能力仍有占位、缺口或未持久化。
- 未实现：当前代码中尚未落地。

## 1. 系统定位

MultiChatEval 是一个面向多模型问答的对话质量评估系统。用户输入同一个问题后，可以选择多个模型并发回答，系统展示每个模型的回答内容、耗时、输出长度、成本估算、规则评分和可选 LLM Judge 评分，帮助用户横向比较不同模型的回答质量。

当前版本优先保证多模型、规则评分、LLM Judge、模型级渐进展示和历史任务查询的完整链路。系统已经可以从前端发起评测请求，并由后端并发调用真实 OpenAI-compatible 模型接口；哪个模型完整回答先完成，前端就先展示哪个模型。评测任务、回答、规则评分和 LLM Judge 结果会写入 MySQL，并可在历史任务页分页查看。

## 2. 前端功能

### 2.1 多模型评测工作台

状态：已实现

入口路径：`/`

入口文件：`frontend/src/views/EvaluationView.vue`

已实现能力：

- 展示“多模型评测工作台”主界面。
- 支持输入用户问题。
- 支持通过复选按钮选择已启用且已配置 API Key 的模型配置。
- 支持 LLM 评审开关；开启后必须选择一个已配置 API Key 的评审模型。
- 点击“开始评测”后调用后端创建评测任务接口。
- 提交按钮会在请求期间进入 loading 状态。
- 输入为空、未选择模型或系统内没有可评测模型时禁止提交。
- 当系统内没有任何已配置 API Key 的模型时，首页会提醒用户进入“模型配置”页面填写自己的 API Key。
- 支持全局“思考模式”开关，开关状态会随评测请求提交给后端。

当前限制：

- LLM Judge 第一版只做单回答评分，不做 pairwise 对战或多评审投票。
- 采纳、收藏和反馈统计暂未实现。

### 2.2 模型配置页面

状态：已实现

入口路径：`/models`

入口文件：`frontend/src/views/ModelConfigsView.vue`

已实现能力：

- 侧边栏“模型配置”可进入模型配置管理页面。
- 系统内置 DeepSeek、MiniMax、GLM 三家供应商模型。
- 内置配置可编辑 Base URL、API Key、模型名、展示名和启用状态，但不可删除。
- 用户可新增、编辑、启用/禁用、删除自定义 OpenAI-compatible 模型配置。
- 支持测试已保存配置或未保存草稿配置的连接。
- API Key 输入框留空时保留原密钥。
- 列表只展示密钥状态和掩码，不展示原始 API Key。

### 2.3 请求等待态

状态：已实现

已实现能力：

- 请求期间展示“模型调用中”提示。
- 展示本次模型调用的完成进度。
- 每秒更新等待耗时。
- 为每个待返回模型展示等待卡片和占位动画。
- 等待态中显示临时耗时、输出等待中、成本待估算。
- 已完成模型会立即从等待卡片替换为真实回答卡片。

### 2.4 结果对比展示

状态：已实现

已实现能力：

- 根据后端返回的 `responses` 渲染模型回答卡片。
- 单模型、双模型、三模型结果使用不同网格布局。
- 每张卡片展示：
  - 模型名称
  - 调用状态
  - 最终分或失败状态
  - 回答内容
  - 响应耗时
  - 输出 token 数
  - 估算成本
  - 相关性、完整性、清晰度、格式评分条
  - 点赞、点踩按钮和计数
- 调用失败时展示失败状态和后端返回的错误信息。
- 评分详情弹窗展示规则分、LLM Judge 分、最终分、命中项、评审理由和用户反馈摘要。

当前限制：

- 采纳和收藏暂未实现。
- 用户反馈暂不参与最终评分计算。

### 2.4.1 历史任务分页页

状态：已实现

入口路径：`/history`

入口文件：`frontend/src/views/HistoryView.vue`

已实现能力：

- 侧边栏“历史任务”可进入历史任务页。
- 进入历史页时分页加载最近评测任务。
- 支持切换页码和每页 10/20/50 条。
- 点击历史任务后加载完整回答和评分详情。
- 历史任务详情页可以继续对回答点赞或点踩。
- 历史任务时间固定按北京时间展示。
- `pending` 历史任务默认展示为“进行中”，超过前端请求超时时间后仍未完成才展示为“超时未完成”。
- 分页或详情加载失败时展示错误提示。

### 2.4.2 反馈统计页面

状态：部分实现

入口路径：`/feedback`

入口文件：`frontend/src/views/FeedbackStatsView.vue`

已实现能力：

- 侧边栏“反馈统计”可进入独立页面。
- 页面明确展示反馈统计暂未实现，避免导航入口无响应。

当前限制：

- 用户反馈已持久化，但暂未实现真实统计图表。
- 模型推荐逻辑尚未实现。

### 2.5 Markdown 与思考过程渲染

状态：已实现

入口文件：`frontend/src/components/MarkdownRenderer.vue`

已实现能力：

- 使用 `markdown-it` 渲染模型回答中的 Markdown 内容。
- 支持自动链接识别、换行、标题、列表、代码块、表格等 Markdown 内容。
- 使用 `DOMPurify` 清洗 HTML，降低模型输出导致的 XSS 风险。
- 外部链接自动添加 `target="_blank"` 与 `rel="noopener noreferrer"`。
- 自动解析 `<think>...</think>` 内容，并折叠到“思考过程”面板。
- 未闭合的 `<think>` 内容也会被识别为思考过程。
- 没有正式回答内容时展示“暂无回答内容”。

### 2.6 前端路由与布局

状态：已实现

相关文件：

- `frontend/src/components/AppLayout.vue`
- `frontend/src/components/ModelResponseCard.vue`
- `frontend/src/router/index.js`

已实现能力：

- 前端采用统一侧边栏布局。
- 已配置 `/`、`/models`、`/history`、`/feedback` 四个公开路径。
- 未匹配路径会重定向到 `/`。
- 模型回答卡片抽为复用组件，供评测结果和历史任务详情共同使用。

## 3. 后端 API 功能

### 3.1 应用入口与路由

状态：已实现

相关文件：

- `backend/app/main.py`
- `backend/app/api/routes.py`
- `backend/app/api/v1/health.py`
- `backend/app/api/v1/evaluation.py`

已实现能力：

- 创建 FastAPI 应用。
- 根据环境变量配置 CORS 允许来源。
- 所有业务接口统一挂载在 `/api` 前缀下。
- 已注册健康检查、评测和模型配置路由。

### 3.2 健康检查

状态：已实现

接口：

```http
GET /api/health
```

响应：

```json
{
  "status": "ok"
}
```

测试覆盖：

- `backend/tests/test_health.py` 已覆盖健康检查接口。

### 3.3 创建评测任务

状态：已实现

接口：

```http
POST /api/evaluation/tasks
```

相关文件：

- `backend/app/api/v1/evaluation.py`
- `backend/app/schemas/evaluation.py`
- `backend/app/services/evaluation_service.py`

请求字段：

- `conversationId`：可选，会话 ID。
- `prompt`：用户问题。
- `modelIds`：模型 ID 列表。
- `enableJudge`：是否启用 LLM 评审。
- `judgeModelId`：启用 LLM 评审时必填，表示评审模型的 `model_configs.id`。
- `enableThinking`：是否启用全局思考模式。

已实现能力：

- 接收前端提交的问题、模型列表、LLM 评审开关和评审模型 ID。
- 根据 `modelIds` 从 `model_configs.id` 动态解析要调用的模型。
- 未传模型时默认选择已启用的 DeepSeek 和 MiniMax；不可用时回退到前两个已启用模型。
- 如果传入的模型 ID 全部无效，也按同样规则回退。
- 使用 `asyncio.gather` 并发调用多个模型。
- 根据 `enableThinking` 对所有模型统一发送 `thinking.type=enabled` 或 `thinking.type=disabled`。
- 只要至少一个模型调用成功，任务状态返回 `completed`。
- 所有模型均失败时，任务状态返回 `failed`。
- 返回每个模型的回答、耗时、输出 token、成本估算、状态、规则评分和可选 LLM Judge 评分。
- 创建真实数据库任务记录，并返回真实 `taskId`。
- 将模型回答、规则评分和 LLM Judge 结果写入 MySQL。

当前限制：

- `conversationId` 已在请求模型中定义，会写入任务记录；会话管理功能尚未完善。
- `POST /api/evaluation/tasks` 仍为同步等待所有模型完成后一次性返回。
- 思考模式不提供思考程度选择。

### 3.3.1 创建评测任务并渐进返回模型结果

状态：已实现

接口：

```http
POST /api/evaluation/tasks/stream
```

相关文件：

- `backend/app/api/v1/evaluation.py`
- `backend/app/schemas/evaluation.py`
- `backend/app/services/evaluation_service.py`

已实现能力：

- 请求字段与 `POST /api/evaluation/tasks` 一致。
- 响应类型为 `application/x-ndjson`。
- 先返回 `task_started` 事件。
- 每个模型完整回答完成后立即返回 `model_response` 事件。
- 所有模型结束后返回 `task_completed` 事件。
- 单个模型失败只影响该模型事件，不中断其他模型调用。

当前限制：

- 该接口是模型级渐进返回，不是逐字 token 流式输出。
- 启用 LLM Judge 时，单个 `model_response` 事件会等待该回答的 Judge 评审完成后再返回。

### 3.4 查询评测任务

状态：已实现

接口：

```http
GET /api/evaluation/tasks/{task_id}
```

已实现能力：

- 从数据库读取评测任务、模型回答和规则评分。
- 不存在的任务返回 404。
- `responses[].id` 使用真实 `model_responses.id`。
- `responses[].modelConfigId` 使用 `model_configs.id`，供前端维持模型顺序。

### 3.4.1 分页查询历史评测任务

状态：已实现

接口：

```http
GET /api/evaluation/tasks?page=1&pageSize=10
```

已实现能力：

- 按 `created_at desc, id desc` 返回历史任务。
- 返回 `items`、`total`、`page`、`pageSize`。
- 每条任务包含任务 ID、状态、问题、创建时间、完成时间和回答数量。

### 3.5 提交用户反馈

状态：部分实现

接口：

```http
POST /api/evaluation/responses/{response_id}/feedback
```

请求字段：

- `feedbackType`：反馈类型，仅支持 `like` 和 `dislike`。
- `comment`：可选评论。

已实现能力：

- 路由和请求模型已定义。
- 反馈会写入 `user_feedback`。
- 匿名用户固定写入 `user_id = 0`，后续登录用户从 `id = 1` 开始自增。
- 同一用户对同一回答只能保留一个当前反馈。
- 重复提交相同类型会取消，提交另一类型会切换。
- 接口会返回 `responseId`、`feedbackType`、`active` 和最新反馈汇总。
- 历史任务详情会返回每条回答的点赞/点踩状态和数量。

当前限制：

- 暂未将反馈影响纳入评分或推荐逻辑。

### 3.6 模型配置接口

状态：已实现

接口：

- `GET /api/model-configs`
- `POST /api/model-configs`
- `PUT /api/model-configs/{model_config_id}`
- `DELETE /api/model-configs/{model_config_id}`
- `POST /api/model-configs/test`

已实现能力：

- 查询模型配置时自动补齐 DeepSeek、MiniMax、GLM 三个内置模型。
- 内置模型不会从 `.env` 读取 API Key，用户需要在前端模型配置页填写自己的 Key。
- 支持新增自定义 OpenAI-compatible 模型配置。
- 支持编辑内置和自定义配置。
- 支持删除自定义配置，内置配置只能禁用。
- 支持测试模型连接。
- API Key 当前以 `plain:<api_key>` 格式明文落库，业务代码通过统一 helper 保存、读取和掩码展示，保留未来升级为 `enc:v1:<ciphertext>` 的空间。

## 4. 模型调用功能

### 4.1 模型适配器接口

状态：已实现

入口文件：`backend/app/adapters/base.py`

已实现能力：

- 定义统一模型请求对象 `ModelRequest`。
- 定义 token 用量对象 `ModelUsage`。
- 定义模型回复对象 `ModelReply`。
- 定义抽象模型客户端 `ModelClient`，约束所有模型客户端必须实现：
  - `chat`
  - `get_model_name`
  - `estimate_cost`

### 4.2 OpenAI-compatible 客户端

状态：已实现

入口文件：`backend/app/adapters/openai_compatible.py`

已实现能力：

- 兼容 `/chat/completions` 协议。
- 使用非流式请求。
- 自动拼接 `{base_url}/chat/completions`。
- 使用 Bearer Token 认证。
- 请求参数包含：
  - `model`
  - `messages`
  - `max_tokens`
  - `temperature`
  - `stream: false`
- 支持通过 `extra_body` 追加模型供应商特定参数。
- 解析 `choices[0].message.content` 作为回答内容。
- 读取 `usage.prompt_tokens` 和 `usage.completion_tokens`。
- 当供应商未返回 usage 时，使用输入和输出字符长度作为兜底统计。
- 记录模型响应耗时。
- 根据输入、输出单价估算成本。
- API Key 或 Base URL 缺失时抛出明确错误。

当前限制：

- 当前默认模型价格均配置为 0，因此估算成本会返回 0。
- 暂未做供应商级别重试、限流、熔断或错误码归一化。

### 4.3 默认模型配置

状态：已实现

入口文件：`backend/app/services/model_config_service.py`

当前内置模型：

| 供应商 | 默认模型名 |
| --- | --- |
| deepseek | `deepseek-v4-flash` |
| minimax | `MiniMax-M2.5` |
| glm | `glm-4.7` |

已实现能力：

- 从 `.env` 读取三个内置供应商的默认 Base URL 和模型名，不读取 API Key。
- 查询模型配置时自动写入缺失的内置配置。
- 当前首页会在系统内没有任何 API Key 时提醒用户先进入模型配置页。
- 每个模型调用共享 `MODEL_REQUEST_TIMEOUT`，并使用对应模型配置的 `max_tokens`。
- 用户自定义供应商按 OpenAI-compatible 协议调用。
- 每次评测请求都会根据全局思考模式追加：

```json
{
  "thinking": {
    "type": "disabled"
  }
}
```

关闭思考模式时，`type` 为 `disabled`；开启思考模式时，`type` 为 `enabled`。该字段会以嵌套 JSON `thinking.type` 传输，不使用 `thinkingmode`。第一版不发送思考程度参数。如果某个供应商不支持该字段并返回错误，该错误会作为对应模型的失败结果展示。MiniMax 等 OpenAI-compatible 供应商可能在收到 `thinking.type=disabled` 后仍返回 `<think>` 或 reasoning 内容，当前前端会继续折叠展示这些内容。

## 5. 评分功能

### 5.1 规则评分器

状态：已实现

入口文件：`backend/app/services/rule_evaluator.py`

当前评分维度：

- 相关性 `relevance`
- 完整性 `completeness`
- 清晰度 `clarity`
- 格式 `format`
- 安全性 `safety`
- 综合分 `final`

实现规则：

- 相关性：提取问题和回答中的中文、英文、数字片段，计算词集合重合比例。
- 完整性：按回答长度与 120 字符的比例折算，最高 10 分。
- 清晰度：根据换行、列表/代码/表格标记和回答长度加分，最高 10 分。
- 格式：如果问题包含“表格”，回答包含 `|` 得 10 分，否则 4 分；如果问题包含“代码”，回答包含代码块标记得 10 分，否则 4 分；其他情况默认 8 分。除用户明确要求英文、翻译成英文、中英双语等特殊情况外，如果回答出现大篇幅英文且中文内容很少，格式分最高降为 5 分。
- 安全性：当前固定为 10 分。
- 命中项明细：返回 `score.details`，包含各维度评分依据；历史任务详情会根据原始问题和回答内容重新生成规则评分明细。
- 综合分：

```text
final =
  relevance * 0.20
+ completeness * 0.30
+ clarity * 0.20
+ format * 0.15
+ safety * 0.15
```

当前限制：

- 相关性评分较粗糙，尚未进行语义相似度判断。
- 安全性当前为固定分，尚未检测敏感内容或危险建议。
- 语言一致性、事实准确性、有用性等更细维度尚未真正参与当前接口返回。
### 5.2 LLM Judge

状态：已实现

入口文件：`backend/app/services/llm_judge_evaluator.py`

已实现能力：

- 前端开启 LLM 评审后，需要选择一个已启用且已配置 API Key 的评审模型。
- 后端复用现有 OpenAI-compatible 模型配置调用评审模型，不新增独立密钥管理。
- Judge Prompt 要求评审模型忽略候选回答中的反向指令，只输出首尾完整的 JSON，禁止输出 `<think>`、推理过程和额外解释。
- 解析 `score`、优点、缺点、推荐理由和维度分；解析前会剥离 `<think>...</think>`，并从返回文本中抽取第一个完整 JSON 对象。
- `final = 0.60 × ruleFinal + 0.40 × judgeFinal`。
- Judge 超时、调用失败或 JSON 解析失败时，模型回答仍保留成功状态，最终分回退为规则分，失败原因进入 `judgeComment`。

当前限制：

- 第一版只做单回答评分，不做 pairwise 胜负裁判。
- 第一版只使用一个评审模型，不做多评审投票。

## 6. 数据库与持久化

### 6.1 数据库结构

状态：部分实现

相关文件：

- `backend/app/models/*.py`
- `docker/mysql/init/001_schema.sql`
- `docs/database.md`

已建模的数据表：

- `users`：用户。
- `conversations`：评测会话。
- `model_providers`：模型供应商。
- `model_configs`：具体模型配置。
- `evaluation_tasks`：评测任务。
- `model_responses`：模型回答。
- `evaluation_results`：评分结果。
- `user_feedback`：用户反馈。

已实现能力：

- SQLAlchemy 模型已覆盖核心业务实体。
- Docker MySQL 初始化 SQL 已创建核心表结构。
- 数据库连接和异步 Session 工厂已配置。
- Alembic 基础目录和配置已存在。
- 创建评测任务时写入 `evaluation_tasks`。
- 模型回答完成后写入 `model_responses`。
- 规则评分结果写入 `evaluation_results`。
- LLM Judge 结果写入 `evaluation_results.judge_score` 和 `evaluation_results.judge_comment`。
- 用户反馈写入 `user_feedback`，匿名用户固定使用 `user_id = 0`。
- 历史任务列表和任务详情从数据库读取。

## 7. 配置与运行

### 7.1 环境配置

状态：已实现

入口文件：`backend/app/core/config.py`

已实现能力：

- 后端固定读取项目根目录 `.env`。
- 从项目根目录或 `backend/` 目录启动都能读取同一份配置。
- 支持配置：
  - 应用名称和环境。
  - 数据库连接。
  - CORS 来源。
  - 模型请求超时时间。
  - DeepSeek、MiniMax、GLM 的 Base URL 和模型名。
- `scripts/clear-builtin-api-keys.py` 用于一次性清空历史数据库中内置 DeepSeek、MiniMax、GLM 的 API Key，避免继续沿用旧的 `.env` 自动导入密钥。

### 7.2 本地运行

状态：已实现基础脚本与说明

已有能力：

- `docker-compose.yml` 提供 MySQL 服务。
- `scripts/start-local.sh` 可自动准备 `.env`、启动 MySQL、执行 Alembic 数据库迁移，并启动后端和前端开发服务。
- 启动脚本会在默认端口被占用时自动向后寻找可用端口，并把实际后端地址传给 Vite 代理。
- 后端可通过 `uvicorn app.main:app --reload` 启动。
- 前端可通过 `pnpm dev` 启动。
- 前端通过 Vite 代理或同源 `/api` 访问后端接口。

## 8. 测试覆盖

状态：部分实现

已实现：

- 后端健康检查测试：`backend/tests/test_health.py`。

当前缺口：

- 暂无评测任务创建接口测试。
- 暂无模型适配器单元测试。
- 已有规则评分器单元测试，覆盖综合权重、大篇幅英文回答格式扣分和用户明确要求英文时不扣分。
- 暂无前端组件或端到端测试。
- 暂无数据库持久化相关测试。

## 9. 当前主流程状态

状态：部分实现，但已可验证前后端持久化主链路

当前实际链路：

```text
用户输入问题
  ↓
前端从 GET /api/model-configs 加载可选模型
  ↓
前端选择模型并提交 POST /api/evaluation/tasks
  ↓
后端按 model_configs.id 读取模型配置
  ↓
并发调用 DeepSeek / MiniMax / GLM 或自定义 OpenAI-compatible 模型
  ↓
写入模型回答、耗时、输出 token、成本估算和调用状态
  ↓
执行规则评分并写入评分结果
  ↓
一次性返回结果
  ↓
前端以 Markdown、评分条和指标卡片展示
  ↓
前端历史任务页分页查询任务并加载详情
```

尚未完成的目标链路：

```text
结合规则评分、LLM Judge 和用户反馈生成推荐
```

## 10. 后续优先级建议

建议按以下顺序推进：

1. 基于已持久化的点赞、点踩数据实现反馈统计和模型推荐页面。
2. 为评测创建、规则评分和失败模型调用补充更多测试。
3. 将 `plain:` 密钥存储升级为 `enc:v1:` 加密存储。
4. 接入登录功能后，将匿名用户 `user_id = 0` 切换为真实用户反馈。
5. 在核心流程稳定后再考虑逐字 token 流式输出。
