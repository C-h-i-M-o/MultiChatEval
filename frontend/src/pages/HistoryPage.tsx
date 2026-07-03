import { useEffect, useMemo, useState } from "react";

import { ApiError, getEvaluationTask, listEvaluationTasks, submitResponseFeedback } from "../api/client";
import type { FeedbackType } from "../api/client";
import { ModelResponseCard } from "../components/ModelResponseCard";
import type { EvaluationTaskListItem, EvaluationTaskRead } from "../features/evaluation/types";
import {
  formatHistoryTime,
  historyStatusClass,
  historyStatusText,
  isStalePendingTask,
  updateTaskResponseFeedback
} from "../features/history/history";

const defaultPageSize = 10;

export function HistoryPage() {
  const [items, setItems] = useState<EvaluationTaskListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(defaultPageSize);
  const [loading, setLoading] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [selectedTask, setSelectedTask] = useState<EvaluationTaskRead | null>(null);
  const [feedbackSubmittingIds, setFeedbackSubmittingIds] = useState<number[]>([]);

  const totalPages = Math.max(Math.ceil(total / pageSize), 1);
  const selectedHistoryItem = useMemo(
    () => items.find((taskItem) => taskItem.taskId === selectedTask?.taskId) || null,
    [items, selectedTask]
  );
  const selectedStatusSource = selectedHistoryItem || selectedTask;

  useEffect(() => {
    void loadHistory(1, defaultPageSize);
  }, []);

  async function loadHistory(nextPage: number, nextPageSize: number): Promise<void> {
    setLoading(true);
    setErrorMessage("");
    try {
      const result = await listEvaluationTasks({ page: nextPage, pageSize: nextPageSize });
      setItems(result.items);
      setTotal(result.total);
      setPage(result.page);
      setPageSize(result.pageSize);
    } catch (error) {
      setErrorMessage(getErrorMessage(error, "历史任务加载失败"));
    } finally {
      setLoading(false);
    }
  }

  async function loadHistoryTask(taskId: number): Promise<void> {
    setDetailLoading(true);
    setErrorMessage("");
    try {
      setSelectedTask(await getEvaluationTask(taskId));
    } catch (error) {
      setErrorMessage(getErrorMessage(error, "历史任务详情加载失败"));
    } finally {
      setDetailLoading(false);
    }
  }

  async function submitFeedback(responseId: number, feedbackType: FeedbackType): Promise<void> {
    if (feedbackSubmittingIds.includes(responseId) || !selectedTask) {
      return;
    }
    setFeedbackSubmittingIds((ids) => [...ids, responseId]);
    setErrorMessage("");
    try {
      const result = await submitResponseFeedback(responseId, feedbackType);
      setSelectedTask((task) => (task ? updateTaskResponseFeedback(task, result) : task));
    } catch (error) {
      setErrorMessage(getErrorMessage(error, "用户反馈提交失败"));
    } finally {
      setFeedbackSubmittingIds((ids) => ids.filter((id) => id !== responseId));
    }
  }

  return (
    <section className="history-page">
      <header className="page-head">
        <div>
          <p className="eyebrow">History</p>
          <h2>历史任务</h2>
        </div>
        <button type="button" onClick={() => void loadHistory(page, pageSize)}>
          {loading ? "刷新中" : "刷新"}
        </button>
      </header>
      {errorMessage ? <p className="alert-message error">{errorMessage}</p> : null}
      <section className="history-layout">
        <aside className="history-panel">
          <div className="history-list-head">
            <div>
              <p className="panel-label">任务列表</p>
              <h3>最近评测</h3>
            </div>
            <span>{total} 条</span>
          </div>
          <div className="history-list" aria-busy={loading}>
            {items.map((taskItem) => (
              <button
                key={taskItem.taskId}
                type="button"
                className={selectedTask?.taskId === taskItem.taskId ? "history-item active" : "history-item"}
                onClick={() => void loadHistoryTask(taskItem.taskId)}
              >
                <span className="history-item-title">{taskItem.prompt}</span>
                <span className="history-item-meta">
                  {taskItem.ownerUsername} · {formatHistoryTime(taskItem.createdAt)} · {taskItem.responseCount} 个回答
                </span>
                <span className="history-item-tags">
                  <i>{taskItem.visibility === "private" ? "私有" : "公开"}</i>
                  <i className={historyStatusClass(taskItem)}>{historyStatusText(taskItem)}</i>
                </span>
              </button>
            ))}
            {!loading && items.length === 0 ? <p className="empty-note">暂无历史任务。</p> : null}
          </div>
          <div className="pagination">
            <select
              value={pageSize}
              onChange={(event) => void loadHistory(1, Number(event.target.value))}
            >
              {[10, 20, 50].map((size) => (
                <option key={size} value={size}>
                  {size} / 页
                </option>
              ))}
            </select>
            <button type="button" disabled={page <= 1} onClick={() => void loadHistory(page - 1, pageSize)}>
              上一页
            </button>
            <span>
              {page} / {totalPages}
            </span>
            <button type="button" disabled={page >= totalPages} onClick={() => void loadHistory(page + 1, pageSize)}>
              下一页
            </button>
          </div>
        </aside>
        <section className="history-detail" aria-busy={detailLoading}>
          {!selectedTask ? (
            <p className="empty-note">请选择一个历史任务。</p>
          ) : (
            <div className="history-detail-body">
              <div className="history-detail-head">
                <div>
                  <p className="panel-label">任务详情</p>
                  <h3>{selectedTask.prompt}</h3>
                  <p>
                    {selectedTask.ownerUsername} · {selectedTask.visibility === "private" ? "私有评测" : "公开评测"}
                  </p>
                </div>
                {selectedStatusSource ? (
                  <span className={`status-badge ${historyStatusClass(selectedStatusSource)}`}>
                    {historyStatusText(selectedStatusSource)}
                  </span>
                ) : null}
              </div>
              {selectedTask.responses.length === 0 ? (
                <EmptyHistoryDetail task={selectedTask} />
              ) : (
                <div className="history-response-list">
                  {selectedTask.responses.map((response) => (
                    <ModelResponseCard
                      key={response.id}
                      response={response}
                      elapsedSeconds={0}
                      feedbackSubmitting={feedbackSubmittingIds.includes(response.id)}
                      showComments
                      onFeedback={(responseId, feedbackType) => void submitFeedback(responseId, feedbackType)}
                    />
                  ))}
                </div>
              )}
            </div>
          )}
        </section>
      </section>
    </section>
  );
}

function EmptyHistoryDetail({ task }: { task: EvaluationTaskRead }) {
  const stale = isStalePendingTask({
    status: task.status,
    createdAt: task.createdAt || "",
    completedAt: task.completedAt || null
  });
  const title = stale ? "任务超时未完成" : task.status === "pending" || task.status === "running" ? "模型回答仍在生成" : "暂无模型回答";
  const description = stale
    ? "该任务超过等待时间后仍未产生模型回答，可以刷新历史任务或重新发起评测。"
    : task.status === "pending" || task.status === "running"
      ? "模型请求尚未完成，可以稍后重新加载详情查看最新结果。"
      : "该任务没有可展示的模型回答。";

  return (
    <div className="history-empty-detail">
      <p className="panel-label">{historyStatusText({ status: task.status, createdAt: task.createdAt || "", completedAt: task.completedAt })}</p>
      <h4>{title}</h4>
      <p>{description}</p>
    </div>
  );
}

function getErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof ApiError || error instanceof Error) {
    return error.message || fallback;
  }
  return fallback;
}
