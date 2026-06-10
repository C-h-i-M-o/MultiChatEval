# 规则评分排除思考内容 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 规则评分仅分析 `<think>` 标签之外的最终回答，同时保留原始回答的存储与前端展示行为。

**Architecture:** 在 `RuleEvaluator.evaluate()` 的统一入口清除完整的 `<think>...</think>` 区块以及未闭合 `<think>` 后的内容，再将清洗结果传给所有评分维度。清洗不修改调用方传入的字符串，也不影响模型回答持久化、接口响应或 Markdown 渲染。

**Tech Stack:** Python、pytest、FastAPI 服务层既有规则评分模块

---

### Task 1: 锁定评分输入行为

**Files:**
- Test: `backend/tests/test_rule_evaluator.py`

- [x] 增加测试，验证带完整 `<think>` 区块的回答与纯最终回答得到完全相同的评分。
- [x] 增加测试，验证只有 `<think>` 内容的回答按空回答计为 0 分。
- [x] 增加测试，验证未闭合 `<think>` 及其后内容不进入评分。
- [x] 运行目标测试，确认新增测试因尚未清洗思考内容而失败。

### Task 2: 实现统一清洗

**Files:**
- Modify: `backend/app/services/rule_evaluator.py`
- Test: `backend/tests/test_rule_evaluator.py`

- [x] 在评分器内部新增 `_strip_think_content(answer: str) -> str`。
- [x] 使用不区分大小写、跨行匹配删除完整 `<think>...</think>` 区块。
- [x] 删除首个未闭合 `<think>` 标签及其后续内容。
- [x] 在空回答判断和所有评分维度调用前统一使用清洗结果。
- [x] 运行规则评分器测试，确认全部通过。

### Task 3: 同步说明并完成验证

**Files:**
- Modify: `docs/system-features-status.md`
- Modify: `docs/architecture.md`
- Modify: `README.md`
- Modify: `AGENTS.md`

- [x] 明确规则评分不包含 `<think>` 思考内容，但完整原始回答仍会保存和展示。
- [x] 执行 `cd backend && pytest -q`。
- [x] 执行 `git diff --check`。
- [x] 提交评分修复。
