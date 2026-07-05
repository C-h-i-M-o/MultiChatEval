import { describe, expect, test } from "vitest";

import { isNearScrollBottom, scoreStatusText } from "./ModelResponseCard";

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
    expect(scoreStatusText("judge_unstable")).toContain("分歧较大");
    expect(scoreStatusText("judge_disabled")).toContain("关闭 LLM 评分");
    expect(scoreStatusText("model_failed")).toContain("模型调用失败");
  });
});
