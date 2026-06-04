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
  "enableThinking": false
}
```

`modelIds` 使用 `model_configs.id`。如果不传，后端默认选择已启用的 DeepSeek 和 MiniMax；如果这两个模型不可用，则选择前两个已启用模型。

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

发送给模型前，后端会在用户原始问题前追加系统内置提示词，用于统一回答质量、安全性和格式要求。接口响应和数据库中的 `prompt` 仍保留用户原始问题。

当前内置提示词：

```text
你是一个严谨、清晰、负责任的 AI 助手。请基于用户问题直接作答，并遵守以下要求：

1. 优先回答用户真正的问题，不要回避核心诉求。
2. 保持中文表达清晰、自然、结构化；如果用户明确要求其他语言，则按用户要求回复。
3. 如果问题适合分步骤、分点或对比说明，请使用清晰的段落、列表或表格组织答案。
4. 如果用户要求代码、JSON、表格、步骤、方案或对比，请严格遵守对应格式。
5. 不要编造不确定的信息。遇到无法确认的事实、数据、时间、版本或来源时，请明确说明不确定性。
6. 对涉及医疗、法律、金融、安全等高风险内容的问题，请给出谨慎、一般性的信息，并提醒用户寻求专业意见。
7. 避免输出违法、有害、危险操作指导、隐私泄露、凭据泄露或恶意攻击相关内容。
8. 回答应兼顾完整性和简洁性：必要时解释原因、给出示例或注意事项，但不要无意义冗长。
9. 如果用户问题本身含糊，请先基于最合理的理解回答，并指出关键假设；不要反复追问导致无法推进。

用户问题如下：
```

响应：

```json
{
  "taskId": 1001,
  "status": "completed",
  "prompt": "帮我解释什么是设计模式",
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
        "final": 8.4,
        "details": {
          "relevance": ["字符 n-gram 相似度 0.58", "覆盖解释意图", "回答聚焦于用户问题"],
          "completeness": ["回答长度处于有效区间"],
          "clarity": ["使用换行分隔内容"],
          "format": ["未指定格式，回答使用了可读结构"],
          "safety": ["未命中明显危险输出", "未发现拒答质量风险", "未涉及高风险专业建议"]
        }
      },
      "feedback": {
        "liked": false,
        "accepted": false,
        "likeCount": 0,
        "acceptedCount": 0
      }
    }
  ]
}
```

该接口会先写入 `evaluation_tasks`，等待所有模型调用完成后写入 `model_responses` 和 `evaluation_results`，再一次性返回完整结果。`responses[].id` 是 `model_responses.id`，`responses[].modelConfigId` 是 `model_configs.id`。

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
        "final": 8.4,
        "details": {
          "relevance": ["字符 n-gram 相似度 0.58", "覆盖解释意图", "回答聚焦于用户问题"],
          "completeness": ["回答长度处于有效区间"],
          "clarity": ["使用换行分隔内容"],
          "format": ["未指定格式，回答使用了可读结构"],
          "safety": ["未命中明显危险输出", "未发现拒答质量风险", "未涉及高风险专业建议"]
        }
      },
      "feedback": {
        "liked": false,
        "accepted": false,
        "likeCount": 0,
        "acceptedCount": 0
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

响应字段与创建评测任务一致，会从数据库读取任务、模型回答和规则评分。任务不存在时返回 404。

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

`feedbackType` 当前只支持：

- `like`：点赞
- `accepted`：采纳

该接口采用状态式切换语义。同一匿名用户上下文下，同一 `responseId + feedbackType` 不存在时会新增一条 `user_feedback`；再次提交同类反馈会取消该反馈。当前未接入登录系统，`user_id` 写入 `NULL`。

响应：

```json
{
  "responseId": 5001,
  "feedbackType": "like",
  "active": true,
  "feedback": {
    "liked": true,
    "accepted": false,
    "likeCount": 1,
    "acceptedCount": 0
  }
}
```

当 `responseId` 不存在时返回 404；当 `feedbackType` 不是 `like` 或 `accepted` 时返回 422。
