import { useEffect, useMemo, useState } from "react";
import { Button, Card, Col, Pagination, Row, Segmented, Select, Space, Statistic, Table, Tag, message } from "antd";
import type { TableColumnsType } from "antd";
import { Bar, CartesianGrid, ComposedChart, Legend, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { ApiError, getAdminFeedbackStats, getPersonalFeedbackStats } from "../api/client";
import type {
  AdminFeedbackStats,
  FeedbackActivity,
  FeedbackActivityType,
  FeedbackModelStats,
  FeedbackStatsRange,
  FeedbackTrendPoint,
  PersonalFeedbackStats
} from "../api/client";
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
  const [modelConfigId, setModelConfigId] = useState<number | null>(null);
  const [activityPage, setActivityPage] = useState(1);
  const [activityPageSize, setActivityPageSize] = useState(20);
  const [stats, setStats] = useState<PersonalFeedbackStats | AdminFeedbackStats | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    void loadStats();
  }, [range, activityType, modelConfigId, activityPage, activityPageSize, isAdmin]);

  const modelColumns = useMemo<TableColumnsType<FeedbackModelStats>>(
    () => [
      { title: "模型", dataIndex: "modelName", fixed: "left", width: 170 },
      { title: "调用 / 已评分", render: (_, row) => `${row.callCount} / ${row.scoredCount}`, width: 130 },
      { title: "最终分", render: (_, row) => formatScore(row.averageFinalScore), width: 90 },
      { title: "规则分", render: (_, row) => formatScore(row.averageRuleScore), width: 90 },
      { title: "Judge", render: (_, row) => formatScore(row.averageJudgeScore), width: 90 },
      { title: "点赞率", render: (_, row) => formatRate(row.likeRate), width: 110 },
      { title: "赞 / 踩 / 评", render: (_, row) => `${row.likeCount} / ${row.dislikeCount} / ${row.commentCount}`, width: 125 }
    ],
    []
  );
  const activityColumns = useMemo<TableColumnsType<FeedbackActivity>>(
    () => [
      {
        title: "类型",
        dataIndex: "activityType",
        width: 88,
        render: (type: FeedbackActivity["activityType"]) => <Tag color={activityColor(type)}>{activityLabel(type)}</Tag>
      },
      { title: "用户", dataIndex: "username", width: 110 },
      { title: "模型", dataIndex: "modelName", width: 150 },
      { title: "问题", dataIndex: "prompt", ellipsis: true },
      { title: "内容", dataIndex: "content", ellipsis: true, render: (value: string | null) => value || "-" },
      { title: "时间", dataIndex: "createdAt", width: 170, render: (value: string) => formatHistoryTime(value) }
    ],
    []
  );

  async function loadStats(): Promise<void> {
    setLoading(true);
    try {
      setStats(
        isAdmin
          ? await getAdminFeedbackStats({ range, activityType, modelConfigId, page: activityPage, pageSize: activityPageSize })
          : await getPersonalFeedbackStats(range)
      );
    } catch (error) {
      setStats(null);
      message.error(getErrorMessage(error, "反馈统计加载失败"));
    } finally {
      setLoading(false);
    }
  }

  function resetRange(nextRange: FeedbackStatsRange): void {
    setRange(nextRange);
    setActivityPage(1);
  }

  const modelOptions = stats?.models
    .filter((model) => model.modelConfigId !== null)
    .map((model) => ({ value: model.modelConfigId as number, label: model.modelName })) ?? [];

  return (
    <section className="feedback-page">
      <header className="page-head">
        <div>
          <p className="eyebrow">{isAdmin ? "System Signals" : "My Signals"}</p>
          <h2>{isAdmin ? "全局反馈统计" : "我的反馈统计"}</h2>
        </div>
        <Space wrap>
          <Segmented<FeedbackStatsRange> options={ranges} value={range} onChange={resetRange} />
          <Button loading={loading} onClick={() => void loadStats()}>刷新</Button>
        </Space>
      </header>
      {stats ? (
        <>
          <div className="feedback-kpi-row">
            <Kpi title="评测任务" value={stats.summary.taskCount} suffix="项" />
            <Kpi title="平均最终分" value={formatScore(stats.summary.averageFinalScore)} suffix="" />
            <Kpi title="模型调用" value={stats.summary.callCount} suffix="次" />
            <Kpi title="点赞率" value={formatRate(stats.summary.likeRate)} suffix="" />
            <Kpi title="评论" value={stats.summary.commentCount} suffix="条" />
          </div>
          {"myInteractions" in stats ? (
            <div className="feedback-kpi-row feedback-kpi-row-compact">
              <Kpi title="我点过赞" value={stats.myInteractions.likeCount} suffix="次" />
              <Kpi title="我点过踩" value={stats.myInteractions.dislikeCount} suffix="次" />
              <Kpi title="我发过评论" value={stats.myInteractions.commentCount} suffix="条" />
            </div>
          ) : null}
          <Card title="每日反馈脉冲" className="feedback-section">
            {stats.trend.length > 0 ? <TrendChart points={stats.trend} /> : <p className="empty-note">当前范围内暂无趋势数据。</p>}
          </Card>
          <Row gutter={[16, 16]} align="top">
            <Col xs={24} xl={isAdmin ? 12 : 24}>
              <Card title="模型互动" className="feedback-section" extra={<span>均分仅计算已有评分数据</span>}>
                <Table
                  rowKey={(row) => `${row.modelConfigId ?? "legacy"}:${row.modelName}`}
                  columns={modelColumns}
                  dataSource={stats.models}
                  pagination={false}
                  scroll={{ x: 805 }}
                />
              </Card>
            </Col>
            {isAdmin && "activities" in stats ? (
              <Col xs={24} xl={12}>
                <Card
                  title="互动明细"
                  className="feedback-section"
                  extra={
                    <Space wrap>
                      <Select<FeedbackActivityType>
                        value={activityType}
                        style={{ width: 116 }}
                        options={[
                          { value: "all", label: "全部互动" },
                          { value: "like", label: "点赞" },
                          { value: "dislike", label: "点踩" },
                          { value: "comment", label: "评论" }
                        ]}
                        onChange={(value) => { setActivityType(value); setActivityPage(1); }}
                      />
                      <Select
                        allowClear
                        placeholder="全部模型"
                        value={modelConfigId}
                        style={{ width: 150 }}
                        options={modelOptions}
                        onChange={(value: number | null) => { setModelConfigId(value ?? null); setActivityPage(1); }}
                      />
                    </Space>
                  }
                >
                  <Table
                    rowKey={(row) => `${row.activityType}:${row.activityId}`}
                    columns={activityColumns}
                    dataSource={stats.activities.items}
                    pagination={false}
                    scroll={{ x: 760 }}
                  />
                  <Pagination
                    className="feedback-pagination"
                    total={stats.activities.total}
                    current={activityPage}
                    pageSize={activityPageSize}
                    showSizeChanger
                    pageSizeOptions={[10, 20, 50]}
                    onChange={(page, size) => { setActivityPage(page); setActivityPageSize(size); }}
                  />
                </Card>
              </Col>
            ) : null}
          </Row>
        </>
      ) : !loading ? <p className="empty-note">反馈统计暂时不可用。</p> : null}
    </section>
  );
}

