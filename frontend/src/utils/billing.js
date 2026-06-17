export function formatMoney(value, currency = "CNY") {
  const amount = Number.isFinite(Number(value)) ? Number(value) : 0;
  const symbol = currency === "USD" ? "$" : "¥";
  return `${symbol}${amount.toFixed(6)}`;
}

export function normalizeCostDetails(response = {}) {
  const details = response.costDetails || {};
  return [
    {
      key: "input",
      label: "输入",
      tokens: response.inputTokens || 0,
      cost: details.inputCost || 0
    },
    {
      key: "output",
      label: "输出",
      tokens: response.outputTokens || 0,
      cost: details.outputCost || 0
    },
    {
      key: "cache-hit",
      label: "缓存命中",
      tokens: response.cacheHitTokens || 0,
      cost: details.cacheHitCost || 0
    },
    {
      key: "cache-creation",
      label: "缓存创建",
      tokens: response.cacheCreationTokens || 0,
      cost: details.cacheCreationCost || 0
    }
  ];
}
