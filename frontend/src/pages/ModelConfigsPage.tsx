import { useEffect, useState } from "react";

import {
  ApiError,
  createModelConfig,
  deleteModelConfig,
  listModelConfigs,
  testModelConfig,
  updateModelConfig
} from "../api/client";
import type { ModelConfig, ModelConfigPayload } from "../api/client";

const providerPresets = [
  { key: "deepseek", label: "DeepSeek", providerName: "deepseek", baseUrl: "https://api.deepseek.com" },
  { key: "minimax", label: "MiniMax", providerName: "minimax", baseUrl: "https://api.minimaxi.com/v1" },
  { key: "glm", label: "智谱 GLM", providerName: "glm", baseUrl: "https://open.bigmodel.cn/api/paas/v4" },
  { key: "qwen", label: "阿里 Qwen", providerName: "qwen", baseUrl: "https://dashscope.aliyuncs.com/compatible-mode/v1" },
  { key: "openai", label: "OpenAI", providerName: "openai", baseUrl: "https://api.openai.com/v1" },
  { key: "custom", label: "OpenAI-compatible", providerName: "", baseUrl: "" }
];

const emptyForm: Required<ModelConfigPayload> = {
  providerName: "",
  displayName: "",
  modelName: "",
  baseUrl: "",
  apiKey: "",
  enabled: true,
  maxTokens: 1024,
  temperature: 0.7,
  timeoutSeconds: 60,
  notes: "",
  currency: "CNY",
  priceInput: 0,
  priceOutput: 0,
  priceCacheHit: 0,
  priceCacheCreation: 0
};

