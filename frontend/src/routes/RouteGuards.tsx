import { Navigate, useLocation } from "react-router-dom";
import type { ReactNode } from "react";

import { useAuth } from "../features/auth/AuthContext";
import { resolveRouteAccess } from "../features/navigation/navigation";

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const auth = useAuth();
  const location = useLocation();

  if (!auth.initialized) {
    return <main className="route-loading">正在恢复登录态...</main>;
  }

  const access = resolveRouteAccess(location.pathname, auth.user);

  if (access.type === "redirect") {
    const search = access.redirect ? `?redirect=${encodeURIComponent(access.redirect)}` : "";
    return <Navigate to={`${access.to}${search}`} replace />;
  }

  return children;
}

export function PublicOnlyRoute({ children }: { children: ReactNode }) {
  const auth = useAuth();
  const location = useLocation();

  if (!auth.initialized) {
    return <main className="route-loading">正在恢复登录态...</main>;
  }

  const access = resolveRouteAccess(location.pathname, auth.user);

  if (access.type === "redirect") {
    return <Navigate to={access.to} replace />;
  }

  return children;
}
