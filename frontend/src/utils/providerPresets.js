export const providerPresets = [
  {
    key: "deepseek",
    label: "DeepSeek",
    providerName: "deepseek",
    baseUrl: "https://api.deepseek.com",
    description: "适用于 DeepSeek 官方 OpenAI-compatible API。",
    consoleUrl: "https://platform.deepseek.com/",
    docsUrl: "https://api-docs.deepseek.com/quick_start/pricing"
  },
  {
    key: "minimax",
    label: "MiniMax",
    providerName: "minimax",
    baseUrl: "https://api.minimaxi.com/v1",
    description: "适用于 MiniMax 文本模型的 OpenAI-compatible 接口。",
    consoleUrl: "https://platform.minimaxi.com/user-center/basic-information",
    docsUrl: "https://platform.minimaxi.com/docs/pricing/overview"
  },
  {
    key: "glm",
    label: "智谱 GLM",
    providerName: "glm",
    baseUrl: "https://open.bigmodel.cn/api/paas/v4",
    description: "适用于智谱开放平台 GLM 系列模型。",
    consoleUrl: "https://open.bigmodel.cn/usercenter/apikeys",
    docsUrl: "https://open.bigmodel.cn/dev/api"
  },
  {
    key: "qwen",
    label: "阿里 Qwen",
    providerName: "qwen",
    baseUrl: "https://dashscope.aliyuncs.com/compatible-mode/v1",
    description: "适用于阿里云百炼的 OpenAI-compatible 模式。",
    consoleUrl: "https://bailian.console.aliyun.com/",
    docsUrl: "https://help.aliyun.com/zh/model-studio/model-pricing"
  },
  {
    key: "xiaomi-mimo",
    label: "Xiaomi MiMo",
    providerName: "xiaomi-mimo",
    baseUrl: "https://api.xiaomimimo.com/v1",
    description: "适用于 Xiaomi MiMo 开放平台官方 API。",
    consoleUrl: "https://platform.xiaomimimo.com/",
    docsUrl: "https://platform.xiaomimimo.com/"
  },
  {
    key: "openai",
    label: "OpenAI",
    providerName: "openai",
    baseUrl: "https://api.openai.com/v1",
    description: "适用于 OpenAI 官方 Chat Completions 兼容模型。",
    consoleUrl: "https://platform.openai.com/api-keys",
    docsUrl: "https://developers.openai.com/api/docs/pricing"
  },
  {
    key: "openai-compatible",
    label: "OpenAI-compatible",
    providerName: "",
    baseUrl: "",
    description: "用于其他兼容 /chat/completions 的供应商，所有字段需要手动填写。",
    consoleUrl: "",
    docsUrl: ""
  }
];

export const visibleProviderPresets = providerPresets.slice(0, 3);
export const collapsedProviderPresets = providerPresets.slice(3);
