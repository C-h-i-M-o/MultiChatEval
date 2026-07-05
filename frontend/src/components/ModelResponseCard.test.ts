import { describe, expect, test } from "vitest";

import { JUDGE_SCORE_WEIGHT_LABEL, JUDGE_STABILITY_THRESHOLD_LABEL, isNearScrollBottom, scoreStatusText } from "./ModelResponseCard";

describe("ModelResponseCard 自动滚动判断", () => {
  test("视口接近底部时允许自动滚动", () => {
    expect(isNearScrollBottom({ scrollTop: 460, clientHeight: 500, scrollHeight: 980 })).toBe(true);
  });

  test("用户向上查看内容时不自动滚动", () => {
    expect(isNearScrollBottom({ scrollTop: 120, clientHeight: 500, scrollHeight: 980 })).toBe(false);
  });

  test("五种评分状态都有明确文案", () => {
    expect(scoreStatusText("scored")).toBe("已计入统计");
    expect(scoreStatusText("judge_failed")).toContain("LLM 评分失败");
    expect(scoreStatusText("judge_unstable")).toContain("有效评分分歧较大");
    expect(scoreStatusText("judge_disabled")).toContain("关闭 LLM 评分");
    expect(scoreStatusText("model_failed")).toContain("模型调用失败");
  });

  test("LLM 评审详情展示 70% 权重", () => {
    expect(JUDGE_SCORE_WEIGHT_LABEL).toBe("70%");
  });

  test("LLM 评审详情展示 2.0 稳定阈值", () => {
    expect(JUDGE_STABILITY_THRESHOLD_LABEL).toBe("2.0");
  });
});
