# AGENT.md

## 项目概览

MultiChatEval 是一个“面向多模型问答的对话质量评估系统”。项目目标不是绝对判断哪个 AI 回答最好，而是通过多模型并发回答、客观指标、规则评分、可选 LLM 评审和用户反馈，帮助用户结构化比较不同模型回答。

一句话定位：

> 多模型对话质量评估与对比平台。

## 当前版本状态

当前 **v2 版本开发已经结束并冻结**。开放注册、HttpOnly Cookie JWT、普通用户/管理员 RBAC、真实用户数据归属、公开/私有评测、管理员模型配置、Token 额度、反馈统计等已实现能力继续保留；语义分析、模型推荐、运行监控等未完成的 v2 后续功能不再继续开发。

`main` 分支的 `demo-v1` 标签对应可发布基线。模型配置、多模型并发评测、模型级渐进展示、规则评分、可选 LLM Judge、历史任务、点赞/点踩反馈计分和公开评论均已形成可运行闭环。v2 的 `/feedback` 已实现角色分流：普通用户查看个人统计，管理员查看全局统计和互动明细。当前新的主要任务是在保留现有 Vue 前端的基础上，新建 React 技术栈前端并逐步重构同等业务能力。

## 当前技术栈

- 后端：Python、FastAPI、SQLAlchemy 2.0、Alembic、Pydantic Settings、pytest
- 现有前端：Vue 3、JavaScript、Vite、Pinia、Vue Router、Axios、Element Plus、Markdown-it、DOMPurify、GSAP
- 重构目标前端：React 19、TypeScript、Vite、React Router，独立目录 `frontend/` 并复用现有后端 API
- 数据库：MySQL 8
- 本地数据库环境：Docker Compose
- 包管理：前端优先使用 pnpm

注意：现有 Vue 前端使用 JavaScript，不使用 TypeScript。React 重构阶段的语言和工程约定以后续 React 设计文档为准。

## 目录结构

