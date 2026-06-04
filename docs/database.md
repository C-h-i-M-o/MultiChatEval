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

创建评测时会先写入任务记录。同步接口和模型级渐进接口都会使用真实任务 ID 返回给前端。

## model_providers

模型供应商表，例如 DeepSeek、MiniMax、Zhipu。

字段重点：

- `name`：供应商唯一名称。内置供应商固定为 `deepseek`、`minimax`、`glm`。
- `base_url`：OpenAI-compatible 接口基础地址，例如 `https://api.deepseek.com`。
- `api_key_encrypted`：MVP 阶段复用为版本化密钥字段。当前使用 `plain:<api_key>` 明文格式保存，未来可升级为 `enc:v1:<ciphertext>` 加密格式。
- `enabled`：供应商是否启用。

业务代码不得直接读写原始 API Key 字段，需要通过统一密钥 helper 保存、读取和掩码展示。列表接口只返回 `hasApiKey` 和 `maskedApiKey`，不返回原文。

## model_configs

具体模型配置表，例如 `deepseek-v4-flash`、`MiniMax-M2.5`、`glm-4.7`。

字段重点：

- `provider_id`：关联模型供应商。
- `model_name`：发送给模型接口的真实模型名。
- `display_name`：前端展示名。
- `price_input` / `price_output`：输入和输出 token 单价，当前默认 0。
- `max_tokens`：单次回答最大输出 token。
- `enabled`：该模型配置是否可在评测页选择。

系统启动或查询模型配置时会补齐 DeepSeek、MiniMax、GLM 三个内置配置。内置配置只包含供应商名、Base URL、模型名和展示名，不会从 `.env` 读取 API Key。内置配置可编辑、可禁用，但不可删除。用户新增的自定义配置统一按 OpenAI-compatible 协议调用。

## model_responses

模型回答表。每个模型的一次回答单独保存。

字段重点：

- `answer_text`：原始回答
- `latency_ms`：响应耗时
- `input_tokens` / `output_tokens`：token 统计
- `estimated_cost`：费用估算
- `status` / `error_message`：调用状态

每个模型调用结束后写入一条回答记录。接口响应中的 `responses[].id` 对应本表主键，`responses[].modelConfigId` 对应 `model_configs.id`。

## evaluation_results

评分结果表。每条模型回答对应一组评分。

当前规则评分会写入：

- `relevance_score`：相关性
- `completeness_score`：完整性
- `clarity_score`：清晰度
- `format_score`：格式符合度
- `safety_score`：安全性
- `rule_score` / `final_score`：规则综合分

`judge_score` 和 `judge_comment` 保留给后续 LLM Judge 使用。

## user_feedback

用户反馈表。当前用于保存匿名点赞和采纳状态，`user_id` 暂时写入 `NULL`。

最小反馈闭环采用状态式语义：同一 `response_id + feedback_type` 不存在时新增反馈，已存在时取消反馈。当前支持的 `feedback_type` 为：

- `like`：点赞
- `accepted`：采纳

点踩、收藏、评论统计和登录用户维度暂未接入。
