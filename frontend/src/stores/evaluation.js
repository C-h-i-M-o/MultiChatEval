import { defineStore } from "pinia";

import { streamEvaluationTask } from "../utils/api";

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
      this.task = {
        taskId: null,
        status: "running",
        prompt: payload.prompt,
        responses: []
      };

      try {
        await streamEvaluationTask(payload, (event) => {
          if (event.type === "task_started") {
            this.task = {
              taskId: event.taskId,
              status: "running",
              prompt: event.prompt,
              responses: []
            };
            return;
          }

          if (event.type === "model_response") {
            const currentResponses = this.task?.responses || [];
            const nextResponses = currentResponses.filter((response) => response.id !== event.response.id);
            nextResponses.push(event.response);
            this.task = {
              ...(this.task || {}),
              responses: nextResponses
            };
            return;
          }

          if (event.type === "task_completed") {
            this.task = event.task;
          }
        });
      } catch (error) {
        this.errorMessage = error?.message || "评测任务创建失败";
      } finally {
        this.loading = false;
      }
    }
  }
});
