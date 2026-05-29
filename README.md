# MultiChatEval

面向多模型问答的对话质量评估系统。

本项目用于课程设计，目标不是判断“哪个 AI 一定最好”，而是通过多模型并发回答、客观指标、规则评分、可选 LLM 评审和用户反馈，帮助用户结构化比较不同模型的回答质量。

## 技术栈

- 后端：Python、FastAPI、SQLAlchemy 2.0、Alembic、Pydantic Settings、pytest
- 前端：Vue 3、JavaScript、Vite、Pinia、Vue Router、Axios、Element Plus、ECharts
- 数据库：MySQL 8
- 本地环境：Docker Compose

## 仓库结构

```text
MultiChatEval/
  backend/        FastAPI 后端服务
  frontend/       Vue 3 + JavaScript 前端应用
  docker/         MySQL 初始化脚本
  docs/           架构、接口、数据库和开源复用说明
  docker-compose.yml
  .env.example
```

## 快速开始

### 1. 启动数据库

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

后端默认地址：

```text
http://localhost:8000
```

### 3. 启动前端

```bash
cd frontend
pnpm install
pnpm dev
```

前端默认地址：

```text
http://localhost:5173
```

## MVP 范围

第一版先实现：

1. 用户输入问题并选择多个模型。
2. 后端创建评测任务。
3. 模型适配层并发获取多个回答。
4. 保存回答耗时、字数、成本估算和错误状态。
5. 执行规则评分。
6. 前端展示回答对比、评分明细和用户反馈入口。

第一版暂不做流式输出，等核心流程稳定后再加入 SSE 或 WebSocket。
