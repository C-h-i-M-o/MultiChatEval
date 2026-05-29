import { createRouter, createWebHistory } from "vue-router";

import EvaluationWorkspace from "../views/EvaluationWorkspace.vue";

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      name: "workspace",
      component: EvaluationWorkspace
    }
  ]
});
