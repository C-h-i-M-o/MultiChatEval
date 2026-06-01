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

响应：

```json
{
  "taskId": 1001,
  "status": "completed",
  "prompt": "帮我解释什么是设计模式",
  "responses": []
}
```

该接口会等待所有模型调用完成后一次性返回完整结果，保留用于兼容旧前端或调试场景。

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
    "id": 1,
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
      "final": 8.4
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
