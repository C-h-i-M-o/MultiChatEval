import { Navigate, Route, Routes } from "react-router-dom";
import { ConfigProvider } from "antd";
import zhCN from "antd/locale/zh_CN";

import { AuthProvider } from "./features/auth/AuthContext";
import { AppLayout } from "./layout/AppLayout";
import { AuthPage } from "./pages/AuthPage";
import { EvaluationPage } from "./pages/EvaluationPage";
import { HistoryPage } from "./pages/HistoryPage";
import { AdminUsersPage } from "./pages/AdminUsersPage";
import { FeedbackStatsPage } from "./pages/FeedbackStatsPage";
import { ModelConfigsPage } from "./pages/ModelConfigsPage";
import { ProtectedRoute, PublicOnlyRoute } from "./routes/RouteGuards";

function App() {
  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        token: {
          colorPrimary: "#1e4a2e",
          borderRadius: 8,
          fontFamily: "Avenir Next, Helvetica Neue, Helvetica, Arial, sans-serif"
        }
      }}
    >
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
            <Route index element={<EvaluationPage />} />
            <Route path="models" element={<ModelConfigsPage />} />
            <Route path="users" element={<AdminUsersPage />} />
            <Route path="history" element={<HistoryPage />} />
            <Route path="feedback" element={<FeedbackStatsPage />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </ConfigProvider>
  );
}

export default App;
