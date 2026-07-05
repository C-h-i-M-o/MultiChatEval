# MultiChatEval 量化指标测试报告

测试时间：2026-07-05 17:40 CST  
优化复测：2026-07-05 17:59 CST  
批处理补测：2026-07-06 CST  
真实 UI 流式采样：2026-07-06 00:24 CST  
测试环境：macOS 26.3，M5，24GB；Node.js v24.16.0；pnpm 11.5.3；Python 3.13.9；MySQL 8.4 Docker 容器  
测试对象：React 主前端 `frontend/` + FastAPI 后端 `backend/` + MySQL 本地数据库  
本地服务：后端 `http://127.0.0.1:8001`，React 前端 `http://127.0.0.1:5175`

## 结论摘要

- React 前端构建通过，优化后 `frontend/dist` 总体积仍约 3.2 MB；最大 JS chunk 从 `antd-core` 1,006.89 kB 降到 `chart-vendor` 379.99 kB，Vite 大 chunk 警告已消失。
- 前端 Vitest 通过：8 个测试文件、49 个用例全部通过；新增 2 个流式批处理单测。
- 后端 pytest 当前结果为 151 passed / 6 warnings；此前 2 个 async 测试因缺少显式 `@pytest.mark.asyncio` 标记在仓库根目录全量运行时失败，现已修复。
- 3 模型并发流式评测总耗时 4.896s；同样 3 个模型分别串行调用合计 10.360s，本次样本节省约 52.7%。
- 4 模型并发流式评测总耗时 5.139s，首个模型增量事件约 0.453s，4 个模型均成功返回。
- LLM Judge 开启时，3 个候选回答各执行 3 次 Judge，整条链路总耗时 42.155s，3 个回答均进入 `scored` 状态。
- 登录态业务首页本地 dev 环境 FCP 约 356ms，DOM Content Loaded 约 320.5ms，首屏接口请求约 5.5-10.7ms。
- UI 流式采样中，首个回答卡片完成约 4.423s，期间观察到 116 条 DOM mutation；补充 React Profiler 采样后记录到 `ModelResponseCard` 129 次 commit、`MarkdownRenderer` 97 次 commit，Profiler 采样代码已注释保留。
- 前端已补充手动批处理：后端仍通过 NDJSON 返回 token/delta 级增量事件，前端用 `requestAnimationFrame` 合并同一帧内的高频事件再更新状态。单元测试中 100 个 `model_delta` 事件合并为 1 次状态应用，状态应用次数减少约 99%。
- 真实 UI 流式采样中，页面收到 213 次 `model_delta` 增量事件，React root commit 186 次，实际 commit 次数相对逐增量更新减少约 12.7%；采样窗口内 Long Task 为 0。

## 测试口径

本报告覆盖用户提出的全部指标方向，但有两点口径限制：

1. React 内部 render 次数和 commit 耗时需要在源码中接入 React Profiler 才能精确测量。报告初版先用 Chrome DevTools 的 DOM `MutationObserver` 和 Long Task API 记录页面更新压力；优化复测阶段已临时接入 React Profiler，采样后将相关测试代码注释保留。
2. 当前数据库只有 4 个启用且配置了 API Key 的模型，因此无法测 5 模型并发。本报告记录 3 模型和 4 模型并发结果。
3. 批处理量化数据来自前端单元测试，验证同一调度窗口内的高频 `model_delta` 事件会被合并为一次状态应用；真实浏览器中每帧合并数量会受网络分片、模型输出速度和主线程调度影响。
4. 真实 UI 流式采样使用浏览器页面内的 React DevTools hook 统计 root commit 次数，统计对象是整棵 React root，不等同于某个单独组件的 render 次数；同时用 `fetch` clone 统计 NDJSON 事件，不影响页面原始流消费。

## 前端性能

### 构建与包体积

测试命令：

```bash
cd frontend
pnpm build
du -sh dist
find dist -type f | wc -l
```

结果：

