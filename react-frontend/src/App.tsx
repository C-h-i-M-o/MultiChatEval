import { Navigate, Route, Routes } from "react-router-dom";

import { AuthProvider } from "./features/auth/AuthContext";
import { AppLayout } from "./layout/AppLayout";
import { AuthPage } from "./pages/AuthPage";
import { PlaceholderPage } from "./pages/PlaceholderPage";
import { ProtectedRoute, PublicOnlyRoute } from "./routes/RouteGuards";

function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route
          path="/login"
          element={
            <PublicOnlyRoute>
              <AuthPage mode="login" />
            </PublicOnlyRoute>
          }
        />
        <Route
          path="/register"
          element={
            <PublicOnlyRoute>
              <AuthPage mode="register" />
            </PublicOnlyRoute>
          }
        />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <AppLayout />
            </ProtectedRoute>
          }
        >
          <Route
            index
            element={
              <PlaceholderPage
                title="评测工作台"
                description="阶段二已接入认证与布局，评测表单和模型级渐进展示会在阶段三迁移。"
              />
            }
          />
          <Route
            path="models"
            element={
              <PlaceholderPage title="模型配置" description="管理员入口已受角色保护，具体配置表单会在后续阶段迁移。" />
            }
          />
          <Route
            path="users"
            element={
              <PlaceholderPage title="用户额度" description="管理员入口已受角色保护，额度管理页面会在后续阶段迁移。" />
            }
          />
          <Route
            path="history"
            element={<PlaceholderPage title="历史任务" description="历史任务分页和详情会在后续阶段迁移。" />}
          />
          <Route
            path="feedback"
            element={<PlaceholderPage title="反馈统计" description="角色分流统计视图会在后续阶段迁移。" />}
          />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  );
}

export default App;
