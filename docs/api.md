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
  "enableJudge": false
}
```

响应：

```json
{
  "taskId": 1001,
  "status": "completed",
  "prompt": "帮我解释什么是设计模式",
  "responses": []
}
```

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
