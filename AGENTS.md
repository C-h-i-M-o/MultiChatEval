# AGENT.md

## 项目概览

MultiChatEval 是一个“面向多模型问答的对话质量评估系统”。项目目标不是绝对判断哪个 AI 回答最好，而是通过多模型并发回答、客观指标、规则评分、可选 LLM 评审和用户反馈，帮助用户结构化比较不同模型回答。

一句话定位：

> 多模型对话质量评估与智能推荐平台。

## 当前版本状态

当前 `codex/dev-v2` 分支已完成 v2 阶段 1：开放注册、HttpOnly Cookie JWT、普通用户/管理员 RBAC、真实用户数据归属和公开/私有评测。demo-v1 的多模型评测、评分、历史、反馈和评论闭环继续保留。

## 当前技术栈

- 后端：Python、FastAPI、SQLAlchemy 2.0、Alembic、Pydantic Settings、pytest
- 前端：Vue 3、JavaScript、Vite、Pinia、Vue Router、Axios、Element Plus、Markdown-it、DOMPurify
- 数据库：MySQL 8
- 本地数据库环境：Docker Compose
- 包管理：前端优先使用 pnpm

注意：项目要求前端使用 JavaScript，不使用 TypeScript。

## 目录结构

```text
MultiChatEval/
  backend/        FastAPI 后端服务
  frontend/       Vue 3 + JavaScript 前端应用
  docker/         MySQL 初始化脚本
  docs/           架构、接口、数据库和开源复用说明
  scripts/        本地启动与维护脚本
  docker-compose.yml
  README.md
  .env.example
```

## 已完成内容

### 后端

- FastAPI 应用入口：`backend/app/main.py`
- 配置管理：`backend/app/core/config.py`
- 数据库连接：`backend/app/db/session.py`
- SQLAlchemy 基础模型：
    - 用户
    - 会话
    - 模型供应商
    - 模型配置
    - 评测任务
    - 模型回答
    - 评分结果
    - 用户反馈
    - 用户评论
- API 路由：
    - `GET /api/health`
    - `POST /api/auth/register`
    - `POST /api/auth/login`
    - `POST /api/auth/logout`
    - `GET /api/auth/me`
    - `GET /api/models/available`
    - `GET /api/admin/model-configs`
    - `POST /api/admin/model-configs`
    - `PUT /api/admin/model-configs/{modelConfigId}`
    - `DELETE /api/admin/model-configs/{modelConfigId}`
    - `POST /api/admin/model-configs/test`
    - `POST /api/evaluation/tasks`
    - `POST /api/evaluation/tasks/stream`
    - `GET /api/evaluation/tasks`
    - `GET /api/evaluation/tasks/{taskId}`
    - `POST /api/evaluation/responses/{responseId}/feedback`
    - `GET /api/evaluation/responses/{responseId}/comments`
    - `POST /api/evaluation/responses/{responseId}/comments`
    - `DELETE /api/evaluation/comments/{commentId}`
- 模型适配器接口：`backend/app/adapters/base.py`
- OpenAI-compatible 真实调用适配器：`backend/app/adapters/openai_compatible.py`
- 规则评分器：`backend/app/services/rule_evaluator.py`
- 规则评分相关性使用轻量本地多信号评分，不依赖外部语义模型或下载。
- 当前评测服务已接入真实模型 API，并从数据库中的模型配置动态读取可调用模型。
- 评测请求发送给模型前，会在用户原始问题前拼接系统内置提示词；数据库、历史任务和接口响应中的 `prompt` 仍保留用户原始问题。
- 系统内置 DeepSeek、MiniMax、GLM 三个模型配置，但不会从 `.env` 读取 API Key；管理员需要在前端“模型配置”页面维护 API Key。
- 评测请求支持全局“思考模式”开关。关闭时所有模型统一发送 `thinking.type=disabled`；开启时统一发送 `thinking.type=enabled`；不传递思考程度参数。
- 思考模式字段以嵌套 JSON `thinking.type` 传输，不使用 `thinkingmode`。MiniMax 等 OpenAI-compatible 供应商即使收到 `thinking.type=disabled`，也可能仍返回 `<think>` 或 reasoning 内容。
- `POST /api/evaluation/tasks` 保留一次性返回完整结果。
- `POST /api/evaluation/tasks/stream` 支持模型级渐进返回：哪个模型完整回答先完成，哪个模型结果先展示。
- 评测任务、模型回答、规则评分、LLM Judge 结果、点赞/点踩和评论会真实写入 MySQL。
- `GET /api/evaluation/tasks` 支持分页查询历史任务。
- `GET /api/evaluation/tasks/{taskId}` 支持从数据库查询任务详情。
- 评测任务支持 `public` 和 `private`；公开任务对所有登录用户可见，私有任务只对创建者可见。
- 反馈和评论归属当前登录用户，用户只能删除自己的评论。

