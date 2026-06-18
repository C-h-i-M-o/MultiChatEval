import assert from "node:assert/strict";
import { existsSync } from "node:fs";
import test from "node:test";

const moduleUrl = new URL("../src/utils/feedbackStats.js", import.meta.url);

test("feedback stats utility module is available", () => {
  assert.equal(existsSync(moduleUrl), true);
});

test("feedback stats formatters preserve empty values", async () => {
  const { formatRate, formatScore } = await import(moduleUrl);

  assert.equal(formatScore(null), "—");
  assert.equal(formatScore(8.236), "8.24");
  assert.equal(formatRate(null), "暂无反馈");
  assert.equal(formatRate(0.875), "87.5%");
});

test("trend width uses the largest activity total as baseline", async () => {
  const { activityTotal, trendWidth } = await import(moduleUrl);
  const points = [
    { likeCount: 2, dislikeCount: 1, commentCount: 0 },
    { likeCount: 4, dislikeCount: 1, commentCount: 3 }
  ];

  assert.equal(activityTotal(points[0]), 3);
  assert.equal(trendWidth(points[0], points), "37.5%");
  assert.equal(trendWidth({ likeCount: 0, dislikeCount: 0, commentCount: 0 }, []), "0%");
});

test("activity labels distinguish feedback and comments", async () => {
  const { activityTypeLabel } = await import(moduleUrl);

  assert.equal(activityTypeLabel("like"), "点赞");
  assert.equal(activityTypeLabel("dislike"), "点踩");
  assert.equal(activityTypeLabel("comment"), "评论");
});

test("table row keys remain unique for legacy models and mixed activities", async () => {
  const { activityRowKey, modelRowKey } = await import(moduleUrl);

  assert.equal(modelRowKey({ modelConfigId: null, modelName: "历史模型" }), "legacy:历史模型");
  assert.notEqual(
    activityRowKey({ activityId: 3, activityType: "like" }),
    activityRowKey({ activityId: 3, activityType: "comment" })
  );
});
