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
        <el-table-column label="类型" width="92">
          <template #default="{ row }">
            <el-tag :type="row.builtin ? 'success' : 'info'" effect="plain">
              {{ row.builtin ? "内置" : "自定义" }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="providerName" label="供应商" min-width="130" />
        <el-table-column prop="displayName" label="展示名" min-width="160" />
        <el-table-column prop="modelName" label="模型名" min-width="170" />
        <el-table-column prop="baseUrl" label="Base URL" min-width="220" show-overflow-tooltip />
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
            <el-button v-if="!row.builtin" size="small" type="danger" @click="confirmDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <el-dialog v-model="dialogVisible" :title="editingConfig ? '编辑模型配置' : '新增模型配置'" width="620px">
      <el-form label-position="top" class="config-form">
        <el-form-item label="供应商名称">
          <el-input v-model="form.providerName" :disabled="Boolean(editingConfig?.builtin)" />
        </el-form-item>
        <el-form-item label="展示名">
          <el-input v-model="form.displayName" />
        </el-form-item>
        <el-form-item label="模型名">
          <el-input v-model="form.modelName" />
        </el-form-item>
        <el-form-item label="Base URL">
          <el-input v-model="form.baseUrl" />
        </el-form-item>
        <el-form-item label="API Key">
          <el-input v-model="form.apiKey" type="password" show-password :placeholder="apiKeyPlaceholder" />
        </el-form-item>
        <div class="form-grid">
          <el-form-item label="Max Tokens">
            <el-input-number v-model="form.maxTokens" :min="1" :step="128" controls-position="right" />
          </el-form-item>
          <el-form-item label="输入单价">
            <el-input-number v-model="form.priceInput" :min="0" :step="0.000001" controls-position="right" />
          </el-form-item>
          <el-form-item label="输出单价">
            <el-input-number v-model="form.priceOutput" :min="0" :step="0.000001" controls-position="right" />
          </el-form-item>
        </div>
        <el-form-item label="启用状态">
          <el-switch v-model="form.enabled" />
        </el-form-item>
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

const form = reactive({
  providerName: "",
  displayName: "",
  modelName: "",
  baseUrl: "",
  apiKey: "",
  enabled: true,
  maxTokens: 1024,
  priceInput: 0,
  priceOutput: 0
});

const apiKeyPlaceholder = computed(() => {
  if (!editingConfig.value) {
    return "";
  }
  return editingConfig.value.hasApiKey ? "留空保留现有密钥" : "请输入自己的 API Key";
});

function resetForm() {
  form.providerName = "";
  form.displayName = "";
  form.modelName = "";
  form.baseUrl = "";
  form.apiKey = "";
  form.enabled = true;
  form.maxTokens = 1024;
  form.priceInput = 0;
  form.priceOutput = 0;
}

function openCreateDialog() {
  editingConfig.value = null;
  resetForm();
  dialogVisible.value = true;
}

function openEditDialog(config) {
  editingConfig.value = config;
  form.providerName = config.providerName;
  form.displayName = config.displayName;
  form.modelName = config.modelName;
  form.baseUrl = config.baseUrl;
  form.apiKey = "";
  form.enabled = config.enabled;
  form.maxTokens = config.maxTokens;
  form.priceInput = config.priceInput;
  form.priceOutput = config.priceOutput;
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
    priceInput: form.priceInput,
    priceOutput: form.priceOutput
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
    if (result.success) {
      ElMessage.success(`${result.message}，耗时 ${result.latencyMs}ms`);
    } else {
      ElMessage.error(result.message);
    }
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
    if (result.success) {
      ElMessage.success(`${result.message}，耗时 ${result.latencyMs}ms`);
    } else {
      ElMessage.error(result.message);
    }
  } catch (error) {
    ElMessage.error(error?.message || "连接测试失败");
  } finally {
    testingDraft.value = false;
  }
}

async function confirmDelete(config) {
  try {
    await ElMessageBox.confirm(`确认删除 ${config.displayName}？`, "删除模型配置", {
      confirmButtonText: "删除",
      cancelButtonText: "取消",
      type: "warning"
    });
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
