import test from "node:test";
import assert from "node:assert/strict";

import { formatMoney, normalizeCostDetails } from "../src/utils/billing.js";
import { providerPresets, visibleProviderPresets } from "../src/utils/providerPresets.js";

test("formatMoney uses the configured currency without exchange conversion", () => {
  assert.equal(formatMoney(0.004218, "USD"), "$0.004218");
  assert.equal(formatMoney(1.25, "CNY"), "¥1.250000");
});

test("normalizeCostDetails fills missing token and cost categories with zero", () => {
  assert.deepEqual(normalizeCostDetails({ outputTokens: 12 }), [
    { key: "input", label: "输入", tokens: 0, cost: 0 },
    { key: "output", label: "输出", tokens: 12, cost: 0 },
    { key: "cache-hit", label: "缓存命中", tokens: 0, cost: 0 },
    { key: "cache-creation", label: "缓存创建", tokens: 0, cost: 0 }
  ]);
});

test("provider presets expose three default choices and the compatible blank template", () => {
  assert.deepEqual(
    visibleProviderPresets.map((preset) => preset.key),
    ["deepseek", "minimax", "glm"]
  );
  assert.equal(providerPresets.at(-1).key, "openai-compatible");
});