| 指标 | 优化前 | 优化后 | 变化 |
|---|---:|---:|---:|
| 构建结果 | 通过 | 通过 | 保持 |
| Vite 构建耗时 | 363ms | 249ms | -114ms |
| `dist/` 总体积 | 3.2 MB | 3.2 MB | 基本持平 |
| `dist/` 文件数 | 83 | 89 | +6 |
| assets 文件数 | 82 | 88 | +6 |
| JS 文件数 / 未压缩体积 | 19 / 1,817,781 B | 25 / 1,825,558 B | +6 / +7,777 B |
| CSS 文件数 / 未压缩体积 | 3 / 63,670 B | 3 / 63,670 B | 持平 |
| 字体文件数 / 未压缩体积 | 59 / 1,072,948 B | 59 / 1,072,948 B | 持平 |
| 图片文件数 / 未压缩体积 | 1 / 218,285 B | 1 / 218,285 B | 持平 |
| JS/CSS gzip 合计 | 596,033 B | 604,123 B | +8,090 B |

主要 chunk：

| 产物 | 优化前未压缩 / gzip | 优化后未压缩 / gzip | 变化 |
|---|---:|---:|---|
| 最大 JS chunk | `antd-core` 1,006,898 B / 316,070 B | `chart-vendor` 379,995 B / 108,010 B | 最大 chunk 降低约 62.3% |
| 最大 Ant Design chunk | `antd-core` 1,006,898 B / 316,070 B | `antd-button` 355,106 B / 118,840 B | Ant Design 最大 chunk 降低约 64.7% |
| `antd-core-*.js` | 1,006,898 B / 316,070 B | 212,210 B / 67,530 B | 核心包明显拆小 |
| `chart-vendor-*.js` | 379,987 B / 106,650 B | 379,995 B / 108,010 B | 基本持平 |
| `markdown-vendor-*.js` | 128,715 B / 54,982 B | 128,715 B / 54,982 B | 持平 |
| `vendor-*.js` | 151,950 B / 43,529 B | 151,953 B / 43,528 B | 基本持平 |

构建提示：

- 优化前 Vite 提示 `antd-core-*.js` 超过 500 KB。
- 优化后通过细分 Ant Design manual chunks，构建不再出现超过 500 KB 的 chunk 警告。
- 代价是 JS chunk 数从 19 个增加到 25 个，JS/CSS gzip 合计增加约 8.1 KB；收益是最大阻塞包显著变小，首屏和按路由缓存更容易分摊。

### 首屏启动速度

采样方式：Chrome DevTools 打开当前全栈 Vite dev server，读取 Navigation Timing、Paint Timing、Resource Timing。  
注意：该结果代表本地 dev server + `/api` 代理环境，不等同于生产 CDN 环境。

登录页：

| 指标 | 结果 |
|---|---:|
| DOM Content Loaded | 368.4ms |
| Load Event End | 370.5ms |
| FCP | 408ms |
| LCP | 1232ms |
| CLS | 0 |
| Resource Count | 55 |

生产预览登录页：

采样方式：`cd frontend && pnpm preview --host 127.0.0.1 --port 4175 --strictPort`，打开 `http://127.0.0.1:4175/login`。该结果来自生产构建静态资源，不包含 Vite dev client 和 HMR。

| 指标 | dev 登录页 | 生产预览登录页 | 变化 |
|---|---:|---:|---:|
| DOM Content Loaded | 368.4ms | 72.7ms | -295.7ms |
| Load Event End | 370.5ms | 72.8ms | -297.7ms |
| FCP | 408ms | 108ms | -300ms |
| Resource Count | 55 | 17 | -38 |
| 最大 JS 资源 | `antd.js` 约 10.67 MB dev 资源 | `antd-button` 117.3 kB gzip / 355.1 kB decoded | 生产构建资源显著压缩 |

已登录业务首页：

| 指标 | 结果 |
|---|---:|
| DOM Content Loaded | 320.5ms |
| Load Event End | 323ms |
| FCP | 356ms |
| CLS | 0 |
| Resource Count | 51 |
| `/api/auth/me` | 5.5ms / 10.2ms |
| `/api/models/available` | 8.9ms / 10.7ms |
| `/api/token-usage/me/today` | 7.6ms / 9.2ms |

已登录业务首页 dev 资源中，体积最高的是 Ant Design、Ant Design Icons、React Router、Markdown/KaTeX 和 GSAP 相关资源。生产构建优化前 `antd-core` 是最大包体；优化后 Ant Design 被拆成 `antd-button`、`antd-core`、`antd-display`、`antd-table`、`antd-feedback`、`antd-controls`、`antd-input` 等更细 chunk。

## 流式体验

