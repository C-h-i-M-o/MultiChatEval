# 文档目录说明

本文档用于区分当前仍在维护的权威文档、React 重构文档和 v2 历史归档文档。

## 当前权威文档

这些文档描述当前系统已经实现并继续复用的后端、数据库、接口和 Vue 前端基线：

- `architecture.md`：系统架构、核心流程和现有 Vue 前端展示层。
- `api.md`：后端接口说明，React 前端重构必须复用。
- `database.md`：数据库表结构和持久化说明。
- `system-features-status.md`：系统功能状态和 React 重构优先级。
- `uml.md`：当前实现对应的图示文档。
- `open-source-reuse.md`：开源项目参考和复用说明。

## 当前 React 重构文档

React 重构相关文档统一放在 `react-rewrite/`：

- `react-rewrite/README.md`：React 重构文档入口。
- `react-rewrite/plan.md`：React 前端重构计划。
- `react-rewrite/architecture.md`：React 前端架构草案。

## v2 历史归档文档

v2 已冻结，历史开发计划和阶段设计统一归档在 `legacy-v2/`。这些文档只用于回看历史规划，不再作为当前开发目标：

- `legacy-v2/development-plan.md`
- `legacy-v2/stage1-auth-rbac-design.md`
- `legacy-v2/stage2-3-model-billing-quota-design.md`

## 维护规则

- 当前 React 重构相关说明优先写入 `react-rewrite/`。
- 已冻结的 v2 规划不要继续改写成当前目标。
- 接口变化同步 `api.md`。
- 数据库变化同步 `database.md`。
- 架构或主流程变化同步 `architecture.md` 和 `system-features-status.md`。