```text
MultiChatEval/
  backend/        FastAPI 后端服务
  frontend/       React 19 + TypeScript + Vite 前端应用，已接入认证、角色导航、基础布局和评测工作台
  vue-frontend/   原 Vue 3 + JavaScript 前端应用，React 重构期间继续保留为可运行基线
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
    - `GET /api/feedback-stats/me`
    - `GET /api/admin/feedback-stats`
- 模型适配器接口：`backend/app/adapters/base.py`
- OpenAI-compatible 真实调用适配器：`backend/app/adapters/openai_compatible.py`
- 规则评分器：`backend/app/services/rule_evaluator.py`
- 规则评分相关性使用轻量本地多信号评分，不依赖外部语义模型或下载。
- 规则评分会排除完整或未闭合的 `<think>` 思考内容，仅评价最终回答；原始回答仍完整保存和返回。
- 当前评测服务已接入真实模型 API，并从数据库中的模型配置动态读取可调用模型。
- 评测请求发送给模型前，会在用户原始问题前拼接系统内置提示词；数据库、历史任务和接口响应中的 `prompt` 仍保留用户原始问题。
- 系统不自动创建内置模型配置；管理员从供应商预设或 OpenAI-compatible 空白模板创建配置并维护 API Key。
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
- 登录页和注册页：`vue-frontend/src/views/AuthView.vue`
- 主页面：`vue-frontend/src/views/EvaluationView.vue`
- 功能骨架：
    - 输入问题
    - 按已启用且已配置 API Key 的模型配置选择模型
    - 启用或关闭 LLM 评审开关
    - 展示多模型回答摘要卡和全文详情弹窗
    - 展示耗时、输出长度、成本和评分条
    - 当系统内没有可用模型时，管理员可进入模型配置，普通用户会看到联系管理员提示
    - 支持公开和私有评测选择
- 前端展示增强：
    - 请求期间显示等待卡片、耗时计数和完成进度
    - 模型完成即展示，避免等待最慢模型后才统一呈现
    - 对比评测回答使用平衡摘要网格，四个模型固定两行两列，五至九个模型自动铺满每一行
    - 使用 GSAP 实现结果进入、等待卡替换、评分条和详情弹窗动画，并适配减少动态效果偏好
    - 支持全局“思考模式”开关
    - `MarkdownRenderer` 支持 Markdown 回答渲染
    - `<think>...</think>` 内容折叠为“思考过程”
- 侧边栏“历史任务”入口支持分页查看历史评测，回答使用单列紧凑列表并可加载详情
    - Element Plus 使用中文语言配置，分页容量后缀显示为 `/页`
    - 评分详情支持分页查看、发布和删除公开评论
	    - 根据用户角色控制模型配置导航和页面访问
	- 桌面端侧边栏固定在可视区域内，"默认流程"保持在侧栏底部；移动端恢复普通流式布局
- 状态管理：`vue-frontend/src/stores/evaluation.js`
- API 封装：`vue-frontend/src/utils/api.js`

### React 重构前端

- 独立目录：`frontend/`
- 技术栈：React 19、TypeScript、Vite、React Router、Vitest
- 阶段一已完成：
    - 独立依赖、测试、构建和开发服务命令
    - Vite `/api` 开发代理，默认代理到 FastAPI 后端
    - 类型化 API 客户端
    - 应用启动后调用 `GET /api/health`
    - 应用启动后调用 `GET /api/auth/me` 恢复 HttpOnly Cookie 登录态
- 阶段二已完成：
    - 登录、注册、退出和当前用户恢复
    - 受保护业务路由和公开认证路由
    - 普通用户与管理员导航可见性隔离
    - `/models` 与 `/users` 管理员入口保护
- 阶段三核心工作台已完成：
    - `/` 已迁移为 React 评测工作台
    - 支持模型列表、今日 Token、公开/私有评测、思考模式和 LLM 评审
    - 支持 `POST /api/evaluation/tasks/stream` 的模型级 NDJSON 渐进展示
    - 支持 Markdown 安全渲染、`<think>` 折叠、评分详情和点赞/点踩反馈
- 阶段四已完成：
    - `/history` 已迁移为 React 历史任务页面
    - 支持历史任务分页、详情加载、状态标记、超时提示和公开/私有标记
    - 历史详情支持点赞/点踩、完整回答、评分详情和公开评论分页、发布、删除
    - `/models` 已迁移为管理员模型配置页面，支持列表、新增、编辑、启用/禁用、删除和连接测试
    - `/users` 已迁移为管理员用户额度页面，支持查看今日 Token 用量并调整普通用户每日额度
    - `/feedback` 已迁移为按角色分流的反馈统计页面
- 阶段五已完成：
    - `docs/react-rewrite/acceptance.md` 记录自动验收、手工核心路径和 Vue 基线保留决策
    - `scripts/verify-react-rewrite.sh` 可执行后端测试、React 测试、React 构建、Vue 测试、Vue 构建和 `git diff --check`
    - `vue-frontend/` 本阶段继续保留，是否移除需后续单独决策

### 数据库与文档

- MySQL Docker Compose：`docker-compose.yml`
- 初始化 SQL：`docker/mysql/init/001_schema.sql`
- Alembic 基础配置：`backend/alembic.ini`
- 文档：
    - `docs/README.md`
    - `docs/architecture.md`
    - `docs/database.md`
    - `docs/api.md`
    - `docs/open-source-reuse.md`
    - `docs/react-rewrite/`
    - `docs/legacy-v2/`

## 本地运行方式

推荐使用一键启动脚本：

```bash
./scripts/start-local.sh
```

脚本会检查 `.env`、启动 MySQL、准备后端虚拟环境和 Vue 前端依赖、执行 Alembic 数据库迁移，并同时启动后端与 Vue 前端开发服务。按 `Ctrl+C` 可停止本次启动的服务。

React 重构版本使用：

```bash
./scripts/start-react-local.sh
```

该脚本会启动同一套 MySQL 和 FastAPI 后端，并启动 `frontend/`。默认 React 前端地址为 `http://127.0.0.1:5174`；如端口占用，会自动向后寻找可用端口。

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

### 3. 启动 Vue 前端基线

```bash
cd vue-frontend
pnpm install
pnpm dev
```

Vue 前端通过 `vue-frontend/pnpm-workspace.yaml` 的 `onlyBuiltDependencies` 允许 `esbuild`、`vue-demi` 执行必要构建脚本；依赖安装统一使用 `pnpm install --frozen-lockfile`。