### 前端

- Vue 3 + JavaScript + Vite 基础项目
- 登录页和注册页：`frontend/src/views/AuthView.vue`
- 主页面：`frontend/src/views/EvaluationView.vue`
- 功能骨架：
    - 输入问题
    - 按已启用且已配置 API Key 的模型配置选择模型
    - 启用或关闭 LLM 评审开关
    - 展示多模型回答卡片
    - 展示耗时、输出长度、成本和评分条
    - 当系统内没有可用模型时，管理员可进入模型配置，普通用户会看到联系管理员提示
    - 支持公开和私有评测选择
- 前端展示增强：
    - 请求期间显示等待卡片、耗时计数和完成进度
    - 模型完成即展示，避免等待最慢模型后才统一呈现
    - 结果卡片根据模型数量自适应布局
    - 支持全局“思考模式”开关
    - `MarkdownRenderer` 支持 Markdown 回答渲染
    - `<think>...</think>` 内容折叠为“思考过程”
    - 侧边栏“历史任务”入口支持分页查看历史评测并加载详情
    - Element Plus 使用中文语言配置，分页容量后缀显示为 `/页`
    - 评分详情支持分页查看、发布和删除公开评论
    - 根据用户角色控制模型配置导航和页面访问
- 状态管理：`frontend/src/stores/evaluation.js`
- API 封装：`frontend/src/utils/api.js`

### 数据库与文档

- MySQL Docker Compose：`docker-compose.yml`
- 初始化 SQL：`docker/mysql/init/001_schema.sql`
- Alembic 基础配置：`backend/alembic.ini`
- 文档：
    - `docs/architecture.md`
    - `docs/database.md`
    - `docs/api.md`
    - `docs/open-source-reuse.md`
    - `docs/v2-development-plan.md`
    - `docs/v2-stage1-auth-rbac-design.md`

## 本地运行方式

推荐使用一键启动脚本：

```bash
./scripts/start-local.sh
```

脚本会检查 `.env`、启动 MySQL、准备后端虚拟环境和前端依赖、执行 Alembic 数据库迁移，并同时启动后端与前端开发服务。按 `Ctrl+C` 可停止本次启动的服务。

### 1. 启动 MySQL

```bash
docker compose up -d mysql
```

### 2. 启动后端

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

默认地址：

```text
http://localhost:8000
```

健康检查：

```text
http://localhost:8000/api/health
```

### 3. 启动前端

```bash
cd frontend
pnpm install
pnpm dev
```

默认地址：

```text
http://localhost:5173
```

## 环境变量

复制 `.env.example` 为 `.env` 后再按本地环境修改。后端配置固定读取项目根目录的 `.env`，从根目录或 `backend/` 目录启动都可以读取同一份配置。

重点变量：

```text
DATABASE_URL=mysql+aiomysql://multichateval:multichateval@localhost:3306/multichateval
BACKEND_CORS_ORIGINS=http://localhost:5173
DEEPSEEK_MODEL=deepseek-v4-flash
MINIMAX_MODEL=MiniMax-M2.5
ZHIPU_MODEL=glm-4.7
MODEL_REQUEST_TIMEOUT=90
```

真实模型 API Key 不应提交到 Git。

## 当前实现状态与后续路线

### 已跑通主流程

当前已实现：

- 用户提问 → 选择多个模型 → 后端并发调用真实 OpenAI-compatible 模型 → 模型级渐进展示 → 规则评分与可选 LLM Judge → 前端对比展示。
- 模型配置从数据库动态读取。
- 模型耗时、输出 token、成本估算、错误状态、规则评分和可选 LLM Judge 结果会返回给前端。
- `<think>...</think>` 和 `reasoning_content` 会折叠展示为“思考过程”。

### 已实现：持久化与历史任务

- 将评测任务写入 `evaluation_tasks`。
- 将模型回答写入 `model_responses`。
- 将规则评分写入 `evaluation_results`。
- 将 `GET /api/evaluation/tasks/{taskId}` 改为真实查询。
- 前端“历史任务”入口支持分页查看和详情加载。

### 评分增强

已实现：

- 相关性评分使用字符 n-gram 相似度、意图覆盖、回答聚焦度、显式要求对齐和离题惩罚，不使用旧的关键词交集主算法。
- 完整性、清晰度、格式和安全性已增加更细的规则与命中项明细；安全性使用危险输出控制、拒答质量、高风险领域谨慎性和隐私/凭据保护四类本地信号合成。
- LLM Judge 输出结构化 JSON，评分、理由和明细会持久化；有效 Judge 分以 40% 权重计入基础分。
- 点赞比例映射为反馈分，并以 10% 权重计入最终分；没有反馈时最终分保持基础分。

