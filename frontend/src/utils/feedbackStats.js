export const feedbackRangeOptions = [
  { value: "7d", label: "近 7 天" },
  { value: "30d", label: "近 30 天" },
  { value: "all", label: "全部" }
];

export function formatScore(value) {
  return value === null || value === undefined ? "—" : Number(value).toFixed(2);
}

export function formatRate(value) {
  return value === null || value === undefined ? "暂无反馈" : `${(Number(value) * 100).toFixed(1)}%`;
}

export function activityTotal(point = {}) {
  return (point.likeCount || 0) + (point.dislikeCount || 0) + (point.commentCount || 0);
}

export function trendWidth(point, points) {
  const maximum = Math.max(0, ...points.map(activityTotal));
  if (!maximum) {
    return "0%";
  }
  return `${((activityTotal(point) / maximum) * 100).toFixed(1)}%`;
}

export function activityTypeLabel(type) {
  return {
    like: "点赞",
    dislike: "点踩",
    comment: "评论"
  }[type] || type;
}

export function modelRowKey(model) {
  return `${model.modelConfigId ?? "legacy"}:${model.modelName}`;
}

export function activityRowKey(activity) {
  return `${activity.activityType}:${activity.activityId}`;
}
