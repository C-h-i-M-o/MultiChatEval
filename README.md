# MultiChatEval

面向多模型问答的对话质量评估系统。

本项目用于课程设计，目标不是判断“哪个 AI 一定最好”，而是通过多模型并发回答、客观指标、规则评分、可选 LLM 评审和用户反馈，帮助用户结构化比较不同模型的回答质量。

## 当前状态

当前分支正在开发 **v2**。阶段 1 的账号体系与权限控制已经完成：

- 开放注册、登录、退出和 HttpOnly Cookie JWT 登录态。
- 普通用户与管理员角色隔离，模型配置仅管理员可维护。
- 评测任务支持公开和私有模式。
- 任务、点赞/点踩和评论归属真实登录用户。
- 公开任务对所有登录用户可见，私有任务仅创建者可见。

demo-v1 的核心评测能力继续保留：

- 管理员模型配置与 API Key 管理。
- 多模型并发调用和模型级渐进展示。
- 本地规则评分与可选 LLM Judge。
- 点赞/点踩反馈计分、公开评论和历史任务查询。
- MySQL 持久化、Alembic 迁移和一键启动脚本。

反馈统计页面暂不对 demo-v1 用户展示；对应能力将在后续版本实现。

## 技术栈

- 后端：Python、FastAPI、SQLAlchemy 2.0、Alembic、Pydantic Settings、pytest
- 前端：Vue 3、JavaScript、Vite、Pinia、Vue Router、Axios、Element Plus、Markdown-it、DOMPurify、GSAP
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
- `docs/api.md`：后端接口说明。
- `docs/database.md`：数据库表结构说明。
- `docs/v2-development-plan.md`：v2 云端多用户版本的开发顺序、流程和验收标准。
- `docs/v2-stage1-auth-rbac-design.md`：阶段 1 账号、权限和任务可见性设计。

## 快速开始

推荐直接使用本地启动脚本：

```bash
./scripts/start-local.sh
```

脚本会自动检查 `.env`、启动 MySQL、准备后端虚拟环境、安装后端和前端依赖、执行 Alembic 数据库迁移，并同时启动后端与前端开发服务。按 `Ctrl+C` 可以停止本次启动的后端和前端进程。

运行前请确保已经安装并启动：

- Docker Desktop（包含 Docker Compose）。
- Python 3.11 或更高版本。
- Node.js 与 pnpm。
- macOS 自带的 `curl` 和 `lsof`。

脚本会按 `backend/pyproject.toml` 和 `frontend/pnpm-lock.yaml` 校验依赖，并在前后端真实可访问后才提示启动完成。

如果默认端口已被占用，脚本会自动向后寻找可用端口，并把实际后端地址同步给 Vite 代理。也可以通过 `BACKEND_PORT=8001 FRONTEND_PORT=5174 ./scripts/start-local.sh` 指定起始端口。

首次运行前可以复制环境变量模板：

```bash
cp .env.example .env
```