function Kpi({ title, value, suffix }: { title: string; value: number | string; suffix: string }) {
  return (
    <Card><Statistic title={title} value={value} suffix={suffix} /></Card>
  );
}

function TrendChart({ points }: { points: FeedbackTrendPoint[] }) {
  const data = points.map((point) => ({
    ...point,
    label: formatTrendDate(point.date),
    averageFinalScore: point.averageFinalScore ?? 0
  }));
  return (
    <div className="feedback-chart">
      <ResponsiveContainer width="100%" height={320}>
        <ComposedChart data={data} margin={{ top: 12, right: 18, bottom: 12, left: 0 }}>
          <CartesianGrid stroke="#e2dccf" strokeDasharray="4 4" />
          <XAxis dataKey="label" />
          <YAxis yAxisId="count" allowDecimals={false} />
          <YAxis yAxisId="score" orientation="right" domain={[0, 10]} />
          <Tooltip />
          <Legend />
          <Bar yAxisId="count" dataKey="callCount" name="调用" fill="#16616a" radius={[6, 6, 0, 0]} />
          <Bar yAxisId="count" dataKey="likeCount" name="点赞" fill="#7fa36a" radius={[6, 6, 0, 0]} />
          <Bar yAxisId="count" dataKey="dislikeCount" name="点踩" fill="#bc442b" radius={[6, 6, 0, 0]} />
          <Bar yAxisId="count" dataKey="commentCount" name="评论" fill="#e5b85d" radius={[6, 6, 0, 0]} />
          <Line yAxisId="score" type="monotone" dataKey="averageFinalScore" name="平均最终分" stroke="#17232a" strokeWidth={2} dot />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}

function formatScore(value: number | null): string {
  return value === null || value === undefined ? "-" : value.toFixed(2);
}

function formatRate(value: number | null): string {
  return value === null || value === undefined ? "暂无反馈" : `${(value * 100).toFixed(1)}%`;
}

function formatTrendDate(value: string): string {
  return new Intl.DateTimeFormat("zh-CN", {
    timeZone: "Asia/Shanghai",
    month: "2-digit",
    day: "2-digit"
  }).format(new Date(`${value}T00:00:00+08:00`));
}

function activityLabel(type: string): string {
  return { like: "点赞", dislike: "点踩", comment: "评论" }[type] || type;
}

function activityColor(type: string): string {
  return { like: "success", dislike: "error", comment: "processing" }[type] || "default";
}

function getErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof ApiError || error instanceof Error) {
    return error.message || fallback;
  }
  return fallback;
}