### 3 模型并发流式评测

测试 payload：

```json
{
  "prompt": "请用一句中文回答：什么是前端首屏性能？",
  "modelIds": [1, 2, 3],
  "enableJudge": false,
  "judgeModelId": null,
  "enableThinking": false,
  "visibility": "private"
}
```

结果：

| 指标 | 结果 |
|---|---:|
| HTTP 状态 | 200 |
| 总耗时 | 4.896s |
| 首个事件 | 0.012s |
| 首个完整模型响应 | 1.081s |
| NDJSON 行数 | 59 |
| `model_delta` 事件数 | 51 |
| `model_response` 事件数 | 3 |
| `task_completed` 事件数 | 1 |

模型响应：

| 模型配置 ID | 状态 | 后端记录 latency | 输出 token | 评分状态 |
|---:|---|---:|---:|---|
| 1 | success | 1034ms | 35 | judge_disabled |
| 3 | success | 3207ms | 36 | judge_disabled |
| 2 | success | 4836ms | 0 | judge_disabled |

### 4 模型并发流式评测

| 指标 | 结果 |
|---|---:|
| HTTP 状态 | 200 |
| 总耗时 | 5.139s |
| 首个事件 | 0.011s |
| 首个模型增量 | 0.453s |
| 首个完整模型响应 | 1.089s |
| NDJSON 行数 | 69 |
| `model_delta` 事件数 | 59 |
| `model_response` 事件数 | 4 |
| `task_completed` 事件数 | 1 |

模型响应：

| 模型配置 ID | 状态 | 后端记录 latency | 输出 token | 评分状态 |
|---:|---|---:|---:|---|
| 4 | success | 994ms | 32 | judge_disabled |
| 1 | success | 1262ms | 28 | judge_disabled |
| 3 | success | 3108ms | 34 | judge_disabled |
| 2 | success | 5084ms | 0 | judge_disabled |

## 并发能力

同一短提示词下，对模型 1、2、3 分别单独流式调用，作为串行基线：

| 模型配置 ID | 单模型总耗时 | 后端记录 latency | 输出 token |
|---:|---:|---:|---:|
| 1 | 1.405s | 1359ms | 35 |
| 2 | 5.887s | 5855ms | 0 |
| 3 | 3.068s | 3027ms | 27 |

对比：

| 指标 | 结果 |
|---|---:|
| 单模型串行合计 | 10.360s |
| 3 模型并发总耗时 | 4.896s |
| 本次样本耗时节省 | 52.7% |

简历可用表述建议：

> 实现多模型并发调用与 NDJSON 流式返回，在本地短提示词样本中，3 模型并发总耗时 4.896s，相比串行调用 10.360s 节省约 52.7% 等待时间。

## 渲染稳定性

采样方式：在已登录评测页关闭 LLM Judge，使用 UI 发起短问题评测；通过 `MutationObserver` 观察主内容区域 DOM 更新，通过 Long Task API 观察页面长任务。

| 指标 | 结果 |
|---|---:|
| 首个回答卡片完成 | 4.423s |
| 流式请求网络耗时 | 4.385s |
| Mutation records | 116 |
| ChildList mutations | 93 |
| CharacterData mutations | 23 |
| Added nodes | 196 |
| 首次 DOM mutation | 23.5ms |
| 流式采样窗口内新增长任务 | 0 |
| 页面历史长任务 | 1 条，157ms |

说明：

- DOM 更新次数可用于证明流式输出过程中页面存在高频增量更新，但不是 React 内部 render 次数。
- 已补充一次临时 React Profiler 采样，采样后将 Profiler 代码注释保留在 `frontend/src/pages/EvaluationPage.tsx`、`frontend/src/components/ModelResponseCard.tsx` 和 `frontend/src/utils/profilerMetrics.ts`，默认不参与运行。

### React Profiler 采样

采样方式：临时使用 React `<Profiler>` 包裹 `EvaluationPage.response-grid`、`ModelResponseCard`、`MarkdownRenderer`，采样结果写入 `window.__MCE_PROFILER_METRICS__`。采样后已将相关代码注释保留，避免影响常规运行。

本次 Profiler 采样同样使用 3 模型、关闭 LLM Judge 的短问题流式评测：

