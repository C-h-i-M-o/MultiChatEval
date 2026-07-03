import { useState } from "react";
import { MenuFoldOutlined, MenuOutlined, PoweroffOutlined } from "@ant-design/icons";
import { Button, Drawer } from "antd";
import { NavLink, Outlet, useLocation } from "react-router-dom";

import { useAuth } from "../features/auth/AuthContext";
import { getVisibleNavigationItems } from "../features/navigation/navigation";

export function AppLayout() {
  const auth = useAuth();
  const user = auth.user;
  const location = useLocation();
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  if (!user) {
    return null;
  }

  const renderNav = () => (
    <nav className="side-nav" aria-label="业务导航">
      {getVisibleNavigationItems(user).map((item) => (
        <NavLink key={item.path} to={item.path} end={item.path === "/"} onClick={() => setMobileNavOpen(false)}>
          {item.label}
        </NavLink>
      ))}
    </nav>
  );
  const renderUserCard = () => (
    <div className="user-card">
      <span>{user.role === "admin" ? "管理员" : "普通用户"}</span>
      <strong>{user.username}</strong>
      <Button icon={<PoweroffOutlined />} type="primary" onClick={() => void auth.logout()}>
        退出登录
      </Button>
    </div>
  );

  return (
    <div className="workspace-layout" data-path={location.pathname}>
      <header className="mobile-topbar">
        <div className="mobile-brand">
          <span className="brand-mark">M</span>
          <strong>MultiChatEval</strong>
        </div>
        <Button
          aria-label="打开导航"
          icon={mobileNavOpen ? <MenuFoldOutlined /> : <MenuOutlined />}
          onClick={() => setMobileNavOpen((open) => !open)}
        />
      </header>
      <aside className="sidebar">
        <div>
          <p className="eyebrow">MultiChatEval React</p>
          <h1 className="layout-title">多模型评测</h1>
        </div>

        {renderNav()}
        {renderUserCard()}
      </aside>

      <main className="workspace-main">
        <Outlet />
      </main>
      <Drawer
        title="MultiChatEval"
        placement="right"
        width={280}
        open={mobileNavOpen}
        onClose={() => setMobileNavOpen(false)}
      >
        {renderNav()}
        {renderUserCard()}
      </Drawer>
    </div>
  );
}
