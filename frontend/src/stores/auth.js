import { defineStore } from "pinia";

import { getCurrentUser, loginUser, logoutUser, registerUser } from "../utils/api";

export const useAuthStore = defineStore("auth", {
  state: () => ({
    user: null,
    initialized: false,
    loading: false
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.user),
    isAdmin: (state) => state.user?.role === "admin"
  },
  actions: {
    async restoreSession() {
      if (this.initialized) {
        return this.user;
      }
      try {
        this.user = await getCurrentUser();
      } catch (error) {
        if (error?.response?.status !== 401) {
          throw error;
        }
        this.user = null;
      } finally {
        this.initialized = true;
      }
      return this.user;
    },
    async login(credentials) {
      this.loading = true;
      try {
        this.user = await loginUser(credentials);
        this.initialized = true;
        return this.user;
      } finally {
        this.loading = false;
      }
    },
    async register(credentials) {
      this.loading = true;
      try {
        this.user = await registerUser(credentials);
        this.initialized = true;
        return this.user;
      } finally {
        this.loading = false;
      }
    },
    async logout() {
      try {
        await logoutUser();
      } finally {
        this.user = null;
        this.initialized = true;
      }
    }
  }
});
