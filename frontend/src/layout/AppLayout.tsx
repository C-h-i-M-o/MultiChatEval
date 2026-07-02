import { NavLink, Outlet } from "react-router-dom";

import { useAuth } from "../features/auth/AuthContext";
import { getVisibleNavigationItems } from "../features/navigation/navigation";

export function AppLayout() {
  const auth = useAuth();
  const user = auth.user;

  if (!user) {
    return null;
  }

  return (
    <div className="workspace-layout">
      <aside className="sidebar">
        <div>
          <p className="eyebrow">MultiChatEval React</p>
          <h1 className="layout-title">多模型评测</h1>
        </div>

        <nav className="side-nav" aria-label="业务导航">
          {getVisibleNavigationItems(user).map((item) => (
            <NavLink key={item.path} to={item.path} end={item.path === "/"}>
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="user-card">
          <span>{user.role === "admin" ? "管理员" : "普通用户"}</span>
          <strong>{user.username}</strong>
          <button type="button" onClick={() => void auth.logout()}>
            退出登录
          </button>
        </div>
      </aside>

      <main className="workspace-main">
        <Outlet />
      </main>
    </div>
  );
}