| 指标 | 结果 |
|---|---:|
| UI 评测总耗时 | 4.809s |
| 流式请求网络耗时 | 4.642s |
| 成功模型数 | 3 |
| Profiler 样本数 | 273 |

| Profiler ID | commit 数 | mount | update | nested update | total actualDuration | max actualDuration | commit 窗口 |
|---|---:|---:|---:|---:|---:|---:|---:|
| `EvaluationPage.response-grid` | 47 | 1 | 40 | 6 | 330.1ms | 26.0ms | 4692.7ms |
| `ModelResponseCard` | 129 | 3 | 120 | 6 | 330.0ms | 13.0ms | 4692.7ms |
| `MarkdownRenderer` | 97 | 3 | 94 | 0 | 53.2ms | 8.6ms | 3707.1ms |

结论：流式阶段主要 commit 压力集中在回答卡片和响应网格；Markdown 渲染本次样本总 actualDuration 约 53.2ms，单次最大约 8.6ms，没有观察到单次 Markdown commit 超过 16ms 的明显卡顿点。

### 高频 token 更新批处理

实现口径：

- 后端 `/api/evaluation/tasks/stream` 保持 NDJSON 增量输出，模型适配器收到增量内容后发送 `model_delta`。
- 前端不再每收到一条 `model_delta` 就立即 `setTaskState`，而是先进入本地队列。
- 浏览器环境下使用 `requestAnimationFrame` 在同一帧内批量 flush；非浏览器测试环境使用 16ms `setTimeout` 兜底。
- flush 时通过 `mergeStreamEvents` 顺序合并事件，保证回答文本顺序不乱。

新增单元测试：

| 测试项 | 样本 | 结果 |
|---|---:|---:|
| 批量合并后回答顺序 | 3 个连续 `model_delta` | 合并为 `第一段` |
| 高频 token 更新批处理 | 100 个连续 `model_delta` | 1 次调度，1 次状态应用 |
| 状态应用次数下降 | 100 次逐条更新基线 vs 1 次批处理 | 约 -99% |

说明：该数据证明的是前端状态更新层面的批处理能力。后端仍然可以持续返回 token/delta 级增量，用户侧也仍能看到渐进输出；优化点在于把同一帧内的高频增量合并后再触发 React 状态更新，降低流式长回答期间的 commit 压力。

### 真实 UI 流式评测采样

采样方式：复用已登录浏览器页面，在点击“开始评测”前注入两类观测：

- 用 `fetch` monkeypatch 对 `/api/evaluation/tasks/stream` 响应做 `clone()`，解析 NDJSON 行并统计 `model_delta`。
- 用 `window.__REACT_DEVTOOLS_GLOBAL_HOOK__.onCommitFiberRoot` 统计 React root commit 次数。
- 用 `MutationObserver` 和 Long Task API 记录 DOM 更新与主线程长任务。

测试 prompt：

```text
请用两句话解释：前端流式渲染为什么需要批处理？
```

结果：

| 指标 | 结果 |
|---|---:|
| 总采样窗口 | 14.387s |
| 流式接口完成时间 | 13.386s |
| NDJSON 行数 | 219 |
| `model_delta` 事件数 | 213 |
| `model_answer_completed` 事件数 | 2 |
| `model_response` 事件数 | 2 |
| `task_completed` 事件数 | 1 |
| 首个 NDJSON 事件 | 859.7ms |
| 首个 `model_delta` | 1,457.7ms |
| delta 字符总量 | 567 |
| React root commit 次数 | 186 |
| 相对逐 `model_delta` 更新的 commit 减少比例 | 约 12.7% |
| 平均每次 React commit 承载 `model_delta` | 1.15 |
| DOM mutation records | 508 |
| CharacterData mutations | 42 |
| ChildList mutations | 466 |
| Added nodes | 1,625 |
| Long Task 数量 | 0 |

模型维度：

| 模型配置 ID | 模型 | `model_delta` 次数 | delta 字符数 | outputTokens | 后端 latency | 状态 |
|---:|---|---:|---:|---:|---:|---|
| 1 | deepseek-v4-flash | 71 | 121 | 71 | 1,534ms | success |
| 2 | MiniMax-M2.7 | 142 | 446 | 0 | 12,436ms | success |

