# 数据库设计

## users

用户表，保存登录用户信息。

字段重点：

- `username`：登录用户名，唯一。
- `password_hash`：Argon2 密码哈希。
- `role`：用户角色，支持 `user` 和 `admin`。
- `status`：用户状态，支持 `active` 和 `disabled`。
- `last_login_at`：最近一次登录成功时间。

开放注册用户默认为 `user` 和 `active`。匿名用户固定使用 `id = 0`，状态为 `disabled`，只用于承载 demo-v1 历史数据，不允许登录。

## conversations

会话表，保存用户的一组评测上下文。

## evaluation_tasks

评测任务表。用户每提交一次问题，就创建一个任务。

字段重点：

- `user_id`：任务创建者。旧匿名任务统一迁移为 `0`。
- `prompt`：用户问题
- `status`：任务状态
- `visibility`：`public` 或 `private`，默认 `public`
- `completed_at`：完成时间

创建评测时会先写入任务记录。同步接口和模型级渐进接口都会使用真实任务 ID 返回给前端。

公开任务对所有登录用户可见；私有任务只对创建者可见。管理员通过普通任务接口也不能查看其他用户的私有任务。

## model_providers

模型供应商表，保存管理员实际创建的 OpenAI-compatible 供应商。

字段重点：

- `name`：供应商唯一名称。
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
- `temperature`：默认温度。
- `timeout_seconds`：单次请求超时秒数。
- `notes`：管理员备注。
- `currency`：价格币种，支持 `CNY` 和 `USD`。
- `price_input` / `price_output` / `price_cache_hit` / `price_cache_creation`：每 100 万 Token 的四类单价。
- `max_tokens`：单次回答最大输出 token。
- `enabled`：该模型配置是否可在评测页选择。

系统不自动创建供应商数据。前端提供常见官方供应商预设和 OpenAI-compatible 空白模板，所有实际保存的配置均可编辑、禁用或删除。

## model_responses

模型回答表。每个模型的一次回答单独保存。

字段重点：

- `answer_text`：原始回答
- `latency_ms`：响应耗时
- `input_tokens` / `output_tokens` / `cache_hit_tokens` / `cache_creation_tokens` / `total_tokens`：四类与总 Token 统计
- `input_cost` / `output_cost` / `cache_hit_cost` / `cache_creation_cost`：四类费用
- `estimated_cost`：四项费用之和
- `currency`：费用币种
- `config_snapshot`：调用时的模型参数与价格快照，不含 API Key
- `status` / `error_message`：调用状态

每个模型调用结束后写入一条回答记录。接口响应中的 `responses[].id` 对应本表主键，`responses[].modelConfigId` 对应 `model_configs.id`。

## user_token_quotas

保存普通用户每日总 Token 上限。每个用户最多一条记录；没有记录时使用默认值 100,000。管理员角色不受额度限制。

## token_usage_logs

记录每个模型回答产生的总 Token，用于审计。字段包含 `user_id`、`task_id`、`response_id`、`model_config_id`、`usage_date` 和 `total_tokens`。

## daily_user_token_usage

按用户和北京时间自然日汇总总 Token。`user_id + usage_date` 唯一，模型回答持久化时原子累加。

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

用户反馈表。用于保存登录用户的点赞和点踩状态。

- demo-v1 旧匿名反馈继续归属 `users.id = 0`。
- 新反馈写入当前登录用户 ID。
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

demo-v1 旧匿名评论继续归属 `user_id = 0`。新评论写入当前登录用户 ID，只有评论作者可以删除。
