import { defineStore } from "pinia";

import { getEvaluationTask, listEvaluationTasks, streamEvaluationTask, submitResponseFeedback } from "../utils/api";

export const useEvaluationStore = defineStore("evaluation", {
  state: () => ({
    task: null,
    loading: false,
    errorMessage: "",
    historyItems: [],
    historyTotal: 0,
    historyPage: 1,
    historyPageSize: 10,
    historyLoading: false,
    historyErrorMessage: "",
    selectedHistoryTask: null,
    historyDetailLoading: false,
    feedbackSubmittingIds: []
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
            const nextResponses = currentResponses.filter((response) => {
              return response.modelConfigId !== event.response.modelConfigId;
            });
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
    },
    async loadHistory(page = this.historyPage, pageSize = this.historyPageSize) {
      this.historyLoading = true;
      this.historyErrorMessage = "";

      try {
        const result = await listEvaluationTasks({ page, pageSize });
        this.historyItems = result.items;
        this.historyTotal = result.total;
        this.historyPage = result.page;
        this.historyPageSize = result.pageSize;
      } catch (error) {
        this.historyErrorMessage = error?.message || "历史任务加载失败";
      } finally {
        this.historyLoading = false;
      }
    },
    async loadHistoryTask(taskId) {
      this.historyDetailLoading = true;
      this.historyErrorMessage = "";

      try {
        this.selectedHistoryTask = await getEvaluationTask(taskId);
      } catch (error) {
        this.historyErrorMessage = error?.message || "历史任务详情加载失败";
      } finally {
        this.historyDetailLoading = false;
      }
    },
    async submitFeedback(responseId, feedbackType) {
      if (this.feedbackSubmittingIds.includes(responseId)) {
        return null;
      }

      this.feedbackSubmittingIds = [...this.feedbackSubmittingIds, responseId];
      try {
        const result = await submitResponseFeedback(responseId, { feedbackType });
        this.applyFeedbackResult(result);
        return result;
      } finally {
        this.feedbackSubmittingIds = this.feedbackSubmittingIds.filter((item) => item !== responseId);
      }
    },
    applyFeedbackResult(result) {
      this.task = updateTaskResponseFeedback(this.task, result);
      this.selectedHistoryTask = updateTaskResponseFeedback(this.selectedHistoryTask, result);
    }
  }
});

function updateTaskResponseFeedback(task, result) {
  if (!task?.responses?.length) {
    return task;
  }

  return {
    ...task,
    responses: task.responses.map((response) => {
      if (response.id !== result.responseId) {
        return response;
      }
      return {
        ...response,
        feedback: result.feedback,
        score: result.score
      };
    })
  };
}
