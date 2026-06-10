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
- `rule_score`：规则综合分
- `judge_score` / `judge_comment`：可选 LLM Judge 分数、理由和结构化明细
- `final_score`：当前最终分；无用户反馈时等于基础分，有反馈时写入包含 10% 反馈分的结果

基础分为规则分，或在 Judge 有效时使用 `rule_score * 0.60 + judge_score * 0.40`。存在点赞/点踩时，反馈分按点赞比例映射到 0–10，并以 10% 权重计入 `final_score`；评论不参与评分。

写入规则评分前，评分器会排除完整的 `<think>...</think>` 思考区块；若标签未闭合，则忽略 `<think>` 及其后续内容。`model_responses.answer_text` 仍保存完整原始回答，便于前端继续展示折叠的思考过程。

## user_feedback

用户反馈表。当前用于保存匿名点赞和点踩状态。

- 匿名用户固定使用 `users.id = 0`，用户名为 `anonymous`。
- 后续登录用户从 `users.id = 1` 开始自增。
- `user_feedback.user_id` 对匿名反馈写入 `0`，不使用 `NULL`。
- `user_id + response_id` 具备唯一约束，保证同一用户对同一回答只有一个当前反馈。
- 当前支持的 `feedback_type` 为：

- `like`：点赞
- `dislike`：点踩

`user_feedback` 不再保存评论。

## user_comments

公开评论表。每条记录表示用户对某个模型回答发布的一条纯文本评论。

- `user_id`：评论用户；当前匿名用户固定为 `0`。
- `response_id`：关联 `model_responses.id`。
- `content`：去除首尾空白后的评论正文，接口限制为 1–1000 个字符。
- `created_at`：评论发布时间。
- 不设置 `user_id + response_id` 唯一约束，同一用户可以对同一回答发布多条评论。
- 第一版支持发布、分页查询和硬删除，不支持编辑、评论点赞、审核或富文本。

旧版 `user_feedback.comment` 中已有的非空内容会在 Alembic 迁移时复制到 `user_comments`，随后删除旧字段。

当前尚未接入真实登录体系，因此所有匿名访客都映射为 `user_id = 0`，无法在不同匿名访客之间区分评论归属。
