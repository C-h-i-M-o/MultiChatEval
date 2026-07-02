# React 重构文档入口

本文档目录用于维护 MultiChatEval 的 React 前端重构资料。

当前边界：

- 保留现有 `frontend/` Vue 前端作为可运行基线。
- 新建 React 技术栈前端，不直接替换现有 Vue 代码。
- 复用现有 FastAPI API、MySQL 数据结构、认证权限模型、评分逻辑和模型级 NDJSON 渐进返回语义。
- 不借 React 重构继续开发 v2 已冻结的新功能，例如语义分析、模型推荐、运行监控、评论审核、导出和批量评测。

## 文档索引

- `plan.md`：React 重构阶段计划、迁移顺序和验收标准。
- `architecture.md`：React 前端架构草案、模块边界和数据流。

## 相关权威文档

- `../api.md`：后端接口说明，React 前端必须优先复用。
- `../database.md`：数据库结构说明，React 重构默认不修改。
- `../architecture.md`：当前系统架构和 Vue 基线说明。
- `../system-features-status.md`：当前已实现功能与 React 重构优先级。
- `../legacy-v2/`：v2 历史开发文档归档。
