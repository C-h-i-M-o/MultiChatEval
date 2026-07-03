import type { EvaluationTaskRead, FeedbackToggleResult } from "../evaluation/types";

const HISTORY_PENDING_TIMEOUT_MS = 120 * 1000;
type HistoryStatusSource = {
  status: string;
  createdAt?: string | null;
  completedAt?: string | null;
};

export function historyStatusText(taskItem: HistoryStatusSource, now = new Date()): string {
  if (isStalePendingTask(taskItem, now)) {
    return "超时未完成";
  }
  if (taskItem.status === "completed") {
    return "已完成";
  }
  if (taskItem.status === "failed") {
    return "失败";
  }
  return "进行中";
}

export function historyStatusClass(
  taskItem: HistoryStatusSource,
  now = new Date()
): string {
  if (isStalePendingTask(taskItem, now) || taskItem.status === "failed") {
    return "failed";
  }
  if (taskItem.status === "completed") {
    return "completed";
  }
  return "running";
}

export function isStalePendingTask(
  taskItem: HistoryStatusSource,
  now = new Date()
): boolean {
  if (taskItem.status !== "pending" || taskItem.completedAt || !taskItem.createdAt) {
    return false;
  }
  const createdAt = parseBackendTime(taskItem.createdAt);
  if (Number.isNaN(createdAt.getTime())) {
    return false;
  }
  return now.getTime() - createdAt.getTime() >= HISTORY_PENDING_TIMEOUT_MS;
}

export function formatHistoryTime(value: string | null | undefined): string {
  if (!value) {
    return "未知时间";
  }
  return new Intl.DateTimeFormat("zh-CN", {
    timeZone: "Asia/Shanghai",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false
  }).format(parseBackendTime(value));
}

export function parseBackendTime(value: string): Date {
  const hasTimezone = /(?:Z|[+-]\d{2}:?\d{2})$/.test(value);
  return new Date(hasTimezone ? value : `${value}Z`);
}

export function updateTaskResponseFeedback(
  task: EvaluationTaskRead,
  result: FeedbackToggleResult
): EvaluationTaskRead {
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
