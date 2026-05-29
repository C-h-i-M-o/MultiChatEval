# 系统架构说明

MultiChatEval 采用前后端分离架构：

```text
Vue 前端
  ↓
FastAPI API
  ↓
Evaluation Service
  ├── Model Adapter Layer
  ├── Objective Metrics Evaluator
  ├── Rule-based Evaluator
  ├── LLM Judge Evaluator
  └── User Feedback Collector
  ↓
MySQL
```

## 核心流程

1. 用户输入问题，选择多个模型。
2. 后端创建评测任务。
3. 模型适配层并发请求 DeepSeek、MiniMax、Zhipu。
4. 系统记录回答内容、响应时间、token 数、成本估算和错误状态。
5. 规则评分器计算相关性、完整性、清晰度、语言一致性和格式符合度。
6. 可选启用 LLM Judge，让评审模型输出结构化评分。
7. 前端以自适应卡片、Markdown 回答内容和评分条展示对比结果。
8. 用户提交点赞、点踩、采纳或评论反馈。

## 第一版边界

第一版先实现非流式请求和规则评分，不做实时逐字输出。这样可以降低并发、状态管理和评分时机的复杂度，优先保证完整主流程。

## 前端展示层

前端主界面位于 `frontend/src/views/EvaluationWorkspace.vue`，用于完成问题输入、模型选择、任务提交和结果对比。

当前展示层包含：

- 模型选择项直接显示具体模型名，避免用户只看到供应商名称。
- 结果卡片根据返回模型数量自适应布局。
- 模型调用期间展示等待卡片、耗时计数和占位动画。
- `MarkdownRenderer` 负责将模型输出渲染为安全的 HTML。
- `MarkdownRenderer` 会把 `<think>...</think>` 中的内容折叠为“思考过程”，让最终回答更清晰。

## 模型调用层

后端通过 `OpenAICompatibleClient` 统一调用兼容 `/chat/completions` 协议的模型服务。当前默认模型为：

- `deepseek-v4-flash`
- `MiniMax-M2.5`
- `glm-4.7`

GLM-4.7 默认可能开启思考模式，导致简单问题也消耗较多 reasoning token。项目已对 Zhipu/GLM 请求默认加入 `thinking.type=disabled`，用于课程项目中的快速多模型对比场景。
