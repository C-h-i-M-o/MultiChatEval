import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

import {
  getCurrentUser,
  loginUser,
  logoutUser,
  registerUser,
  type AuthCredentials,
  type RegisterCredentials,
  type UserProfile
} from "../../api/client";
import { isUnauthorizedError } from "./auth";

interface AuthContextValue {
  user: UserProfile | null;
  initialized: boolean;
  loading: boolean;
  login: (credentials: AuthCredentials) => Promise<UserProfile>;
  register: (credentials: RegisterCredentials) => Promise<UserProfile>;
  logout: () => Promise<void>;
  refresh: () => Promise<UserProfile | null>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [initialized, setInitialized] = useState(false);
  const [loading, setLoading] = useState(false);

  const refresh = useCallback(async (): Promise<UserProfile | null> => {
    try {
      const currentUser = await getCurrentUser();
      setUser(currentUser);
      return currentUser;
    } catch (error) {
      if (!isUnauthorizedError(error)) {
        throw error;
      }
      setUser(null);
      return null;
    } finally {
      setInitialized(true);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const login = useCallback(async (credentials: AuthCredentials): Promise<UserProfile> => {
    setLoading(true);
    try {
      const currentUser = await loginUser(credentials);
      setUser(currentUser);
      setInitialized(true);
      return currentUser;
    } finally {
      setLoading(false);
    }
  }, []);

  const register = useCallback(async (credentials: RegisterCredentials): Promise<UserProfile> => {
    setLoading(true);
    try {
      const currentUser = await registerUser(credentials);
      setUser(currentUser);
      setInitialized(true);
      return currentUser;
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(async (): Promise<void> => {
    try {
      await logoutUser();
    } finally {
      setUser(null);
      setInitialized(true);
    }
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      initialized,
      loading,
      login,
      register,
      logout,
      refresh
    }),
    [initialized, loading, login, logout, refresh, register, user]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth 必须在 AuthProvider 内使用");
  }
  return context;
}
