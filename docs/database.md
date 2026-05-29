# 数据库设计

## users

用户表，保存登录用户信息。

## conversations

会话表，保存用户的一组评测上下文。

## evaluation_tasks

评测任务表。用户每提交一次问题，就创建一个任务。

字段重点：

- `prompt`：用户问题
- `status`：任务状态
- `completed_at`：完成时间

## model_providers

模型供应商表，例如 DeepSeek、MiniMax、Zhipu。

## model_configs

具体模型配置表，例如 `deepseek-v4-flash`、`MiniMax-M2.5`、`glm-4.7`。

## model_responses

模型回答表。每个模型的一次回答单独保存。

字段重点：

- `answer_text`：原始回答
- `latency_ms`：响应耗时
- `input_tokens` / `output_tokens`：token 统计
- `estimated_cost`：费用估算
- `status` / `error_message`：调用状态

## evaluation_results

评分结果表。每条模型回答对应一组评分。

## user_feedback

用户反馈表。用于保存点赞、点踩、采纳和评论。
