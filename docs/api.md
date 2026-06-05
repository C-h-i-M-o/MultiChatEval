# API 草案

## 健康检查

```http
GET /api/health
```

响应：

```json
{
  "status": "ok"
}
```

## 创建评测任务

```http
POST /api/evaluation/tasks
```

请求：

```json
{
  "conversationId": 1,
  "prompt": "帮我解释什么是设计模式",
  "modelIds": [1, 2, 3],
  "enableJudge": false,
  "judgeModelId": null,
  "enableThinking": false
}
```

`modelIds` 使用 `model_configs.id`。如果不传，后端默认选择已启用的 DeepSeek 和 MiniMax；如果这两个模型不可用，则选择前两个已启用模型。

`enableJudge` 为 LLM 评审开关。关闭时后端只返回规则评分；开启时必须传入 `judgeModelId`，该字段同样使用 `model_configs.id`，并要求对应模型已启用且已配置 API Key。LLM Judge 会对每条成功模型回答做单回答 JSON 评分，失败回答不会触发 Judge。

`enableThinking` 为全局思考模式开关，不区分具体模型。关闭时，后端会对所有模型请求统一追加：

```json
{
  "thinking": {
    "type": "disabled"
  }
}
```

开启时，后端会对所有模型请求统一追加：

```json
{
  "thinking": {
    "type": "enabled"
  }
}
```

第一版不提供思考程度选项，也不会发送 `thinkingEffort` 或 `reasoning_effort`。

注意：关闭思考模式时后端确认传输的是 `thinking.type=disabled`，不是 `thinkingmode:disabled`。MiniMax 等部分 OpenAI-compatible 供应商即使收到该参数，也可能仍在 `content`、`reasoning_content` 或 `<think>...</think>` 中返回思考内容；这属于供应商接口行为，不代表前端开关未传递。

发送给模型前，后端会在用户原始问题前追加系统内置提示词。当前提示词要求模型直接作答，并明确要求：除专业名词和特殊情况外，使用中文回答问题。接口响应和数据库中的 `prompt` 仍保留用户原始问题。

响应：

```json
{
  "taskId": 1001,
  "status": "completed",
  "prompt": "帮我解释什么是设计模式",
  "createdAt": null,
  "completedAt": null,
  "responses": [
    {
      "id": 5001,
      "modelConfigId": 1,
      "modelName": "deepseek-v4-flash",
      "provider": "deepseek",
      "answer": "回答内容",
      "latencyMs": 856,
      "outputTokens": 120,
      "estimatedCost": 0,
      "status": "success",
      "score": {
        "relevance": 8,
        "completeness": 8,
        "clarity": 8,
        "format": 8,
        "safety": 10,
        "final": 8.64,
        "details": {
          "relevance": ["覆盖解释意图"],
          "completeness": ["回答长度处于有效区间"],
          "clarity": ["使用换行分隔内容"],
          "format": ["未指定格式，回答使用了可读结构"],
          "safety": ["未命中明显危险输出"]
        },
        "ruleFinal": 8.4,
        "judgeFinal": 9,
        "judgeComment": "优点：覆盖充分；缺点：示例略少；建议：可以补充示例。",
        "judgeDetails": {
          "strengths": ["覆盖充分"],
          "weaknesses": ["示例略少"],
          "recommendation": ["可以补充示例"],
          "dimensionScores": ["事实准确性：9", "问题覆盖度：9"]
        }
      }
    }
  ]
}
```

该接口会先写入 `evaluation_tasks`，等待所有模型调用完成后写入 `model_responses` 和 `evaluation_results`，再一次性返回完整结果。`responses[].id` 是 `model_responses.id`，`responses[].modelConfigId` 是 `model_configs.id`。

启用 LLM Judge 时，最终分计算为：

```text
final = 0.60 × ruleFinal + 0.40 × judgeFinal
```

如果未启用 Judge，或 Judge 超时、调用失败、返回非法 JSON，则 `judgeFinal` 为 `null`，`final` 等于 `ruleFinal`，失败原因会放入 `judgeComment`。

## 创建评测任务并渐进返回模型结果

```http
POST /api/evaluation/tasks/stream
```

请求字段与 `POST /api/evaluation/tasks` 一致。响应内容类型为 `application/x-ndjson`，每一行都是一个独立 JSON 事件。

任务开始事件：

```json
{
  "type": "task_started",
  "taskId": 1,
  "prompt": "帮我解释什么是设计模式",
  "modelIds": [1, 2, 3],
  "total": 3
}
```

单个模型完成事件：

