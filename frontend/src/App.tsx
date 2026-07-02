import { Navigate, Route, Routes } from "react-router-dom";

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
  );
}

export default App;
