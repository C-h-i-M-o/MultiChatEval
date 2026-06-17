<template>
  <section class="config-stage">
    <header class="topbar config-topbar">
      <div>
        <p class="eyebrow">Model Providers</p>
        <h2>模型配置</h2>
      </div>
      <div class="config-actions">
        <el-button :loading="loading" @click="$emit('refresh')">刷新</el-button>
        <el-button type="primary" @click="openCreateDialog">新增配置</el-button>
      </div>
    </header>

    <section class="config-panel">
      <el-table v-loading="loading" :data="configs" row-key="id">
        <el-table-column prop="providerName" label="供应商" min-width="130" />
        <el-table-column prop="displayName" label="展示名" min-width="160" />
        <el-table-column prop="modelName" label="模型名" min-width="170" />
        <el-table-column prop="baseUrl" label="Base URL" min-width="220" show-overflow-tooltip />
        <el-table-column label="币种" width="84">
          <template #default="{ row }">{{ row.currency }}</template>
        </el-table-column>
        <el-table-column label="密钥" width="130">
          <template #default="{ row }">
            <span class="key-state">{{ row.hasApiKey ? row.maskedApiKey : "未配置" }}</span>
          </template>
        </el-table-column>
        <el-table-column label="启用" width="92">
          <template #default="{ row }">
            <el-switch :model-value="row.enabled" @change="toggleEnabled(row, $event)" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="openEditDialog(row)">编辑</el-button>
            <el-button size="small" :loading="testingId === row.id" @click="testSavedConfig(row)">测试</el-button>
            <el-button size="small" type="danger" @click="confirmDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <el-dialog
      v-model="dialogVisible"
      :title="editingConfig ? '编辑模型配置' : '新增模型配置'"
      width="min(760px, 94vw)"
    >
      <el-form label-position="top" class="config-form">
        <section v-if="!editingConfig" class="provider-picker">
          <div class="field-heading">
            <div>
              <span>选择供应商</span>
              <small>选择后会自动填写官方 OpenAI-compatible Base URL。</small>
            </div>
          </div>
          <div class="provider-preset-grid">
            <button
              v-for="preset in visibleProviderPresets"
              :key="preset.key"
              type="button"
              class="provider-preset"
              :class="{ active: selectedPresetKey === preset.key }"
              @click="selectPreset(preset)"
            >
              <strong>{{ preset.label }}</strong>
              <span>{{ preset.description }}</span>
            </button>
          </div>
          <el-collapse-transition>
            <div v-if="showMoreProviders" class="provider-preset-grid provider-preset-grid-more">
              <button
                v-for="preset in collapsedProviderPresets"
                :key="preset.key"
                type="button"
                class="provider-preset"
                :class="{ active: selectedPresetKey === preset.key }"
                @click="selectPreset(preset)"
              >
                <strong>{{ preset.label }}</strong>
                <span>{{ preset.description }}</span>
              </button>
            </div>
          </el-collapse-transition>
          <el-button text class="more-provider-button" @click="showMoreProviders = !showMoreProviders">
            {{ showMoreProviders ? "收起供应商" : "更多供应商" }}
          </el-button>
        </section>

        <section v-if="selectedPreset" class="provider-guide">
          <div>
            <strong>{{ selectedPreset.label }} 配置提示</strong>
            <p>{{ selectedPreset.description }}</p>
            <p>请在官方控制台创建 API Key，并从官方模型列表复制准确的模型名称。</p>
          </div>
          <div class="provider-guide-links">
            <el-link
              v-if="selectedPreset.consoleUrl"
              :href="selectedPreset.consoleUrl"
              target="_blank"
              type="primary"
            >
              官方控制台
            </el-link>
            <el-link
              v-if="selectedPreset.docsUrl"
              :href="selectedPreset.docsUrl"
              target="_blank"
              type="primary"
            >
              官方文档
            </el-link>
          </div>
        </section>

        <div class="form-grid form-grid-two">
          <el-form-item label="供应商名称">
            <el-input v-model="form.providerName" placeholder="例如 deepseek" />
          </el-form-item>
          <el-form-item label="展示名">
            <el-input v-model="form.displayName" placeholder="评测页显示的名称" />
          </el-form-item>
        </div>
        <el-form-item label="模型名">
          <el-input v-model="form.modelName" placeholder="复制官方文档中的 Model ID" />
          <p class="field-help">模型名必须与供应商控制台或官方模型列表完全一致。</p>
        </el-form-item>
        <el-form-item label="API Key">
          <el-input v-model="form.apiKey" type="password" show-password :placeholder="apiKeyPlaceholder" />
          <p class="field-help">密钥只用于后端调用，列表和接口不会返回原文。</p>
        </el-form-item>
        <el-form-item label="启用状态">
          <el-switch v-model="form.enabled" />
        </el-form-item>

        <el-collapse v-model="advancedSections" class="advanced-options">
          <el-collapse-item title="高级选项" name="advanced">
            <el-form-item label="Base URL">
              <el-input v-model="form.baseUrl" placeholder="例如 https://api.example.com/v1" />
              <p class="field-help">
                API 服务入口。预设会自动填写；空白模板请在供应商“OpenAI 兼容”文档中查找 Base URL。
              </p>
            </el-form-item>
            <div class="form-grid form-grid-two">
              <el-form-item label="温度">
                <el-input-number
                  v-model="form.temperature"
                  :min="0"
                  :max="2"
                  :step="0.1"
                  controls-position="right"
                />
                <p class="field-help">越低越稳定，越高越发散；不确定时保留 0.7。</p>
              </el-form-item>
              <el-form-item label="最大输出 Token">
                <el-input-number v-model="form.maxTokens" :min="1" :step="128" controls-position="right" />
                <p class="field-help">限制单次回答长度，不是每日用户额度。</p>
              </el-form-item>
              <el-form-item label="请求超时（秒）">
                <el-input-number
                  v-model="form.timeoutSeconds"
                  :min="1"
                  :max="600"
                  :step="5"
                  controls-position="right"
                />
                <p class="field-help">超过该时间后，仅当前模型标记为失败。</p>
              </el-form-item>
              <el-form-item label="计费币种">
                <el-select v-model="form.currency">
                  <el-option label="人民币 CNY" value="CNY" />
                  <el-option label="美元 USD" value="USD" />
                </el-select>
                <p class="field-help">系统不换汇，请按官方价格原币种填写。</p>
              </el-form-item>
            </div>

            <div class="price-guide">
              <strong>价格单位：每 100 万 Token</strong>
              <p>在供应商官方定价页查找对应模型和地区。没有单独价格的类别可填写 0。</p>
              <el-link
                v-if="selectedPreset?.docsUrl"
                :href="selectedPreset.docsUrl"
                target="_blank"
                type="primary"
              >
                打开当前供应商官方定价文档
              </el-link>
            </div>
            <div class="form-grid form-grid-two">
              <el-form-item label="输入价格">
                <el-input-number v-model="form.priceInput" :min="0" :step="0.1" controls-position="right" />
                <p class="field-help">未被缓存覆盖的请求输入 Token 单价。</p>
              </el-form-item>
              <el-form-item label="输出价格">
                <el-input-number v-model="form.priceOutput" :min="0" :step="0.1" controls-position="right" />
                <p class="field-help">模型生成回答内容的 Token 单价。</p>
              </el-form-item>
              <el-form-item label="缓存命中价格">
                <el-input-number v-model="form.priceCacheHit" :min="0" :step="0.1" controls-position="right" />
                <p class="field-help">供应商复用已有提示词缓存时的输入单价；未提供则填 0。</p>
              </el-form-item>
              <el-form-item label="缓存创建价格">
                <el-input-number
                  v-model="form.priceCacheCreation"
                  :min="0"
                  :step="0.1"
                  controls-position="right"
                />
                <p class="field-help">首次写入提示词缓存时的单价；未提供则填 0。</p>
              </el-form-item>
            </div>
            <el-form-item label="管理员备注">
              <el-input
                v-model="form.notes"
                type="textarea"
                :rows="3"
                maxlength="2000"
                show-word-limit
                placeholder="例如价格更新时间、模型用途或地区"
              />
              <p class="field-help">仅供管理员记录价格更新时间、地区或模型用途，不发送给模型。</p>
            </el-form-item>
          </el-collapse-item>
        </el-collapse>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button :loading="testingDraft" @click="testDraftConfig">测试连接</el-button>
        <el-button type="primary" :loading="saving" @click="saveConfig">保存</el-button>
      </template>
    </el-dialog>
  </section>
