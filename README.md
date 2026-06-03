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
  scripts/        本地启动与维护脚本
  docker-compose.yml
  README.md
  .env.example
```

## 文档入口

- `docs/system-features-status.md`：系统功能、实现状态和后续优先级。
- `docs/architecture.md`：系统架构和核心流程。
- `docs/api.md`：后端接口草案。
- `docs/database.md`：数据库表结构说明。

## 快速开始

推荐直接使用本地启动脚本：

```bash
./scripts/start-local.sh
```

脚本会自动检查 `.env`、启动 MySQL、准备后端虚拟环境、安装后端和前端依赖、执行 Alembic 数据库迁移，并同时启动后端与前端开发服务。按 `Ctrl+C` 可以停止本次启动的后端和前端进程。

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

## 当前能力

当前版本已经跑通：

1. 用户输入问题并选择多个模型。
2. 后端从数据库读取已启用且已配置 API Key 的模型配置。
3. OpenAI-compatible 适配器并发调用真实模型。
4. 每个模型返回后立即以模型级渐进结果展示到前端。
5. 记录回答耗时、输出 token、成本估算和错误状态。
6. 执行规则评分并展示评分条和评分详情。
7. 支持全局“思考模式”开关。
8. 将评测任务、模型回答、规则评分和点赞/采纳反馈保存到 MySQL，并支持分页查看历史任务。

当前仍不做逐字 token 流式输出；`/api/evaluation/tasks/stream` 是模型级渐进返回，即一个模型完整回答完成后立刻展示。

尚未完成的重点能力包括：

- LLM Judge 实际评分。
- 反馈统计和模型推荐。

## 前端展示能力

当前前端已经支持：

- 使用多路由结构组织页面：`/` 为对比评测，`/models` 为模型配置，`/history` 为历史任务，`/feedback` 为反馈统计占位页。
- 按实际模型名称展示模型选择项和结果卡片，例如 `deepseek-v4-flash`、`MiniMax-M2.5`、`glm-4.7`。
- 根据模型数量自适应卡片布局：单模型占满整行，双模型并排，三模型三列展示。
- 模型请求期间展示等待卡片、等待秒数和占位动画；某个模型先完成时，会立即替换成真实回答卡片。
- 全局“思考模式”开关会随评测请求发送给后端，不区分具体模型，也不提供思考程度选项。
- 回答内容使用 Markdown 渲染，支持标题、列表、代码块、表格、引用和链接。
- 使用 DOMPurify 清洗渲染后的 HTML，降低 Markdown 内容带来的 XSS 风险。
- 自动识别 `<think>...</think>` 内容，并折叠到“思考过程”面板中，正式回答单独展示。
- 侧边栏“历史任务”入口支持分页查看历史评测，并加载完整回答和评分详情。
- 结果卡片支持点赞、采纳和详情弹窗，反馈会真实写入或取消写入 `user_feedback`。
- 历史任务时间按北京时间展示；`pending` 任务默认显示“进行中”，超过前端请求超时时间后仍未完成才显示为“超时未完成”。
- 侧边栏“反馈统计”入口已路由化，当前展示未实现占位说明。

## 真实模型配置

后端当前已支持 OpenAI-compatible 的 `/chat/completions` 调用。系统会内置 DeepSeek、MiniMax、GLM 三个模型配置，但不会从 `.env` 读取 API Key。新用户需要在前端“模型配置”页面填写自己的 API Key 后再使用。

```text
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash

MINIMAX_BASE_URL=https://api.minimaxi.com/v1
MINIMAX_MODEL=MiniMax-M2.5

ZHIPU_BASE_URL=https://open.bigmodel.cn/api/paas/v4
ZHIPU_MODEL=glm-4.7
```

如果系统内没有任何已配置 API Key 的模型，前端首页会提醒先进入“模型配置”页面填写 API Key。

如果评测问题较长或模型响应较慢，可以在 `.env` 中调大：

```text
MODEL_REQUEST_TIMEOUT=90
```

规则评分使用轻量本地多信号评分，不依赖外部语义模型或下载。相关性会结合字符 n-gram 相似度、关键词覆盖、意图覆盖、回答聚焦度、显式要求对齐和离题惩罚计算；安全性会结合危险输出控制、拒答质量、高风险领域谨慎性和隐私/凭据保护计算。

前端请求超时时间已设置为 120 秒，避免后端仍在等待模型返回时前端过早中断。

评测请求发送给模型前，后端会在用户原始问题前拼接系统内置提示词，用于统一直接作答、结构化表达、安全边界和格式遵循要求。数据库、历史记录和接口响应中的 `prompt` 仍保留用户原始问题。

评测请求会使用全局“思考模式”开关控制所有模型的 thinking 参数。关闭时统一传入：

```json
{
  "thinking": {
    "type": "disabled"
  }
}
```

开启时统一传入：

```json
{
  "thinking": {
    "type": "enabled"
  }
}
```

项目不传递思考程度参数。如果某个供应商不支持 `thinking` 字段，对应模型会在结果卡片中显示失败，不影响其他模型继续返回。

关闭思考模式时，后端确认发送的是嵌套字段 `thinking.type=disabled`，不是 `thinkingmode:disabled`。MiniMax 等部分 OpenAI-compatible 供应商即使收到该参数，也可能仍在返回内容中包含 `<think>` 或 reasoning 字段；前端会按当前规则折叠展示这些内容。
