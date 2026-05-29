import { defineStore } from "pinia";

import { createEvaluationTask } from "../utils/api";

export const useEvaluationStore = defineStore("evaluation", {
  state: () => ({
    task: null,
    loading: false,
    errorMessage: ""
  }),
  actions: {
    async submitEvaluation(payload) {
      this.loading = true;
      this.errorMessage = "";

      try {
        this.task = await createEvaluationTask(payload);
      } catch (error) {
        this.errorMessage = error?.message || "评测任务创建失败";
      } finally {
        this.loading = false;
      }
    }
  }
});