结论：真实模型输出并不是所有增量都挤在同一帧内，因此实际压缩率低于单元测试的极端高频场景。该次样本中 213 次 token/delta 级增量对应 186 次 React root commit，减少约 12.7% 的 commit 触发，同时没有产生 Long Task，说明批处理没有牺牲渐进展示，也没有观察到主线程明显卡顿。

## 后端接口

使用临时普通用户注册并携带 Cookie 访问接口。

| 接口 | HTTP 状态 | 耗时 |
|---|---:|---:|
| `POST /api/auth/register` | 201 | 93.647ms |
| `GET /api/auth/me` | 200 | 2.643ms |
| `GET /api/models/available` | 200 | 6.962ms |
| `GET /api/evaluation/tasks?page=1&pageSize=10` | 200 | 7.599ms |
| `GET /api/feedback-stats/me?range=7d&page=1&pageSize=10` | 200 | 12.870ms |
| `GET /api/admin/users` 普通用户访问 | 403 | 3.158ms |

未登录访问：

| 接口 | HTTP 状态 | 耗时 |
|---|---:|---:|
| `GET /api/health` | 200 | 0.888ms |
| `GET /api/auth/me` | 401 | 1.415ms |
| `GET /api/models/available` | 401 | 1.183ms |

历史分页：

| pageSize | HTTP 状态 | 耗时 |
|---:|---:|---:|
| 10 | 200 | 7.021ms |
| 20 | 200 | 11.975ms |
| 50 | 200 | 6.770ms |
| 100 | 200 | 7.697ms |

## 评分链路

### 规则评分

本地规则评分器对同一 prompt/answer 运行 200 次：

| 指标 | 结果 |
|---|---:|
| 平均耗时 | 0.1726ms |
| P50 | 0.1680ms |
| P95 | 0.2080ms |
| 最小值 | 0.1588ms |
| 最大值 | 0.2672ms |
| 样本最终分 | 8.03 |

### LLM Judge

3 个候选模型 + 1 个空闲 Judge 模型，Judge 开启：

| 指标 | 结果 |
|---|---:|
| HTTP 状态 | 200 |
| 总耗时 | 42.155s |
| 首个 `model_response` | 22.182s |
| 完成事件 | 42.151s |
| 候选回答数 | 3 |
| 每个回答 Judge 次数 | 3 |
| 总 Judge runs | 9 |

Judge 结果：

| 模型配置 ID | 状态 | 回答 latency | 评分状态 | Judge runs | Judge Final | 分差 |
|---:|---|---:|---|---:|---:|---:|
| 1 | success | 948ms | scored | 3 | 9.17 | 0.5 |
| 2 | success | 4581ms | scored | 3 | 8.83 | 0.5 |
| 3 | success | 27468ms | scored | 3 | 9.50 | 1.0 |

说明：LLM Judge 是当前链路中最耗时的部分，适合在简历和面试中说明为“可选增强评分”，而不是默认低延迟路径。

## 数据闭环

当前本地数据库统计：

| 表/指标 | 数量 |
|---|---:|
| users | 24+，采样后新增临时测试用户 |
| model_providers | 7 |
| model_configs | 4 |
| 启用且带 Key 的模型配置 | 4 |
| evaluation_tasks | 49 |
| model_responses | 102 |
| evaluation_results | 102 |
| user_feedback | 7 |
| user_comments | 4 |
| 模型回答评分覆盖率 | 100.0% |
| 模型回答成功率 | 99.02% |
| 历史 `model_failed` 数 | 1 |

本次采样验证了以下写入链路：

- 注册临时用户并设置 HttpOnly Cookie。
- 读取可用模型配置。
- 创建私有评测任务。
- 写入模型回答。
- 写入规则评分或 Judge 评分结果。
- 更新今日 Token 用量。
- 历史任务列表可查询新增任务。

## 权限安全

| 场景 | 结果 |
|---|---|
| 未登录访问 `/api/auth/me` | 401 |
| 未登录访问 `/api/models/available` | 401 |
| 普通用户访问 `/api/admin/users` | 403 |
| 注册成功后 Cookie 登录态恢复 | 通过 |
| 业务首页展示普通用户身份和今日 Token | 通过 |
| 私有评测任务创建 | 通过 |

## 工程质量

### 前端测试

```bash
cd frontend
pnpm test
```

结果：

| 指标 | 结果 |
|---|---:|
| 测试文件 | 8 passed |
| 测试用例 | 49 passed |
| Vitest duration | 745ms |
| 命令总耗时 | 约 1s |