默认地址：

```text
http://localhost:5173
```

## 环境变量

复制 `.env.example` 为 `.env` 后再按本地环境修改。后端配置固定读取项目根目录的 `.env`，从根目录或 `backend/` 目录启动都可以读取同一份配置。

重点变量：

```text
DATABASE_URL=mysql+aiomysql://multichateval:multichateval@localhost:3306/multichateval
BACKEND_CORS_ORIGINS=http://localhost:5173,http://localhost:5174,http://127.0.0.1:5173,http://127.0.0.1:5174
```

真实模型 API Key 不应提交到 Git。

## 当前实现状态与 React 重构方向

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

冻结说明：

- v2 不再继续增加语言一致性评分。

### LLM Judge

已实现：

- 使用独立评审 Prompt，并将候选回答视为不可信输入。
- 要求评审模型输出结构化 JSON。
- 解析评分、优点、缺点、改进建议和推荐理由。
- 将有效 LLM Judge 分以 40% 权重纳入基础分。

### 用户反馈

已实现：

- 点赞、点踩按钮已接通反馈接口。
- 点赞和点踩会真实写入或取消写入 `user_feedback`。
- demo-v1 旧匿名数据继续归属 `user_id = 0`；新反馈和评论归属当前登录用户。
- 评测页和历史任务详情页都可以提交点赞或点踩。
- 点赞/点踩变化会重算并持久化最终分。
- 全文详情弹窗会展示完整回答、维度分数、权重、命中项明细、当前反馈状态和评分公式。
- 支持分页查看、发布和硬删除公开评论；同一用户对同一回答的评论数量不受限制。
- 反馈统计页支持最近 7 天、30 天和全部历史范围，普通用户查看本人评测表现与本人互动，管理员查看全局模型统计、每日趋势和分页互动明细。

冻结说明：

- v2 不再继续增加模型推荐。

### v2 阶段 2/3 设计

- 管理员从 DeepSeek、MiniMax、GLM、Qwen、Xiaomi MiMo、OpenAI 预设或 OpenAI-compatible 空白模板创建模型配置，不再自动补齐三家内置记录。
- 模型配置支持温度、最大输出、超时、备注、币种及输入、输出、缓存命中、缓存创建四类每百万 Token 单价。
- 普通用户默认每日额度为 100,000 总 Token，管理员不限额；额度按北京时间自然日统计。
- 回答卡片先显示总费用，悬停或聚焦查看四项费用明细。

### v2 冻结与 React 重构方向

- v2 后续新功能开发到此结束。
- 未完成的模型推荐、语言一致性评分、评论审核、结果导出、批量评测和运行监控只作为历史规划保留，不再作为当前开发目标。
- 当前任务是保留现有 Vue 前端，另建 React 技术栈前端，优先迁移登录、评测工作台、历史任务、模型配置、用户额度和反馈统计等已实现页面。
- React 重构应复用现有后端 API、数据库结构和评分逻辑，不借重构扩大后端功能范围。

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
- 现有 Vue 前端使用 JavaScript，不使用 TypeScript。
- React 重构阶段需要先补充设计文档，明确目录、技术栈、路由、状态管理、API 封装和验收标准后再编码。
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
2. `docs/README.md`
3. `docs/architecture.md`
4. `docs/database.md`
5. `docs/api.md`
6. `docs/system-features-status.md`
7. `docs/react-rewrite/README.md`
8. `docs/react-rewrite/plan.md`
9. `docs/react-rewrite/architecture.md`
10. `backend/app/services/evaluation_service.py`
11. `vue-frontend/src/views/EvaluationView.vue`

优先推进的任务是：

1. 安装依赖并启动前后端。
2. 确认前端能调用后端真实模型接口。
3. 确认模型级渐进展示和全局思考模式行为正常。
4. 验证评分结果、点赞/点踩和公开评论均正确持久化到 MySQL。
5. 新建 React 前端框架并复用现有后端 API。
6. 按现有 Vue 页面逐步迁移 React 页面，迁移期间保持 Vue 前端可运行。
7. 验证公开任务跨用户可见、私有任务仅创建者可见。
8. React 重构收尾验收可运行 `./scripts/verify-react-rewrite.sh`。
