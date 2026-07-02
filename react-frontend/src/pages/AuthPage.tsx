import { FormEvent, useMemo, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { ApiError } from "../api/client";
import { useAuth } from "../features/auth/AuthContext";

export function AuthPage({ mode }: { mode: "login" | "register" }) {
  const auth = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const isRegister = mode === "register";

  const redirectPath = useMemo(() => {
    const params = new URLSearchParams(location.search);
    const redirect = params.get("redirect");
    return redirect?.startsWith("/") ? redirect : "/";
  }, [location.search]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setErrorMessage(null);

    const credentials = {
      username: username.trim(),
      password
    };

    if (!credentials.username || !credentials.password) {
      setErrorMessage("请输入用户名和密码");
      return;
    }

    try {
      if (isRegister) {
        await auth.register(credentials);
      } else {
        await auth.login(credentials);
      }
      navigate(redirectPath, { replace: true });
    } catch (error) {
      setErrorMessage(error instanceof ApiError ? error.message : "认证失败，请检查输入");
    }
  }

  return (
    <main className="auth-shell">
      <section className="auth-card">
        <div className="auth-brand">
          <span className="brand-mark">M</span>
          <div>
            <p className="eyebrow">MultiChatEval React</p>
            <h1>{isRegister ? "注册账号" : "登录系统"}</h1>
          </div>
        </div>

        <p className="auth-description">
          {isRegister ? "注册后即可创建公开或私有评测。" : "登录后继续查看评测任务与模型结果。"}
        </p>

        <form className="auth-form" onSubmit={(event) => void handleSubmit(event)}>
          <label>
            用户名
            <input
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              autoComplete="username"
              maxLength={64}
            />
          </label>
          <label>
            密码
            <input
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              type="password"
              autoComplete={isRegister ? "new-password" : "current-password"}
              maxLength={128}
            />
          </label>
          {errorMessage ? <p className="error-message">{errorMessage}</p> : null}
          <button className="auth-submit" type="submit" disabled={auth.loading}>
            {auth.loading ? "处理中..." : isRegister ? "注册并登录" : "登录"}
          </button>
        </form>

        <p className="auth-switch">
          {isRegister ? "已有账号？" : "还没有账号？"}
          <Link to={isRegister ? "/login" : "/register"}>{isRegister ? "返回登录" : "立即注册"}</Link>
        </p>
      </section>
    </main>
  );
}