新增覆盖：

- `mergeStreamEvents` 批量合并多个流式事件，并保持增量文本顺序。
- `createStreamEventBatcher` 将同一调度窗口内的 100 个 `model_delta` 合并成 1 次状态应用。

### 后端测试

```bash
backend/.venv/bin/pytest -q
```

结果：

| 指标 | 结果 |
|---|---:|
| passed | 151 |
| failed | 0 |
| warnings | 6 |
| pytest duration | 0.86s |

修复说明：

此前失败项：

- `backend/tests/test_feedback_stats_service.py::test_personal_stats_separates_owned_tasks_from_own_interactions`
- `backend/tests/test_token_quota_service.py::test_explicit_zero_daily_limit_is_not_replaced_by_default`

根因是从仓库根目录运行 `backend/.venv/bin/pytest -q` 时，pytest rootdir 会落在项目根目录，未加载 `backend/pyproject.toml` 中的 `asyncio_mode = "auto"`，`pytest-asyncio` 使用 strict 模式；这两个裸 `async def` 测试没有显式 `@pytest.mark.asyncio`，因此失败。当前已按仓库其他 async 测试的写法补充标记，完整后端测试恢复通过。

### 前端控制台

Chrome DevTools 当前页面采集到：

| 项目 | 优化前 | 优化后 |
|---|---|---|
| Ant Design Drawer | `width` 已废弃，建议改用 `size` | 已改为 `size="default"`，warning 消失 |
| 评测输入框 | 1 个表单字段缺少 `id` 或 `name` | 已补充 `id="evaluation-prompt"` 和 `name="evaluationPrompt"`，issue 消失 |
| 控制台 error/warn/issue | 3 条 | 0 条 |
| Performance API warning | 采样脚本触发 deprecated warning | 优化复测页面未发现控制台消息 |

## 简历可用量化表述

可以优先采用以下较稳妥的简历表达：

- 基于 FastAPI、React 19、TypeScript、MySQL 构建多模型对话质量评估平台，打通模型配置、并发评测、流式展示、规则评分、LLM Judge、用户反馈和历史统计闭环。
- 实现 OpenAI-compatible 多模型并发调用与 NDJSON token/delta 级流式响应，本地短提示词样本中 3 模型并发耗时 4.896s，相比串行调用 10.360s 节省约 52.7% 等待时间；4 模型并发首个增量约 0.453s。
- 针对流式长回答手动实现前端批处理，不再每收到一个增量事件就触发状态更新；单元测试中 100 个 `model_delta` 合并为 1 次状态应用，真实 UI 采样中 213 次 `model_delta` 对应 186 次 React root commit，实际 commit 触发减少约 12.7%，采样窗口 Long Task 为 0。
- 设计规则评分 + LLM Judge + 用户反馈的综合评分链路，规则评分本地 P95 约 0.208ms，LLM Judge 支持每个回答 3 次独立评审并持久化评分状态。
- 完成 HttpOnly Cookie 登录态、RBAC、公开/私有评测、管理员模型配置和用户反馈统计；本地采样中普通用户访问管理员接口返回 403，未登录业务接口返回 401。
- 优化 React/Vite 工程拆包与路由懒加载，生产构建 `dist` 约 3.2 MB，最大 JS chunk 从 1,006.89 kB 降到 379.99 kB，前端 49 个 Vitest 用例全部通过。

## 后续优化建议

1. 已接入并执行临时 React Profiler 采样，采样后代码已注释保留；后续如需长期监控，可抽成仅开发环境启用的工具开关。
2. 已处理 `antd-core` chunk 过大问题，最大 JS chunk 从 1,006.89 kB 降到 379.99 kB；后续若继续优化，可考虑按路由延迟加载图表和表格页面。
3. 将后端测试入口固定为 `cd backend && .venv/bin/pytest -q` 或保留显式 async 标记，避免不同 rootdir 下 pytest 配置加载差异导致误报。
4. 为 `/api/evaluation/tasks/stream` 增加固定 mock adapter 或本地 fake provider，避免性能回归测试依赖真实模型接口和外部网络波动。
5. 已用 `pnpm preview` 补充生产静态登录页首屏采样；完整生产链路仍建议后续增加后端反向代理或真实部署环境，再复测登录后业务页。
