# v2 阶段 2/3：模型计费与 Token 额度设计

> 归档说明：本文档是 v2 历史设计文档。v2 已冻结，React 替代 Vue 的历史重构文档见 `../react-rewrite/`。

最后更新：2026-06-12

## 目标

阶段 2 将模型配置改为管理员统一维护的 OpenAI-compatible 配置，并补齐模型参数与四类 Token 价格。阶段 3 按用户记录每日总 Token，用最小可用规则限制普通用户继续发起评测。

## 模型配置

系统不再自动创建 DeepSeek、MiniMax、GLM 数据库记录。新建配置时提供以下预设，用于填充供应商名称、Base URL、说明、控制台和官方定价文档：

- DeepSeek：`https://api.deepseek.com`
- MiniMax：`https://api.minimaxi.com/v1`
- GLM：`https://open.bigmodel.cn/api/paas/v4`
- Qwen：`https://dashscope.aliyuncs.com/compatible-mode/v1`
- Xiaomi MiMo：`https://api.xiaomimimo.com/v1`
- OpenAI：`https://api.openai.com/v1`
- OpenAI-compatible：空白模板

预设不包含模型名称、API Key 或价格，不代表系统保证供应商所有模型均兼容。Claude 等非 OpenAI-compatible 接口不在本阶段范围内。

基础配置包含供应商、展示名、模型名、API Key 和启用状态。页面默认展示 DeepSeek、MiniMax、GLM，其他预设通过“更多供应商”展开。Base URL 随预设自动填充，并放在“高级选项”内供管理员核对或修改。

“高级选项”折叠区包含：

- `temperature`：默认温度，范围 0–2，默认 0.7。
- `maxTokens`：单次回答最大输出 Token，默认 1024。
- `timeoutSeconds`：单次请求超时秒数，默认 60。
- `notes`：管理员备注。
- `currency`：`CNY` 或 `USD`。
- `priceInput`、`priceOutput`、`priceCacheHit`、`priceCacheCreation`：每 100 万 Token 的价格。

## Token 与成本

适配器把供应商 usage 归一化为：

- `inputTokens`：未计入缓存命中、缓存创建的普通输入 Token。
- `outputTokens`：输出 Token。
- `cacheHitTokens`：缓存命中输入 Token。
- `cacheCreationTokens`：缓存创建输入 Token。
- `totalTokens`：四类 Token 总和。

供应商未返回某一缓存字段时按 0 处理。成功响应缺失 usage 时继续使用字符长度作为输入、输出兜底；失败且没有 usage 时全部记 0。

四项费用分别按 `tokens × 每百万 Token 单价 ÷ 1,000,000` 计算，总费用为四项之和。系统保存模型参数和价格快照，但不保存 API Key，不进行货币换算、阶梯价格或 Batch 折扣计算。

## 每日额度

- 普通用户默认每日额度为 100,000 总 Token。
- 管理员不受额度限制。
- 自然日按 `Asia/Shanghai` 计算，数据库保存日期值。
- 发起同步或渐进评测前检查今日已用量；普通用户额度已耗尽时返回 429。
- 不预占最大输出量。每个模型回答持久化时在同一事务写入流水并累计每日汇总，当前任务允许实际消耗超过剩余额度，后续任务立即阻止。
- Token 流水只记录用户、任务、回答、模型和总 Token，不复制四类明细。

## 前端行为

- 评测页展示今日已用、剩余和每日额度；管理员显示“不限额”。
- 回答摘要先显示带币种的总费用。桌面端悬停或键盘聚焦显示四项 Token 与费用，移出或失焦关闭；触屏设备点击切换。
- 管理员用户管理页展示用户名、角色、状态、今日用量和每日额度，并允许修改普通用户额度。

## 验收

- 普通用户不能访问模型配置和额度管理接口。
- 启用且配置 API Key 的模型能使用保存的温度、最大输出和超时调用。
- 回答记录、接口响应和历史详情中的四类 Token、总 Token 与费用一致。
- 北京时间跨日后使用新的每日汇总。
- 达到额度的普通用户不能创建新评测，管理员仍可正常使用。
