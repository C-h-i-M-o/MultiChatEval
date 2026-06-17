import { createRouter, createWebHistory } from "vue-router";

import { pinia } from "../stores";
import { useAuthStore } from "../stores/auth";
import AuthView from "../views/AuthView.vue";
import AdminUsersView from "../views/AdminUsersView.vue";
import EvaluationView from "../views/EvaluationView.vue";
import FeedbackStatsView from "../views/FeedbackStatsView.vue";
import HistoryView from "../views/HistoryView.vue";
import ModelConfigsView from "../views/ModelConfigsView.vue";

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/login",
      name: "login",
      component: AuthView,
      meta: { public: true }
    },
    {
      path: "/register",
      name: "register",
      component: AuthView,
      meta: { public: true }
    },
    {
      path: "/",
      name: "workspace",
      component: EvaluationView,
      meta: { requiresAuth: true }
    },
    {
      path: "/models",
      name: "model-configs",
      component: ModelConfigsView,
      meta: { requiresAuth: true, requiresAdmin: true }
    },
    {
      path: "/users",
      name: "admin-users",
      component: AdminUsersView,
      meta: { requiresAuth: true, requiresAdmin: true }
    },
    {
      path: "/history",
      name: "history",
      component: HistoryView,
      meta: { requiresAuth: true }
    },
    {
      path: "/feedback",
      name: "feedback-stats",
      component: FeedbackStatsView,
      meta: { requiresAuth: true, requiresAdmin: true }
    },
    {
      path: "/:pathMatch(.*)*",
      redirect: "/"
    }
  ]
});

router.beforeEach(async (to) => {
  const authStore = useAuthStore(pinia);
  await authStore.restoreSession();

  if (to.meta.public) {
    return authStore.isAuthenticated ? { path: "/" } : true;
  }
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return {
      path: "/login",
      query: { redirect: to.fullPath }
    };
  }
  if (to.meta.requiresAdmin && !authStore.isAdmin) {
    return { path: "/" };
  }
  return true;
});
