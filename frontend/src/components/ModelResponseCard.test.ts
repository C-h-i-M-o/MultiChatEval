import { describe, expect, test } from "vitest";

import { isNearScrollBottom } from "./ModelResponseCard";

describe("ModelResponseCard 自动滚动判断", () => {
  test("视口接近底部时允许自动滚动", () => {
    expect(isNearScrollBottom({ scrollTop: 460, clientHeight: 500, scrollHeight: 980 })).toBe(true);
  });

  test("用户向上查看内容时不自动滚动", () => {
    expect(isNearScrollBottom({ scrollTop: 120, clientHeight: 500, scrollHeight: 980 })).toBe(false);
  });
});