</template>

<script setup>
import { computed, reactive, ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";

import {
  collapsedProviderPresets,
  providerPresets,
  visibleProviderPresets
} from "../utils/providerPresets";
import { createModelConfig, deleteModelConfig, testModelConfig, updateModelConfig } from "../utils/api";

defineProps({
  configs: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(["refresh"]);
const dialogVisible = ref(false);
const editingConfig = ref(null);
const saving = ref(false);
const testingDraft = ref(false);
const testingId = ref(null);
const showMoreProviders = ref(false);
const selectedPresetKey = ref("deepseek");
const advancedSections = ref([]);

const form = reactive({
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
});

const selectedPreset = computed(() => {
  return providerPresets.find((preset) => preset.key === selectedPresetKey.value) || null;
});

const apiKeyPlaceholder = computed(() => {
  if (!editingConfig.value) {
    return "粘贴供应商控制台创建的 API Key";
  }
  return editingConfig.value.hasApiKey ? "留空保留现有密钥" : "请输入 API Key";
});

function resetForm() {
  Object.assign(form, {
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
  });
}

function selectPreset(preset) {
  selectedPresetKey.value = preset.key;
  form.providerName = preset.providerName;
  form.baseUrl = preset.baseUrl;
}

function openCreateDialog() {
  editingConfig.value = null;
  resetForm();
  showMoreProviders.value = false;
  advancedSections.value = [];
  selectPreset(visibleProviderPresets[0]);
  dialogVisible.value = true;
}

function openEditDialog(config) {
  editingConfig.value = config;
  selectedPresetKey.value =
    providerPresets.find((preset) => preset.providerName === config.providerName)?.key || "openai-compatible";
  Object.assign(form, {
    providerName: config.providerName,
    displayName: config.displayName,
    modelName: config.modelName,
    baseUrl: config.baseUrl,
    apiKey: "",
    enabled: config.enabled,
    maxTokens: config.maxTokens,
    temperature: config.temperature,
    timeoutSeconds: config.timeoutSeconds,
    notes: config.notes || "",
    currency: config.currency,
    priceInput: config.priceInput,
    priceOutput: config.priceOutput,
    priceCacheHit: config.priceCacheHit,
    priceCacheCreation: config.priceCacheCreation
  });
  advancedSections.value = [];
  dialogVisible.value = true;
}

function buildPayload(includeEmptyApiKey = false) {
  const payload = {
    providerName: form.providerName.trim(),
    displayName: form.displayName.trim(),
    modelName: form.modelName.trim(),
    baseUrl: form.baseUrl.trim(),
    enabled: form.enabled,
    maxTokens: form.maxTokens,
    temperature: form.temperature,
    timeoutSeconds: form.timeoutSeconds,
    notes: form.notes.trim(),
    currency: form.currency,
    priceInput: form.priceInput,
    priceOutput: form.priceOutput,
    priceCacheHit: form.priceCacheHit,
    priceCacheCreation: form.priceCacheCreation
  };
  if (includeEmptyApiKey || form.apiKey.trim()) {
    payload.apiKey = form.apiKey.trim();
  }
  return payload;
}

function validateForm() {
  if (!form.providerName.trim() || !form.displayName.trim() || !form.modelName.trim() || !form.baseUrl.trim()) {
    ElMessage.error("请填写供应商、展示名、模型名和 Base URL");
    return false;
  }
  return true;
}

async function saveConfig() {
  if (!validateForm()) {
    return;
  }
  saving.value = true;
  try {
    if (editingConfig.value) {
      await updateModelConfig(editingConfig.value.id, buildPayload(false));
    } else {
      await createModelConfig(buildPayload(true));
    }
    ElMessage.success("模型配置已保存");
    dialogVisible.value = false;
    emit("refresh");
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || error?.message || "模型配置保存失败");
  } finally {
    saving.value = false;
  }
}

async function toggleEnabled(config, enabled) {
  try {
    await updateModelConfig(config.id, { enabled });
    ElMessage.success(enabled ? "模型已启用" : "模型已禁用");
    emit("refresh");
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || error?.message || "启用状态更新失败");
    emit("refresh");
  }
}

async function testSavedConfig(config) {
  testingId.value = config.id;
  try {
    const result = await testModelConfig({ modelConfigId: config.id });
    result.success
      ? ElMessage.success(`${result.message}，耗时 ${result.latencyMs}ms`)
      : ElMessage.error(result.message);
  } catch (error) {
    ElMessage.error(error?.message || "连接测试失败");
  } finally {
    testingId.value = null;
  }
}

async function testDraftConfig() {
  if (!validateForm()) {
    return;
  }
  testingDraft.value = true;
  try {
    const payload = buildPayload(false);
    if (editingConfig.value) {
      payload.modelConfigId = editingConfig.value.id;
    }
    const result = await testModelConfig(payload);
    result.success
      ? ElMessage.success(`${result.message}，耗时 ${result.latencyMs}ms`)
      : ElMessage.error(result.message);
  } catch (error) {
    ElMessage.error(error?.message || "连接测试失败");
  } finally {
    testingDraft.value = false;
  }
}

async function confirmDelete(config) {
  try {
    await ElMessageBox.confirm(
      `确认删除 ${config.displayName}？历史回答会保留模型快照。`,
      "删除模型配置",
      {
        confirmButtonText: "删除",
        cancelButtonText: "取消",
        type: "warning"
      }
    );
    await deleteModelConfig(config.id);
    ElMessage.success("模型配置已删除");
    emit("refresh");
  } catch (error) {
    if (error !== "cancel" && error !== "close") {
      ElMessage.error(error?.response?.data?.detail || error?.message || "模型配置删除失败");
    }
  }
}
</script>