待做：

- 增加语言一致性评分。

### LLM Judge

已实现：

- 使用独立评审 Prompt，并将候选回答视为不可信输入。
- 要求评审模型输出结构化 JSON。
- 解析评分、优点、缺点、改进建议和推荐理由。
- 将有效 LLM Judge 分以 40% 权重纳入基础分。

### 用户反馈与推荐

已实现：

- 点赞、点踩按钮已接通反馈接口。
- 点赞和点踩会真实写入或取消写入 `user_feedback`。
- demo-v1 旧匿名数据继续归属 `user_id = 0`；新反馈和评论归属当前登录用户。
- 评测页和历史任务详情页都可以提交点赞或点踩。
- 点赞/点踩变化会重算并持久化最终分。
- 评分详情弹窗会展示维度分数、权重、命中项明细、当前反馈状态和评分公式。
- 支持分页查看、发布和硬删除公开评论；同一用户对同一回答的评论数量不受限制。

待做：

- 增加反馈统计和模型推荐。

### v2 后续路线

- 用户注册、登录、会话和真实用户反馈归属。
- 反馈统计看板与基于历史质量、成本和偏好的模型推荐。
- 评论审核、举报和管理能力。
- 评测结果导出、分享与可复现报告。
- 批量评测数据集、回归对比和自定义评分权重。
- 服务健康监控、调用失败分析和成本趋势统计。

## 当前评分公式

当前基础分和最终分：

```text
BaseFinal = RuleFinal
BaseFinal = 0.60 × RuleFinal + 0.40 × JudgeFinal  # Judge 有效时
FeedbackScore = 10 × LikeCount / (LikeCount + DislikeCount)
Final = BaseFinal                                 # 暂无反馈
Final = 0.90 × BaseFinal + 0.10 × FeedbackScore  # 已有反馈
```

评论不参与评分。新评论归属当前登录用户，只有作者可以删除；旧匿名评论继续归属 `user_id = 0`。

## 开源项目参考

### OpenCompass

适合作为评测体系和答辩相关工作的参考，但不建议直接作为主业务底座。原因是 OpenCompass 更偏离线 benchmark，而本项目是面向用户的在线多模型对话评测平台。

### promptfoo

适合参考 LLM 输出测试、规则评分和 LLM-as-a-Judge 的配置思路。

### FastChat

适合参考多模型聊天、模型对比和用户偏好反馈思路。

## 开发约定

- 全程使用中文交流、中文注释和中文文档。
- 前端使用 JavaScript，不使用 TypeScript。
- 前端包管理优先使用 pnpm。
- 后端尽量补充类型标注。
- 不要把 API Key、数据库密码等真实敏感信息提交到仓库。
- 文件修改前需要确认用户授权。
- 不要随意删除用户已有文件。
- 不要将 `.env`、`node_modules`、虚拟环境、构建产物提交到 Git。
- 当前只做模型级渐进返回，不做逐字 token 流式输出。

## 文档先行约定

- 每次做功能更新前，先确认会影响哪些文档；如果需求、接口、数据结构或交互行为不清楚，先补充或更新设计/说明文档，再改代码。
- 每次完成后端接口、前端功能、数据库结构、配置项、评分规则或模型调用逻辑变更时，必须同步更新对应文档。
- 功能实现状态统一维护在 `docs/system-features-status.md`；当功能从“未实现”变为“部分实现”或“已实现”时，需要同步更新该文档。
- API 请求/响应变化需要同步更新 `docs/api.md`。
- 数据表、字段、关系或持久化流程变化需要同步更新 `docs/database.md`。
- 架构、模块边界、主流程或模型调用链路变化需要同步更新 `docs/architecture.md`。
- README 只保留项目概览、运行方式和重要入口；详细实现状态优先写入 `docs/` 下的专题文档。
- 交付前需要检查本次代码变更和文档是否一致（包含`README.md`和`AGENTS.md`两个核心文档）；如果暂时无法更新文档，必须在回复中说明原因和后续补文档位置。

## 后续 AI 接手建议

新的 AI 或开发者接手时，建议按以下顺序阅读：

1. `README.md`
2. `docs/architecture.md`
3. `docs/database.md`
4. `docs/api.md`
5. `docs/system-features-status.md`
6. `backend/app/services/evaluation_service.py`
7. `frontend/src/views/EvaluationView.vue`

优先推进的任务是：

1. 安装依赖并启动前后端。
2. 确认前端能调用后端真实模型接口。
3. 确认模型级渐进展示和全局思考模式行为正常。
4. 验证评分结果、点赞/点踩和公开评论均正确持久化到 MySQL。
5. 增加反馈统计和模型推荐。
6. 验证公开任务跨用户可见、私有任务仅创建者可见。