部署到非本地环境前，必须将 `.env` 中的 `JWT_SECRET_KEY` 改为足够长的随机值，并在 HTTPS 环境设置 `AUTH_COOKIE_SECURE=true`。

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
pnpm install --frozen-lockfile
pnpm dev
```

前端已在 `package.json` 中允许 `esbuild` 和 `vue-demi` 执行必要的依赖构建脚本。若本地升级 pnpm 后遇到 `ERR_PNPM_IGNORED_BUILDS`，请在 `frontend/` 下执行 `pnpm rebuild` 后再启动。

前端默认地址：

```text
http://localhost:5173
```

## 当前能力

当前版本已经跑通：

1. 用户注册或登录，并选择公开或私有评测。
2. 普通用户读取管理员已启用且已配置 API Key 的模型。
3. OpenAI-compatible 适配器并发调用真实模型。
4. 每个模型返回后立即以模型级渐进结果展示到前端。
5. 记录回答四类 Token、总 Token、分项费用、总费用和错误状态。
6. 执行规则评分，可选启用 LLM Judge，并展示评分条和评分详情。
7. 支持全局“思考模式”开关。
8. 将评测任务、模型回答、评分、点赞/点踩和公开评论按登录用户保存到 MySQL，并支持分页查看历史任务。
9. 点赞/点踩以 10% 权重计入最终分；没有反馈时保持基础分不变。
10. 历史任务详情会正确展示超时未完成状态，并在暂无回答时显示明确说明。

当前仍不做逐字 token 流式输出；`/api/evaluation/tasks/stream` 是模型级渐进返回，即一个模型完整回答完成后立刻展示。

v2 阶段 2/3 已提供管理员模型参数、四类计费配置、用户每日 Token 额度和用量展示。后续将继续推进语义分析、反馈统计、模型推荐和运行监控。

## 前端展示能力

当前前端已经支持：

- 使用多路由结构组织页面：`/login` 和 `/register` 为认证页面，`/` 为对比评测，`/models` 为管理员模型配置，`/users` 为管理员用户额度，`/history` 为历史任务。
- 普通用户不显示模型配置入口，管理员可以维护模型配置。
- 评测表单支持公开和私有模式，历史任务展示创建者与可见性。
- 按实际模型名称展示模型选择项和结果卡片，例如 `deepseek-v4-flash`、`MiniMax-M2.5`、`glm-4.7`。
- 对比评测使用平衡摘要网格：四个模型固定两行两列，五至九个模型自动平衡分行并铺满每一行；容器变窄时自动降为两列或单列。
- 模型请求期间展示等待卡片、等待秒数和占位动画；某个模型先完成时，会立即替换成真实回答卡片。
- 使用 GSAP 实现结果进入、等待卡替换、评分条和详情弹窗动画，并适配减少动态效果偏好。
- 全局“思考模式”开关会随评测请求发送给后端，不区分具体模型，也不提供思考程度选项。
- 回答内容使用 Markdown 渲染，支持标题、列表、代码块、表格、引用和链接。
- 使用 DOMPurify 清洗渲染后的 HTML，降低 Markdown 内容带来的 XSS 风险。
- 自动识别 `<think>...</think>` 内容，并折叠到“思考过程”面板中，正式回答单独展示。
- 侧边栏“历史任务”入口支持分页查看历史评测，回答以单列紧凑列表展示，并可加载完整回答和评分详情。
- Element Plus 使用中文语言配置，历史任务分页容量显示为 `10/页`、`20/页` 或 `50/页`。
- 回答摘要卡支持点赞、点踩和全文详情弹窗，反馈会真实写入或取消写入 `user_feedback`，并立即更新最终分。
- 回答卡先展示总费用，悬停或键盘聚焦总费用时展示四类 Token 与分项费用；移动端点击切换。
- 评测页展示北京时间当日 Token 已用、剩余和每日额度，额度耗尽时禁止创建新任务。
- 评分详情支持分页查看、发布和删除公开评论，评论独立保存在 `user_comments`，不参与评分。
- 历史任务时间按北京时间展示；`pending` 任务默认显示“进行中”，创建超过 120 秒后仍未完成才显示为“超时未完成”。
- 反馈统计占位路由仍保留给后续开发，但 demo-v1 侧边栏不展示该入口。
- 桌面端侧边栏固定在可视区域内，“默认流程”保持在侧栏底部；移动端恢复普通流式布局。

## 真实模型配置

后端当前已支持 OpenAI-compatible 的 `/chat/completions` 调用。系统不再自动创建内置模型记录；管理员可从 DeepSeek、MiniMax、GLM、Qwen、Xiaomi MiMo、OpenAI 预设或 OpenAI-compatible 空白模板创建配置，并自行填写 API Key、模型名和官方价格。

如果系统内没有任何已配置 API Key 的模型，管理员会看到配置入口，普通用户会看到联系管理员的提示。

首次创建管理员：

```bash
cd backend
source .venv/bin/activate
python -m app.scripts.create_admin --username admin
```

如果评测问题较长或模型响应较慢，可在管理员模型配置的“高级选项”中调整对应模型的请求超时。

规则评分使用轻量本地多信号评分，不依赖外部语义模型或下载。评分前会排除 `<think>...</think>` 思考内容，仅分析最终回答；原始回答仍会完整保存并在前端折叠展示思考过程。相关性会结合字符 n-gram 相似度、关键词覆盖、意图覆盖、回答聚焦度、显式要求对齐和离题惩罚计算；安全性会结合危险输出控制、拒答质量、高风险领域谨慎性和隐私/凭据保护计算。

普通 Axios API 请求超时时间为 120 秒。模型级渐进评测使用原生 `fetch` 持续读取 NDJSON，不设置 120 秒前端强制中断；历史任务以创建超过 120 秒作为“超时未完成”的展示阈值。

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

项目不传递思考程度参数。如果某个供应商不支持 `thinking` 字段，对应模型会在回答摘要卡中显示失败，不影响其他模型继续返回。

关闭思考模式时，后端确认发送的是嵌套字段 `thinking.type=disabled`，不是 `thinkingmode:disabled`。MiniMax 等部分 OpenAI-compatible 供应商即使收到该参数，也可能仍在返回内容中包含 `<think>` 或 reasoning 字段；前端会按当前规则折叠展示这些内容。
