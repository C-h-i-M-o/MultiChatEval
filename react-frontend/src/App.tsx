import { useEffect, useState } from "react";
import { Link, Route, Routes } from "react-router-dom";

import { getCurrentUser, getHealthStatus, type HealthStatus, type UserProfile } from "./api/client";
import { isUnauthorizedError } from "./features/auth/auth";

interface PhaseOneState {
  health: HealthStatus | null;
  user: UserProfile | null;
  loading: boolean;
  errorMessage: string | null;
  authMessage: string;
}

const initialState: PhaseOneState = {
  health: null,
  user: null,
  loading: true,
  errorMessage: null,
  authMessage: "正在恢复登录态"
};

function App() {
  const [state, setState] = useState<PhaseOneState>(initialState);

  useEffect(() => {
    let cancelled = false;

    async function loadPhaseOneState(): Promise<void> {
      try {
        const health = await getHealthStatus();
        let user: UserProfile | null = null;
        let authMessage = "登录态恢复完成";

        try {
          user = await getCurrentUser();
        } catch (error) {
          if (isUnauthorizedError(error)) {
            authMessage = "未登录，后续阶段将接入登录页";
          } else {
            throw error;
          }
        }

        if (!cancelled) {
          setState({
            health,
            user,
            loading: false,
            errorMessage: null,
            authMessage
          });
        }
      } catch (error) {
        if (!cancelled) {
          const message = error instanceof Error ? error.message : "React 前端初始化失败";
          setState({
            health: null,
            user: null,
            loading: false,
            errorMessage: message,
            authMessage: "登录态恢复未完成"
          });
        }
      }
    }

    void loadPhaseOneState();

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <Routes>
      <Route path="*" element={<PhaseOneShell state={state} />} />
    </Routes>
  );
}

function PhaseOneShell({ state }: { state: PhaseOneState }) {
  return (
    <main className="app-shell">
      <nav className="topbar" aria-label="主导航">
        <Link to="/" className="brand">
          MultiChatEval React
        </Link>
        <span className="phase-badge">阶段一</span>
      </nav>

      <section className="hero-section">
        <div className="hero-copy">
          <p className="eyebrow">React 重构基线</p>
          <h1>多模型对话质量评估系统</h1>
          <p className="summary">
            当前 React 版本只接入工程壳、开发代理、系统健康检查和登录态恢复，后续页面会按既有 Vue 业务能力逐步迁移。
          </p>
        </div>
        <StatusPanel state={state} />
      </section>
    </main>
  );
}

function StatusPanel({ state }: { state: PhaseOneState }) {
  return (
    <section className="status-panel" aria-label="阶段一联调状态">
      <h2>阶段一联调</h2>
      <StatusRow
        label="系统健康检查"
        value={state.health?.status === "ok" ? "后端已响应" : "等待响应"}
        tone={state.health?.status === "ok" ? "ready" : "pending"}
      />
      <StatusRow
        label="登录态恢复"
        value={state.user ? `${state.user.username}（${state.user.role}）` : state.authMessage}
        tone={state.user ? "ready" : "pending"}
      />
      <StatusRow label="加载状态" value={state.loading ? "请求中" : "已完成"} tone={state.loading ? "pending" : "ready"} />
      {state.errorMessage ? <p className="error-message">{state.errorMessage}</p> : null}
    </section>
  );
}

function StatusRow({ label, value, tone }: { label: string; value: string; tone: "ready" | "pending" }) {
  return (
    <div className="status-row">
      <span>{label}</span>
      <strong className={`status-pill status-pill-${tone}`}>{value}</strong>
    </div>
  );
}

export default App;
