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
7. 前端以卡片、表格和图表展示对比结果。
8. 用户提交点赞、点踩、采纳或评论反馈。

## 第一版边界

第一版先实现非流式请求和规则评分，不做实时逐字输出。这样可以降低并发、状态管理和评分时机的复杂度，优先保证完整主流程。
