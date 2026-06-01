# 系统功能与实现状态

最后更新：2026-06-02

本文档根据当前代码实现梳理 MultiChatEval 的系统功能、模块边界和完成情况。状态说明：

- 已实现：代码已经接入主流程或可直接运行。
- 部分实现：已有结构或界面，但能力仍有占位、缺口或未持久化。
- 未实现：当前代码中尚未落地。

## 1. 系统定位

MultiChatEval 是一个面向多模型问答的对话质量评估系统。用户输入同一个问题后，可以选择多个模型并发回答，系统展示每个模型的回答内容、耗时、输出长度、成本估算和规则评分，帮助用户横向比较不同模型的回答质量。

当前版本优先保证非流式、多模型、规则评分的完整展示链路。系统已经可以从前端发起评测请求，并由后端并发调用真实 OpenAI-compatible 模型接口，但评测任务、回答和评分数据暂未完整持久化。

## 2. 前端功能

### 2.1 多模型评测工作台

状态：已实现

入口文件：`frontend/src/views/EvaluationWorkspace.vue`

已实现能力：

- 展示“多模型评测工作台”主界面。
- 支持输入用户问题。
- 支持通过复选按钮选择已启用且已配置 API Key 的模型配置。
- 支持快速评测、标准评测、深度评测三个模式的界面切换。
- 支持 LLM 评审开关的界面交互。
- 点击“开始评测”后调用后端创建评测任务接口。
- 提交按钮会在请求期间进入 loading 状态。
- 输入为空、未选择模型或系统内没有可评测模型时禁止提交。
- 当系统内没有任何已配置 API Key 的模型时，首页会提醒用户进入“模型配置”页面填写自己的 API Key。

当前限制：

- 评测模式只停留在前端状态，暂未参与后端评分或模型调用策略。
- LLM 评审开关会随请求发送给后端，但后端暂未实际执行 LLM Judge。
- “历史任务”“反馈统计”目前只是静态导航按钮。

### 2.2 模型配置页面

状态：已实现

已实现能力：

- 侧边栏“模型配置”可切换到模型配置管理界面。
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
- 展示本次正在调用的模型数量。
- 每秒更新等待耗时。
- 为每个待返回模型展示等待卡片和占位动画。
- 等待态中显示临时耗时、输出等待中、成本待估算。

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
- 调用失败时展示失败状态和后端返回的错误信息。

当前限制：

- “采纳”“点赞”“详情”按钮已有界面，但暂未绑定反馈提交或详情弹窗逻辑。
- 前端当前只调用创建评测任务接口，尚未调用查询任务接口或反馈接口。

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

状态：部分实现

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

已实现能力：

- 接收前端提交的问题、模型列表和 LLM 评审开关。
- 根据 `modelIds` 从 `model_configs.id` 动态解析要调用的模型。
- 未传模型时默认选择已启用的 DeepSeek 和 MiniMax；不可用时回退到前两个已启用模型。
- 如果传入的模型 ID 全部无效，也按同样规则回退。
- 使用 `asyncio.gather` 并发调用多个模型。
- 只要至少一个模型调用成功，任务状态返回 `completed`。
- 所有模型均失败时，任务状态返回 `failed`。
- 返回每个模型的回答、耗时、输出 token、成本估算、状态和规则评分。

当前限制：

- `taskId` 当前固定返回 `1`，尚未创建真实数据库任务记录。
- `conversationId` 已在请求模型中定义，但当前服务层未使用。
- `enableJudge` 已接收，但当前服务层未使用。
- 任务、模型回答、评分结果尚未写入 MySQL。
- 当前接口为同步等待所有模型完成后一次性返回，暂不支持 SSE、WebSocket 或流式输出。

### 3.4 查询评测任务

状态：部分实现

接口：

```http
GET /api/evaluation/tasks/{task_id}
```

已实现能力：

- 路由和响应模型已定义。

当前限制：

- 当前返回固定示例数据：
  - `taskId` 使用请求路径中的 ID。
  - `status` 固定为 `completed`。
  - `prompt` 固定为“示例问题”。
  - `responses` 固定为空数组。
- 尚未从数据库读取历史任务。

### 3.5 提交用户反馈

状态：部分实现

接口：

```http
POST /api/evaluation/responses/{response_id}/feedback
```

请求字段：

- `feedbackType`：反馈类型，例如点赞、点踩、采纳。
- `comment`：可选评论。

已实现能力：

- 路由和请求模型已定义。
- 接口会返回收到的 `responseId`、`feedbackType` 和 `received` 状态。

当前限制：

- 反馈未写入数据库。
- 暂未校验 `feedbackType` 的合法取值。
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
- Zhipu/GLM 请求默认追加：

```json
{
  "thinking": {
    "type": "disabled"
  }
}
```

这样可以减少简单问题的 reasoning 内容和等待时间。

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
- 格式：如果问题包含“表格”，回答包含 `|` 得 10 分，否则 4 分；如果问题包含“代码”，回答包含代码块标记得 10 分，否则 4 分；其他情况默认 8 分。
- 安全性：当前固定为 10 分。
- 综合分：

```text
final =
  relevance * 0.30
+ completeness * 0.25
+ clarity * 0.20
+ format * 0.15
+ safety * 0.10
```

当前限制：

- 相关性评分较粗糙，尚未进行语义相似度判断。
- 安全性当前为固定分，尚未检测敏感内容或危险建议。
- 语言一致性、事实准确性、有用性等更细维度尚未真正参与当前接口返回。
- LLM Judge 分数尚未实现。

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

当前限制：

- 创建评测任务时未写入 `evaluation_tasks`。
- 模型回答未写入 `model_responses`。
- 规则评分结果未写入 `evaluation_results`。
- 用户反馈未写入 `user_feedback`。
- 评测服务已经从数据库读取模型配置，但任务、回答、评分仍以接口响应形式返回，未持久化。

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
- `scripts/start-local.sh` 可自动准备 `.env`、启动 MySQL、后端和前端开发服务。
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
- 暂无规则评分器单元测试。
- 暂无前端组件或端到端测试。
- 暂无数据库持久化相关测试。

## 9. 当前主流程状态

状态：部分实现，但已可验证前后端非持久化主链路

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
记录本次内存中的耗时、输出 token、成本估算和调用状态
  ↓
执行规则评分
  ↓
一次性返回结果
  ↓
前端以 Markdown、评分条和指标卡片展示
```

尚未完成的目标链路：

```text
创建数据库任务
  ↓
保存每个模型回答
  ↓
保存评分结果
  ↓
支持历史任务查询
  ↓
保存用户反馈
  ↓
结合规则评分、LLM Judge 和用户反馈生成推荐
```

## 10. 后续优先级建议

建议按以下顺序推进：

1. 接入数据库持久化：创建任务、保存回答、保存评分。
2. 将 `GET /api/evaluation/tasks/{task_id}` 改为真实查询。
3. 将反馈接口写入 `user_feedback`，并绑定前端按钮。
4. 为评测创建、规则评分和失败模型调用补充更多测试。
5. 将 `plain:` 密钥存储升级为 `enc:v1:` 加密存储。
6. 实现 LLM Judge，并明确 `enableJudge` 对接口返回的影响。
7. 增加历史任务和反馈统计页面。
8. 在核心流程稳定后再考虑流式输出。
