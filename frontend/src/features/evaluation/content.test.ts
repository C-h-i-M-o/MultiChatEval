import { describe, expect, test } from "vitest";

import { parseThinkContent, toAnswerPreview } from "./content";

describe("React 阶段三回答内容处理", () => {
  test("拆分完整 think 内容与最终回答", () => {
    expect(parseThinkContent("<think>内部推理</think>\n\n最终答案")).toEqual({
      thought: "内部推理",
      answer: "最终答案"
    });
  });

  test("未闭合 think 内容不会混入最终回答", () => {
    expect(parseThinkContent("开头\n<think>还在思考")).toEqual({
      thought: "还在思考",
      answer: "开头"
    });
  });

  test("回答预览会移除 think 与 Markdown 标记", () => {
    expect(toAnswerPreview("## 标题\n<think>隐藏</think>\n**结论**：可以\n```ts\nconst a = 1\n```")).toBe(
      "标题 结论 ：可以 代码块"
    );
  });
});
