# MultiChatEval

面向多模型问答的对话质量评估系统。

本项目用于课程设计，目标不是判断“哪个 AI 一定最好”，而是通过多模型并发回答、客观指标、规则评分、可选 LLM 评审和用户反馈，帮助用户结构化比较不同模型的回答质量。

## 技术栈

- 后端：Python、FastAPI、SQLAlchemy 2.0、Alembic、Pydantic Settings、pytest
- 前端：Vue 3、JavaScript、Vite、Pinia、Vue Router、Axios、Element Plus、ECharts、Markdown-it、DOMPurify
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

首次运行前可以复制环境变量模板：

```bash
cp .env.example .env
```

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

## 前端展示能力

当前前端已经支持：

- 按实际模型名称展示模型选择项和结果卡片，例如 `deepseek-v4-flash`、`MiniMax-M2.5`、`glm-4.7`。
- 根据模型数量自适应卡片布局：单模型占满整行，双模型并排，三模型三列展示。
- 模型请求期间展示等待卡片、等待秒数和占位动画，避免用户误以为页面卡住。
- 回答内容使用 Markdown 渲染，支持标题、列表、代码块、表格、引用和链接。
- 使用 DOMPurify 清洗渲染后的 HTML，降低 Markdown 内容带来的 XSS 风险。
- 自动识别 `<think>...</think>` 内容，并折叠到“思考过程”面板中，正式回答单独展示。

## 真实模型配置

后端当前已支持 OpenAI-compatible 的 `/chat/completions` 调用。当前默认展示并调用 DeepSeek、MiniMax、Zhipu 三个模型。

```text
DEEPSEEK_API_KEY=
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash

MINIMAX_API_KEY=
MINIMAX_BASE_URL=https://api.minimaxi.com/v1
MINIMAX_MODEL=MiniMax-M2.5

ZHIPU_API_KEY=
ZHIPU_BASE_URL=https://open.bigmodel.cn/api/paas/v4
ZHIPU_MODEL=glm-4.7
```

如果没有配置对应 API Key，前端会展示“调用失败”卡片，并显示缺少配置的原因。

如果评测问题较长或模型响应较慢，可以在 `.env` 中调大：

```text
MODEL_REQUEST_TIMEOUT=90
```

前端请求超时时间已设置为 120 秒，避免后端仍在等待模型返回时前端过早中断。

GLM-4.7 默认会启用思考模式，可能导致简单问题也响应很慢。项目里已对 Zhipu/GLM 请求默认传入：

```json
{
  "thinking": {
    "type": "disabled"
  }
}
```

这样可以减少 reasoning token 和等待时间，更适合当前课程项目的多模型快速对比场景。
