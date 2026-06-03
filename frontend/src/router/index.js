import { createRouter, createWebHistory } from "vue-router";

import EvaluationView from "../views/EvaluationView.vue";
import FeedbackStatsView from "../views/FeedbackStatsView.vue";
import HistoryView from "../views/HistoryView.vue";
import ModelConfigsView from "../views/ModelConfigsView.vue";

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      name: "workspace",
      component: EvaluationView
    },
    {
      path: "/models",
      name: "model-configs",
      component: ModelConfigsView
    },
    {
      path: "/history",
      name: "history",
      component: HistoryView
    },
    {
      path: "/feedback",
      name: "feedback-stats",
      component: FeedbackStatsView
    },
    {
      path: "/:pathMatch(.*)*",
      redirect: "/"
    }
  ]
});
