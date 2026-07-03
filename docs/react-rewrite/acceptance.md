# React 重构收尾验收清单

最后更新：2026-07-03

本文档用于阶段五收尾。目标是确认 React 主前端已经覆盖原 Vue 前端的核心业务路径，同时明确 Vue 前端继续作为历史版本保留，不在阶段五删除。

## 自动验收

推荐使用统一脚本：

```bash
./scripts/verify-react-rewrite.sh
```

脚本会依次执行：

```bash
export CI=true
cd backend && .venv/bin/pytest -q
cd frontend && pnpm test
cd frontend && pnpm build
cd vue-frontend && pnpm test
cd vue-frontend && pnpm build
git diff --check
```

在 macOS 本机存在 `/opt/homebrew/bin/pnpm` 时，脚本会优先使用 Homebrew pnpm；也可以通过 `PNPM_BIN=/path/to/pnpm ./scripts/verify-react-rewrite.sh` 指定 pnpm。

如果只验证 React 主前端，可以单独运行：

```bash
cd frontend
pnpm test
pnpm build
```

## 手工核心路径

本地启动 React 版本全栈项目：

```bash
./scripts/start-local.sh
```

默认访问地址为：

```text
http://127.0.0.1:5174
```

验收项：

| 路径 | 验收点 |
| --- | --- |
| `/login`、`/register` | 未登录用户可以登录或注册，已登录用户不会停留在认证页 |
| `/` | 可加载可用模型、今日 Token、公开/私有选项、思考模式和 LLM 评审选项 |
| `/` | 提交评测后按模型完成顺序展示结果，单模型失败不阻塞其他模型 |
| `/` | 回答详情支持 Markdown 安全渲染、`<think>` 折叠、评分详情和点赞/点踩 |
| `/history` | 可分页查看历史任务、加载详情、识别公开/私有和超时未完成任务 |
| `/history` | 历史详情可继续点赞/点踩，并可分页查看、发布、删除公开评论 |
| `/models` | 管理员可新增、编辑、启用/禁用、删除模型配置并测试连接 |
| `/users` | 管理员可查看用户今日 Token 用量并调整普通用户每日额度 |
| `/feedback` | 普通用户查看个人统计，管理员查看全局模型表现、趋势和互动明细 |
| 权限 | 普通用户不显示也不能访问 `/models` 和 `/users` |

## Vue 历史版本决策

阶段五不删除 `vue-frontend/`。原因：

- Vue 版本保留为历史实现，便于必要时对照旧交互。
- React 替代过程不改变后端 API、数据库结构、权限模型和评分公式。
- 是否移除 Vue 前端需要单独任务决策，不能作为阶段五默认动作。

## 收尾结论

阶段五完成后，React 主前端的收尾标准为：

- 自动验收脚本通过。
- `docs/react-rewrite/`、`README.md`、`AGENTS.md` 和 `docs/system-features-status.md` 描述一致。
- Vue 前端继续作为历史版本保留，并通过独立测试和构建验证。