export function ModelConfigsPage() {
  const [configs, setConfigs] = useState<ModelConfig[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [testingId, setTestingId] = useState<number | "draft" | null>(null);
  const [editingConfig, setEditingConfig] = useState<ModelConfig | null>(null);
  const [form, setForm] = useState<Required<ModelConfigPayload>>(emptyForm);
  const [errorMessage, setErrorMessage] = useState("");
  const [noticeMessage, setNoticeMessage] = useState("");

  useEffect(() => {
    void loadConfigs();
  }, []);

  async function loadConfigs(): Promise<void> {
    setLoading(true);
    setErrorMessage("");
    try {
      setConfigs(await listModelConfigs());
    } catch (error) {
      setErrorMessage(getErrorMessage(error, "模型配置加载失败"));
    } finally {
      setLoading(false);
    }
  }

  function startCreate(): void {
    const firstPreset = providerPresets[0];
    setEditingConfig(null);
    setForm({ ...emptyForm, providerName: firstPreset.providerName, baseUrl: firstPreset.baseUrl });
    setNoticeMessage("");
  }

  function startEdit(config: ModelConfig): void {
    setEditingConfig(config);
    setForm({
      providerName: config.providerName,
      displayName: config.displayName,
      modelName: config.modelName,
      baseUrl: config.baseUrl,
      apiKey: "",
      enabled: config.enabled,
      maxTokens: config.maxTokens,
      temperature: config.temperature,
      timeoutSeconds: config.timeoutSeconds,
      notes: config.notes,
      currency: config.currency,
      priceInput: config.priceInput,
      priceOutput: config.priceOutput,
      priceCacheHit: config.priceCacheHit,
      priceCacheCreation: config.priceCacheCreation
    });
    setNoticeMessage("");
  }

  async function saveConfig(): Promise<void> {
    if (!form.providerName.trim() || !form.displayName.trim() || !form.modelName.trim() || !form.baseUrl.trim()) {
      setErrorMessage("请填写供应商、展示名、模型名和 Base URL");
      return;
    }
    setSaving(true);
    setErrorMessage("");
    try {
      const payload = buildPayload(form, !editingConfig);
      if (editingConfig) {
        await updateModelConfig(editingConfig.id, payload);
      } else {
        await createModelConfig(payload);
      }
      setNoticeMessage("模型配置已保存");
      await loadConfigs();
      startCreate();
    } catch (error) {
      setErrorMessage(getErrorMessage(error, "模型配置保存失败"));
    } finally {
      setSaving(false);
    }
  }

  async function toggleEnabled(config: ModelConfig): Promise<void> {
    setErrorMessage("");
    try {
      await updateModelConfig(config.id, { enabled: !config.enabled });
      await loadConfigs();
    } catch (error) {
      setErrorMessage(getErrorMessage(error, "启用状态更新失败"));
    }
  }

  async function removeConfig(config: ModelConfig): Promise<void> {
    if (!window.confirm(`确认删除 ${config.displayName}？历史回答会保留模型快照。`)) {
      return;
    }
    setErrorMessage("");
    try {
      await deleteModelConfig(config.id);
      await loadConfigs();
    } catch (error) {
      setErrorMessage(getErrorMessage(error, "模型配置删除失败"));
    }
  }

  async function testConfig(config?: ModelConfig): Promise<void> {
    setTestingId(config?.id ?? "draft");
    setErrorMessage("");
    setNoticeMessage("");
    try {
      const result = await testModelConfig(config ? { modelConfigId: config.id } : buildTestPayload(form, editingConfig?.id));
      result.success
        ? setNoticeMessage(`${result.message}，耗时 ${result.latencyMs}ms`)
        : setErrorMessage(result.message);
    } catch (error) {
      setErrorMessage(getErrorMessage(error, "连接测试失败"));
    } finally {
      setTestingId(null);
    }
  }

  return (
    <section className="admin-page">
      <header className="page-head">
        <div>
          <p className="eyebrow">Model Providers</p>
          <h2>模型配置</h2>
        </div>
        <button type="button" onClick={() => void loadConfigs()}>
          {loading ? "刷新中" : "刷新"}
        </button>
      </header>
      {errorMessage ? <p className="alert-message error">{errorMessage}</p> : null}
      {noticeMessage ? <p className="alert-message success">{noticeMessage}</p> : null}
      <section className="admin-grid">
        <div className="admin-table-panel">
          <div className="section-head">
            <div>
              <p className="panel-label">配置列表</p>
              <h3>可调用模型</h3>
            </div>
            <span>{configs.length} 项</span>
          </div>
          <div className="table-list">
            {configs.map((config) => (
              <article key={config.id} className="table-row-card">
                <div>
                  <strong>{config.displayName}</strong>
                  <span>{config.providerName} · {config.modelName}</span>
                  <small>{config.baseUrl}</small>
                </div>
                <div className="table-row-meta">
                  <i>{config.currency}</i>
                  <i>{config.hasApiKey ? config.maskedApiKey : "未配置密钥"}</i>
                  <i className={config.enabled ? "completed" : "failed"}>{config.enabled ? "启用" : "禁用"}</i>
                </div>
                <div className="row-actions">
                  <button type="button" onClick={() => startEdit(config)}>编辑</button>
                  <button type="button" disabled={testingId === config.id} onClick={() => void testConfig(config)}>
                    {testingId === config.id ? "测试中" : "测试"}
                  </button>
                  <button type="button" onClick={() => void toggleEnabled(config)}>
                    {config.enabled ? "禁用" : "启用"}
                  </button>
                  <button type="button" className="danger" onClick={() => void removeConfig(config)}>删除</button>
                </div>
              </article>
            ))}
            {!loading && configs.length === 0 ? <p className="empty-note">暂无模型配置。</p> : null}
          </div>
        </div>
        <ModelConfigForm
          form={form}
          editingConfig={editingConfig}
          saving={saving}
          testingDraft={testingId === "draft"}
          onChange={setForm}
          onSave={() => void saveConfig()}
          onTest={() => void testConfig()}
          onCreate={startCreate}
        />
      </section>
    </section>
  );
}

function ModelConfigForm({
  form,
  editingConfig,
  saving,
  testingDraft,
  onChange,
  onSave,
  onTest,
  onCreate
}: {
  form: Required<ModelConfigPayload>;
  editingConfig: ModelConfig | null;
  saving: boolean;
  testingDraft: boolean;
  onChange: (form: Required<ModelConfigPayload>) => void;
  onSave: () => void;
  onTest: () => void;
  onCreate: () => void;
}) {
  function patch(next: Partial<Required<ModelConfigPayload>>): void {
    onChange({ ...form, ...next });
  }

  return (
    <form className="admin-form" onSubmit={(event) => { event.preventDefault(); onSave(); }}>
      <div className="section-head">
        <div>
          <p className="panel-label">{editingConfig ? "编辑配置" : "新增配置"}</p>
          <h3>{editingConfig ? editingConfig.displayName : "新模型"}</h3>
        </div>
        <button type="button" onClick={onCreate}>新建</button>
      </div>
      {!editingConfig ? (
        <div className="preset-grid">
          {providerPresets.map((preset) => (
            <button
              key={preset.key}
              type="button"
              className={form.providerName === preset.providerName && form.baseUrl === preset.baseUrl ? "selected" : ""}
              onClick={() => patch({ providerName: preset.providerName, baseUrl: preset.baseUrl })}
            >
              {preset.label}
            </button>
          ))}
        </div>
      ) : null}
      <div className="form-grid">
        <TextField label="供应商" value={form.providerName} onChange={(value) => patch({ providerName: value })} />
        <TextField label="展示名" value={form.displayName} onChange={(value) => patch({ displayName: value })} />
        <TextField label="模型名" value={form.modelName} onChange={(value) => patch({ modelName: value })} />
        <TextField label="Base URL" value={form.baseUrl} onChange={(value) => patch({ baseUrl: value })} />
        <TextField label="API Key" type="password" value={form.apiKey || ""} onChange={(value) => patch({ apiKey: value })} />
        <NumberField label="最大输出" value={form.maxTokens} onChange={(value) => patch({ maxTokens: value })} />
        <NumberField label="温度" value={form.temperature} step={0.1} onChange={(value) => patch({ temperature: value })} />
        <NumberField label="超时秒数" value={form.timeoutSeconds} onChange={(value) => patch({ timeoutSeconds: value })} />
        <label>
          币种
          <select value={form.currency} onChange={(event) => patch({ currency: event.target.value as "CNY" | "USD" })}>
            <option value="CNY">CNY</option>
            <option value="USD">USD</option>
          </select>
        </label>
        <NumberField label="输入价格" value={form.priceInput} step={0.1} onChange={(value) => patch({ priceInput: value })} />
        <NumberField label="输出价格" value={form.priceOutput} step={0.1} onChange={(value) => patch({ priceOutput: value })} />
        <NumberField label="缓存命中" value={form.priceCacheHit} step={0.1} onChange={(value) => patch({ priceCacheHit: value })} />
        <NumberField label="缓存创建" value={form.priceCacheCreation} step={0.1} onChange={(value) => patch({ priceCacheCreation: value })} />
      </div>
      <label>
        备注
        <textarea value={form.notes} rows={3} onChange={(event) => patch({ notes: event.target.value })} />
      </label>
      <label className="inline-check">
        <input type="checkbox" checked={form.enabled} onChange={(event) => patch({ enabled: event.target.checked })} />
        启用模型
      </label>
      <div className="form-actions">
        <button type="button" disabled={testingDraft} onClick={onTest}>{testingDraft ? "测试中" : "测试连接"}</button>
        <button type="submit" disabled={saving}>{saving ? "保存中" : "保存"}</button>
      </div>
    </form>
  );
}

function TextField({ label, type = "text", value, onChange }: { label: string; type?: string; value: string; onChange: (value: string) => void }) {
  return <label>{label}<input type={type} value={value} onChange={(event) => onChange(event.target.value)} /></label>;
}

function NumberField({ label, value, step = 1, onChange }: { label: string; value: number; step?: number; onChange: (value: number) => void }) {
  return <label>{label}<input type="number" min={0} step={step} value={value} onChange={(event) => onChange(Number(event.target.value))} /></label>;
}

function buildPayload(form: Required<ModelConfigPayload>, includeEmptyApiKey: boolean): ModelConfigPayload {
  const payload: ModelConfigPayload = { ...form, apiKey: undefined };
  if (includeEmptyApiKey || form.apiKey?.trim()) {
    payload.apiKey = form.apiKey?.trim() || "";
  }
  return payload;
}

function buildTestPayload(form: Required<ModelConfigPayload>, modelConfigId?: number): ModelConfigPayload & { modelConfigId?: number } {
  return { ...buildPayload(form, false), modelConfigId };
}

function getErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof ApiError || error instanceof Error) {
    return error.message || fallback;
  }
  return fallback;
}
