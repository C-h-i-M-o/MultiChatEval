# AGENT.md

## 项目概览

MultiChatEval 是一个“面向多模型问答的对话质量评估系统”。项目目标不是绝对判断哪个 AI 回答最好，而是通过多模型并发回答、客观指标、规则评分、可选 LLM 评审和用户反馈，帮助用户结构化比较不同模型回答。

一句话定位：

> 多模型对话质量评估与智能推荐平台。

## 当前技术栈

- 后端：Python、FastAPI、SQLAlchemy 2.0、Alembic、Pydantic Settings、pytest
- 前端：Vue 3、JavaScript、Vite、Pinia、Vue Router、Axios、Element Plus、ECharts
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
  chat.md         项目早期设想对话
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
- API 路由：
  - `GET /api/health`
  - `POST /api/evaluation/tasks`
  - `GET /api/evaluation/tasks/{taskId}`
  - `POST /api/evaluation/responses/{responseId}/feedback`
- 模型适配器接口：`backend/app/adapters/base.py`
- OpenAI-compatible 真实调用适配器：`backend/app/adapters/openai_compatible.py`
- 规则评分器：`backend/app/services/rule_evaluator.py`
- 当前评测服务仍使用模拟回答，尚未接入真实模型 API。

### 前端

- Vue 3 + JavaScript + Vite 基础项目
- 主页面：`frontend/src/views/EvaluationWorkspace.vue`
- 功能骨架：
  - 输入问题
  - 选择模型
  - 切换快速/标准/深度评测模式
  - 启用或关闭 LLM 评审开关
  - 展示多模型回答卡片
  - 展示耗时、输出长度、成本和评分条
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

## 本地运行方式

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
OPENAI_COMPATIBLE_API_KEY=
OPENAI_COMPATIBLE_BASE_URL=
OPENAI_COMPATIBLE_MODEL=
```

真实模型 API Key 不应提交到 Git。

## MVP 开发路线

### 第一阶段：跑通主流程

目标：

```text
用户提问 → 创建评测任务 → 多模型回答 → 规则评分 → 前端展示
```

待做：

- 将当前模拟回答替换为真实模型适配器调用。
- 将任务、回答、评分写入 MySQL。
- 前端从真实任务接口读取结果。

### 第二阶段：客观指标

待做：

- 记录每个模型响应时间。
- 统计输入和输出 token。
- 按模型价格估算成本。
- 保存错误状态和错误信息。

### 第三阶段：规则评分

待做：

- 完善相关性评分。
- 完善完整性评分。
- 完善清晰度评分。
- 增加语言一致性评分。
- 增加格式符合度评分。

### 第四阶段：LLM Judge

待做：

- 设计评审 Prompt。
- 要求评审模型输出 JSON。
- 解析评分、优点、缺点和推荐理由。
- 将 LLM 评审分纳入综合评分。

### 第五阶段：用户反馈

待做：

- 点赞、点踩、采纳、收藏。
- 保存用户反馈。
- 在评分详情中展示用户反馈影响。

## 推荐的评分思路

综合分建议：

```text
FinalScore =
  0.25 × 客观性能分
+ 0.25 × 规则评分
+ 0.40 × LLM 评审分
+ 0.10 × 用户反馈分
```

第一版可以先只使用规则评分，等真实模型接入稳定后再加入 LLM Judge。

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
- 第一版不要做流式输出，先保证完整主流程稳定。

## 后续 AI 接手建议

新的 AI 或开发者接手时，建议按以下顺序阅读：

1. `README.md`
2. `chat.md`
3. `docs/architecture.md`
4. `docs/database.md`
5. `docs/api.md`
6. `backend/app/services/evaluation_service.py`
7. `frontend/src/views/EvaluationWorkspace.vue`

优先推进的任务是：

1. 安装依赖并启动前后端。
2. 确认前端能调用后端模拟接口。
3. 接入第一个真实模型供应商。
4. 将评测任务和模型回答持久化到 MySQL。
5. 完善规则评分与评分详情页面。
