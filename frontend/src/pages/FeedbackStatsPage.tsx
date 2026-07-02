import { useEffect, useState } from "react";

import { ApiError, getAdminFeedbackStats, getPersonalFeedbackStats } from "../api/client";
import type { AdminFeedbackStats, FeedbackActivityType, FeedbackStatsRange, PersonalFeedbackStats } from "../api/client";
import { useAuth } from "../features/auth/AuthContext";
import { formatHistoryTime } from "../features/history/history";

const ranges: Array<{ value: FeedbackStatsRange; label: string }> = [
  { value: "7d", label: "近 7 天" },
  { value: "30d", label: "近 30 天" },
  { value: "all", label: "全部" }
];

export function FeedbackStatsPage() {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";
  const [range, setRange] = useState<FeedbackStatsRange>("30d");
  const [activityType, setActivityType] = useState<FeedbackActivityType>("all");
  const [activityPage, setActivityPage] = useState(1);
  const [stats, setStats] = useState<PersonalFeedbackStats | AdminFeedbackStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    void loadStats();
  }, [range, activityType, activityPage, isAdmin]);

  async function loadStats(): Promise<void> {
    setLoading(true);
    setErrorMessage("");
    try {
      setStats(
        isAdmin
          ? await getAdminFeedbackStats({ range, activityType, page: activityPage, pageSize: 20 })
          : await getPersonalFeedbackStats(range)
      );
    } catch (error) {
      setStats(null);
      setErrorMessage(getErrorMessage(error, "反馈统计加载失败"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="feedback-page">
      <header className="page-head">
        <div>
          <p className="eyebrow">{isAdmin ? "System Signals" : "My Signals"}</p>
          <h2>{isAdmin ? "全局反馈统计" : "我的反馈统计"}</h2>
        </div>
        <div className="toolbar">
          {ranges.map((item) => (
            <button key={item.value} type="button" className={range === item.value ? "selected" : ""} onClick={() => { setRange(item.value); setActivityPage(1); }}>
              {item.label}
            </button>
          ))}
          <button type="button" onClick={() => void loadStats()}>{loading ? "刷新中" : "刷新"}</button>
        </div>
      </header>
      {errorMessage ? <p className="alert-message error">{errorMessage}</p> : null}
      {stats ? (
        <>
          <section className="kpi-grid">
            <Kpi label="评测任务" value={formatInteger(stats.summary.taskCount)} note="当前范围内创建" />
            <Kpi label="平均最终分" value={formatScore(stats.summary.averageFinalScore)} note={`${stats.summary.scoredCount} 条有效评分`} />
            <Kpi label="模型调用" value={formatInteger(stats.summary.callCount)} note="含成功与失败回答" />
            <Kpi label="点赞率" value={formatRate(stats.summary.likeRate)} note={`${stats.summary.likeCount} 赞 · ${stats.summary.dislikeCount} 踩`} />
            <Kpi label="评论" value={formatInteger(stats.summary.commentCount)} note="评论不参与评分" />
          </section>
          {"myInteractions" in stats ? (
            <section className="summary-grid">
              <article><span>我点过赞</span><strong>{stats.myInteractions.likeCount}</strong></article>
              <article><span>我点过踩</span><strong>{stats.myInteractions.dislikeCount}</strong></article>
              <article><span>我发过评论</span><strong>{stats.myInteractions.commentCount}</strong></article>
            </section>
          ) : null}
          <section className="feedback-section">
            <div className="section-head"><div><p className="panel-label">Model Ledger</p><h3>模型表现账本</h3></div></div>
            <div className="table-list">
              {stats.models.map((model) => (
                <article key={`${model.modelConfigId ?? "legacy"}:${model.modelName}`} className="table-row-card">
                  <div><strong>{model.modelName}</strong><span>调用 / 已评分：{model.callCount} / {model.scoredCount}</span></div>
                  <div className="table-row-meta">
                    <i>最终 {formatScore(model.averageFinalScore)}</i>
                    <i>规则 {formatScore(model.averageRuleScore)}</i>
                    <i>Judge {formatScore(model.averageJudgeScore)}</i>
                    <i>{formatRate(model.likeRate)}</i>
                  </div>
                </article>
              ))}
              {stats.models.length === 0 ? <p className="empty-note">当前范围内暂无模型数据。</p> : null}
            </div>
          </section>
          <section className="feedback-section">
            <div className="section-head"><div><p className="panel-label">Daily Pulse</p><h3>每日反馈脉冲</h3></div></div>
            <div className="trend-list">
              {stats.trend.map((point) => (
                <article key={point.date} className="trend-row">
                  <time>{point.date}</time>
                  <span>均分 {formatScore(point.averageFinalScore)}</span>
                  <strong>{point.callCount} 调用 · {point.likeCount} 赞 · {point.dislikeCount} 踩 · {point.commentCount} 评</strong>
                </article>
              ))}
              {stats.trend.length === 0 ? <p className="empty-note">当前范围内暂无趋势数据。</p> : null}
            </div>
          </section>
          {isAdmin && "activities" in stats ? (
            <section className="feedback-section">
              <div className="section-head">
                <div><p className="panel-label">Audit Stream</p><h3>最近互动明细</h3></div>
                <select value={activityType} onChange={(event) => { setActivityType(event.target.value as FeedbackActivityType); setActivityPage(1); }}>
                  <option value="all">全部互动</option>
                  <option value="like">点赞</option>
                  <option value="dislike">点踩</option>
                  <option value="comment">评论</option>
                </select>
              </div>
              <div className="table-list">
                {stats.activities.items.map((activity) => (
                  <article key={`${activity.activityType}:${activity.activityId}`} className="table-row-card">
                    <div>
                      <strong>{activityLabel(activity.activityType)} · {activity.username}</strong>
                      <span>{activity.modelName} · {formatHistoryTime(activity.createdAt)}</span>
                      <small>{activity.prompt}</small>
                    </div>
                    <p>{activity.content || "-"}</p>
                  </article>
                ))}
              </div>
              <nav className="pagination">
                <button type="button" disabled={activityPage <= 1} onClick={() => setActivityPage((page) => page - 1)}>上一页</button>
                <span>{activityPage}</span>
                <button type="button" disabled={activityPage * 20 >= stats.activities.total} onClick={() => setActivityPage((page) => page + 1)}>下一页</button>
              </nav>
            </section>
          ) : null}
        </>
      ) : !loading ? <p className="empty-note">反馈统计暂时不可用。</p> : null}
    </section>
  );
}

function Kpi({ label, value, note }: { label: string; value: string; note: string }) {
  return <article><span>{label}</span><strong>{value}</strong><small>{note}</small></article>;
}

function formatInteger(value: number): string {
  return Number(value || 0).toLocaleString("zh-CN");
}

function formatScore(value: number | null): string {
  return value === null || value === undefined ? "-" : value.toFixed(2);
}

function formatRate(value: number | null): string {
  return value === null || value === undefined ? "暂无反馈" : `${(value * 100).toFixed(1)}%`;
}

function activityLabel(type: string): string {
  return { like: "点赞", dislike: "点踩", comment: "评论" }[type] || type;
}

function getErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof ApiError || error instanceof Error) {
    return error.message || fallback;
  }
  return fallback;
}