```json
{
  "type": "model_response",
  "response": {
    "id": 5001,
    "modelConfigId": 1,
    "modelName": "deepseek-v4-flash",
    "provider": "deepseek",
    "answer": "回答内容",
    "latencyMs": 856,
    "outputTokens": 120,
    "estimatedCost": 0,
    "status": "success",
    "score": {
      "relevance": 8,
      "completeness": 8,
      "clarity": 8,
      "format": 8,
      "safety": 10,
      "final": 8.64,
      "ruleFinal": 8.4,
      "judgeFinal": 9,
      "judgeComment": "优点：覆盖充分；缺点：示例略少；建议：可以补充示例。",
      "judgeDetails": {
        "strengths": ["覆盖充分"],
        "weaknesses": ["示例略少"],
        "recommendation": ["可以补充示例"],
        "dimensionScores": ["事实准确性：9", "问题覆盖度：9"]
      }
    }
  }
}
```

任务完成事件：

```json
{
  "type": "task_completed",
  "task": {
    "taskId": 1,
    "status": "completed",
    "prompt": "帮我解释什么是设计模式",
    "createdAt": null,
    "completedAt": null,
    "responses": []
  }
}
```

如果某个模型调用失败，会以 `model_response` 事件返回该模型的失败状态，不会中断其他模型。

## 分页查询历史评测任务

```http
GET /api/evaluation/tasks?page=1&pageSize=10
```

响应：

```json
{
  "items": [
    {
      "taskId": 1001,
      "status": "completed",
      "prompt": "帮我解释什么是设计模式",
      "createdAt": "2026-06-03T12:00:00",
      "completedAt": "2026-06-03T12:00:12",
      "responseCount": 3
    }
  ],
  "total": 42,
  "page": 1,
  "pageSize": 10
}
```

`page` 从 1 开始，`pageSize` 默认 10，最大 100。列表按 `created_at desc, id desc` 排序。

## 查询模型配置

```http
GET /api/model-configs
```

响应：

```json
[
  {
    "id": 1,
    "providerName": "deepseek",
    "displayName": "deepseek-v4-flash",
    "modelName": "deepseek-v4-flash",
    "baseUrl": "https://api.deepseek.com",
    "enabled": true,
    "builtin": true,
    "hasApiKey": false,
    "maskedApiKey": "",
    "maxTokens": 1024,
    "priceInput": 0,
    "priceOutput": 0
  }
]
```

系统内置模型首次创建时不会读取 `.env` 中的 API Key，因此 `hasApiKey` 默认为 `false`。列表接口不会返回原始 API Key。

## 创建模型配置

```http
POST /api/model-configs
```

请求：

```json
{
  "providerName": "my-openai-compatible",
  "displayName": "自定义模型",
  "modelName": "custom-chat-model",
  "baseUrl": "https://example.com/v1",
  "apiKey": "sk-example",
  "enabled": true,
  "maxTokens": 1024,
  "priceInput": 0,
  "priceOutput": 0
}
```

创建接口用于自定义 OpenAI-compatible 供应商。系统内置供应商由后端自动补齐，不通过该接口创建。

## 更新模型配置

```http
PUT /api/model-configs/{modelConfigId}
```

请求字段与创建接口一致，均为可选字段。`apiKey` 为空字符串或不传时表示保留原密钥。内置配置可编辑 Base URL、API Key、模型名、展示名和启用状态，但不能删除。

## 删除模型配置

```http
DELETE /api/model-configs/{modelConfigId}
```

仅自定义配置允许删除。内置 DeepSeek、MiniMax、GLM 只能禁用，不能删除。

## 测试模型配置连接

```http
POST /api/model-configs/test
```

测试已保存配置：

```json
{
  "modelConfigId": 1
}
```

测试未保存草稿：

```json
{
  "providerName": "my-openai-compatible",
  "modelName": "custom-chat-model",
  "baseUrl": "https://example.com/v1",
  "apiKey": "sk-example",
  "maxTokens": 128
}
```

响应：

```json
{
  "success": true,
  "message": "连接测试成功",
  "latencyMs": 856
}
```

失败时 `success` 为 `false`，`message` 返回失败原因。

## 查询评测任务

```http
GET /api/evaluation/tasks/{taskId}
```

响应字段与创建评测任务一致，会从数据库读取任务、模型回答和规则评分，并返回任务的 `createdAt` 与 `completedAt`。任务不存在时返回 404。

## 提交用户反馈

```http
POST /api/evaluation/responses/{responseId}/feedback
```

请求：

```json
{
  "feedbackType": "like",
  "comment": "这个回答更清楚"
}
```

`feedbackType` 仅支持：

- `like`：点赞。
- `dislike`：点踩。

匿名用户统一使用 `user_id = 0`。同一用户对同一回答只能保留一个当前反馈：重复提交相同类型会取消，提交另一类型会从点赞切换为点踩或反向切换。

响应：

```json
{
  "responseId": 12,
  "feedbackType": "like",
  "active": true,
  "feedback": {
    "liked": true,
    "disliked": false,
    "likeCount": 1,
    "dislikeCount": 0
  }
}
```

回答不存在时返回 404。
