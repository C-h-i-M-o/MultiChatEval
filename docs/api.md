# API 草案

## 认证约定

除健康检查、注册和登录外，业务接口均要求浏览器携带后端签发的 HttpOnly Cookie。未登录返回 `401`，普通用户访问管理员接口返回 `403`。

### 注册

```http
POST /api/auth/register
```

```json
{
  "username": "demo_user",
  "password": "password123"
}
```

注册成功返回当前用户并设置登录 Cookie。重复用户名返回 `409`。

### 登录

```http
POST /api/auth/login
```

请求结构与注册相同。登录成功返回当前用户并设置登录 Cookie；凭据错误返回 `401`，禁用用户返回 `403`。

### 当前用户

```http
GET /api/auth/me
```

```json
{
  "id": 1,
  "username": "demo_user",
  "role": "user",
  "status": "active"
}
```

### 退出

```http
POST /api/auth/logout
```

成功时清除登录 Cookie 并返回 `204 No Content`。

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
  "enableThinking": false,
  "visibility": "public"
}
```

`modelIds` 使用 `model_configs.id`。如果不传，后端默认选择已启用的 DeepSeek 和 MiniMax；如果这两个模型不可用，则选择前两个已启用模型。

`visibility` 支持 `public` 和 `private`，默认 `public`。公开任务可被所有登录用户查看，私有任务只对创建者可见。

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
        "ruleFinal": 8.4,
        "judgeFinal": null,
        "baseFinal": 8.4,
        "feedbackScore": null,
        "final": 8.4,
        "details": {
          "relevance": ["字符 n-gram 相似度 0.58", "覆盖解释意图", "回答聚焦于用户问题"],
          "completeness": ["回答长度处于有效区间"],
          "clarity": ["使用换行分隔内容"],
          "format": ["未指定格式，回答使用了可读结构"],
          "safety": ["未命中明显危险输出", "未发现拒答质量风险", "未涉及高风险专业建议"]
        },
        "judgeComment": null,
        "judgeDetails": {}
      },
      "feedback": {
        "liked": false,
        "disliked": false,
        "likeCount": 0,
        "dislikeCount": 0
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
        "ruleFinal": 8.4,
        "judgeFinal": null,
        "baseFinal": 8.4,
        "feedbackScore": null,
        "final": 8.4,
        "details": {
          "relevance": ["字符 n-gram 相似度 0.58", "覆盖解释意图", "回答聚焦于用户问题"],
          "completeness": ["回答长度处于有效区间"],
          "clarity": ["使用换行分隔内容"],
          "format": ["未指定格式，回答使用了可读结构"],
          "safety": ["未命中明显危险输出", "未发现拒答质量风险", "未涉及高风险专业建议"]
        },
        "judgeComment": null,
        "judgeDetails": {}
      },
      "feedback": {
        "liked": false,
        "disliked": false,
        "likeCount": 0,
        "dislikeCount": 0
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

## 查询可评测模型

```http
GET /api/models/available
```

所有登录用户可访问，只返回已启用且已配置 API Key 的模型精简信息。

## 查询模型配置

```http
GET /api/admin/model-configs
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

该接口仅管理员可访问。系统内置模型首次创建时不会读取 `.env` 中的 API Key，因此 `hasApiKey` 默认为 `false`。列表接口不会返回原始 API Key。

## 创建模型配置

```http
POST /api/admin/model-configs
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
PUT /api/admin/model-configs/{modelConfigId}
```

请求字段与创建接口一致，均为可选字段。`apiKey` 为空字符串或不传时表示保留原密钥。内置配置可编辑 Base URL、API Key、模型名、展示名和启用状态，但不能删除。

## 删除模型配置

```http
DELETE /api/admin/model-configs/{modelConfigId}
```

仅自定义配置允许删除。内置 DeepSeek、MiniMax、GLM 只能禁用，不能删除。

## 测试模型配置连接

```http
POST /api/admin/model-configs/test
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
  "feedbackType": "like"
}
```

`feedbackType` 当前只支持：

- `like`：点赞
- `dislike`：点踩

该接口采用互斥状态式切换语义。同一登录用户对同一回答只能保留一个当前反馈：重复提交相同类型会取消，提交另一类型会从点赞切换为点踩或反向切换。反馈写入当前登录用户 ID；demo-v1 旧匿名反馈继续归属 `user_id = 0`。

反馈提交后会重算并持久化最终分：

```text
baseFinal = ruleFinal                           # 未启用或未得到有效 Judge 分
baseFinal = ruleFinal * 0.60 + judgeFinal * 0.40
feedbackScore = 10 * likeCount / (likeCount + dislikeCount)
final = baseFinal                               # 暂无反馈
final = baseFinal * 0.90 + feedbackScore * 0.10 # 已有反馈
```

评论不通过该接口提交，也不参与评分。

响应：

```json
{
  "responseId": 5001,
  "feedbackType": "like",
  "active": true,
  "feedback": {
    "liked": true,
    "disliked": false,
    "likeCount": 1,
    "dislikeCount": 0
  },
  "score": {
    "relevance": 8,
    "completeness": 8,
    "clarity": 8,
    "format": 8,
    "safety": 10,
    "ruleFinal": 8.4,
    "judgeFinal": null,
    "baseFinal": 8.4,
    "feedbackScore": 10,
    "final": 8.56,
    "details": {},
    "judgeComment": null,
    "judgeDetails": {}
  }
}
```

当 `responseId` 不存在时返回 404；当 `feedbackType` 不是 `like` 或 `dislike` 时返回 422。

## 查询回答评论

```http
GET /api/evaluation/responses/{responseId}/comments?page=1&pageSize=20
```

评论按 `created_at desc, id desc` 返回。`pageSize` 取值范围为 1–100。

响应：

```json
{
  "items": [
    {
      "id": 301,
      "responseId": 5001,
      "userId": 0,
      "username": "anonymous",
      "content": "这个回答的步骤很清楚。",
      "createdAt": "2026-06-06T10:30:00",
      "canDelete": true
    }
  ],
  "total": 1,
  "page": 1,
  "pageSize": 20
}
```

回答不存在时返回 404。

## 发布回答评论

```http
POST /api/evaluation/responses/{responseId}/comments
```

请求：

```json
{
  "content": "这个回答的步骤很清楚。"
}
```

评论会去除首尾空白，正文长度限制为 1–1000 个字符。每个用户可以对同一回答发布多条评论。成功时返回新建评论，回答不存在时返回 404，正文为空或超长时返回 422。

成功响应：

```json
{
  "id": 301,
  "responseId": 5001,
  "userId": 0,
  "username": "anonymous",
  "content": "这个回答的步骤很清楚。",
  "createdAt": "2026-06-06T10:30:00",
  "canDelete": true
}
```

## 删除回答评论

```http
DELETE /api/evaluation/comments/{commentId}
```

只能删除当前用户自己的评论。成功时返回 `204 No Content`；评论不存在或不属于当前用户时返回 404。
