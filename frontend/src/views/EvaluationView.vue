<template>
  <section class="main-stage">
    <header class="topbar">
      <div>
        <p class="eyebrow">Evaluation Task</p>
        <h2>回答质量对比</h2>
      </div>
    </header>

    <section v-if="showModelNotice" class="api-key-notice">
      <div>
        <p class="panel-label">可用模型</p>
        <h3>当前没有可用于评测的模型</h3>
        <p>{{ authStore.isAdmin ? "请进入模型配置启用模型并填写 API Key。" : "请联系管理员配置可用模型。" }}</p>
      </div>
      <el-button v-if="authStore.isAdmin" type="primary" @click="router.push('/models')">去配置</el-button>
    </section>

    <section class="query-panel">
      <div class="query-header">
        <div>
          <p class="panel-label">用户问题</p>
          <h3>创建一次多模型评测</h3>
        </div>
        <div class="query-switches">
          <el-radio-group v-model="visibility" :disabled="store.loading" size="small">
            <el-radio-button value="public">公开评测</el-radio-button>
            <el-radio-button value="private">私有评测</el-radio-button>
          </el-radio-group>
          <el-switch v-model="enableThinking" :disabled="store.loading" active-text="思考模式" />
          <el-switch v-model="enableJudge" :disabled="store.loading" active-text="LLM 评审" />
        </div>
      </div>

      <el-input
        v-model="prompt"
        type="textarea"
        :rows="5"
        :disabled="store.loading"
        resize="none"
      />

      <div class="model-row">
        <el-checkbox-group v-model="selectedModels" :disabled="store.loading">
          <el-checkbox-button
            v-for="modelConfig in configuredModelConfigs"
            :key="modelConfig.id"
            :value="modelConfig.id"
          >
            {{ modelConfig.displayName }}
          </el-checkbox-button>
        </el-checkbox-group>
        <el-button type="primary" :loading="store.loading" :disabled="!canSubmit" @click="submitTask">
          {{ store.loading ? "等待模型响应" : "开始评测" }}
        </el-button>
      </div>

      <div v-if="enableJudge" class="judge-row">
        <span class="panel-label">评审模型</span>
        <el-select
          v-model="judgeModelId"
          :disabled="store.loading"
          placeholder="选择一个模型作为 LLM Judge"
        >
          <el-option
            v-for="modelConfig in configuredModelConfigs"
            :key="modelConfig.id"
            :label="modelConfig.displayName"
            :value="modelConfig.id"
          />
        </el-select>
      </div>
    </section>

    <el-alert
      v-if="modelConfigErrorMessage"
      :title="modelConfigErrorMessage"
      type="warning"
      show-icon
    />

    <section v-if="store.loading" class="waiting-banner" aria-live="polite">
      <div>
        <p class="panel-label">模型调用中</p>
        <strong>已完成 {{ responses.length }} / {{ pendingModelIds.length }}，已等待 {{ elapsedSeconds }}s</strong>
      </div>
      <span class="waiting-pulse" aria-hidden="true"></span>
    </section>

    <el-alert v-if="store.errorMessage" :title="store.errorMessage" type="error" show-icon />

    <ModelResponseSummaryGrid
      :responses="displayResponses"
      :elapsed-seconds="elapsedSeconds"
      :feedback-submitting-ids="store.feedbackSubmittingIds"
      layout-mode="grid"
      show-actions
      @feedback="handleFeedback"
    />
  </section>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { ElMessage } from "element-plus";
import { useRouter } from "vue-router";

import ModelResponseCard from "../components/ModelResponseCard.vue";
import ModelResponseSummaryGrid from "../components/ModelResponseSummaryGrid.vue";
import { useAuthStore } from "../stores/auth";
import { useEvaluationStore } from "../stores/evaluation";
import { listAvailableModels } from "../utils/api";

const router = useRouter();
const authStore = useAuthStore();
const store = useEvaluationStore();
const prompt = ref("");
const selectedModels = ref([]);
const judgeModelId = ref(null);
const enableJudge = ref(false);
const enableThinking = ref(false);
const visibility = ref("public");
const elapsedSeconds = ref(0);
const pendingModelIds = ref([]);
const modelConfigs = ref([]);
const modelConfigLoading = ref(false);
const modelConfigErrorMessage = ref("");
let waitingTimerId = null;

const responses = computed(() => store.task?.responses || []);
const configuredModelConfigs = computed(() => modelConfigs.value);
const showModelNotice = computed(() => !modelConfigLoading.value && configuredModelConfigs.value.length === 0);
const modelNameMap = computed(() => {
  return modelConfigs.value.reduce((names, modelConfig) => {
    names[modelConfig.id] = modelConfig.displayName;
    return names;
  }, {});
});
const responseMap = computed(() => {
  return responses.value.reduce((items, response) => {
    items[response.modelConfigId] = response;
    return items;
  }, {});
});
const canSubmit = computed(() => {
  return (
    !store.loading &&
    Boolean(prompt.value.trim()) &&
    selectedModels.value.length > 0 &&
    (!enableJudge.value || Boolean(judgeModelId.value))
  );
});
const displayResponses = computed(() => {
  if (store.loading) {
    return pendingModelIds.value.map((modelId) => {
      return responseMap.value[modelId] || {
        id: `pending-${modelId}`,
        modelName: modelNameMap.value[modelId] || `模型 ${modelId}`,
        pending: true
      };
    });
  }
  if (pendingModelIds.value.length > 0) {
    const orderedResponses = pendingModelIds.value
      .map((modelId) => responseMap.value[modelId])
      .filter(Boolean);
    if (orderedResponses.length > 0) {
      return orderedResponses;
    }
  }
  return responses.value;
});
function startWaitingTimer() {
  stopWaitingTimer();
  elapsedSeconds.value = 0;
  waitingTimerId = window.setInterval(() => {
    elapsedSeconds.value += 1;
  }, 1000);
}

function stopWaitingTimer() {
  if (waitingTimerId) {
    window.clearInterval(waitingTimerId);
    waitingTimerId = null;
  }
}

function selectDefaultModels() {
  const selectedSet = new Set(selectedModels.value);
  const availableIds = configuredModelConfigs.value.map((modelConfig) => modelConfig.id);
  selectedModels.value = availableIds.filter((modelId) => selectedSet.has(modelId));
  if (!availableIds.includes(judgeModelId.value)) {
    judgeModelId.value = availableIds[0] || null;
  }

  if (selectedModels.value.length > 0) {
    return;
  }

  const defaultModelIds = configuredModelConfigs.value
    .filter((modelConfig) => ["deepseek", "minimax"].includes(modelConfig.providerName))
    .map((modelConfig) => modelConfig.id);
  selectedModels.value = (defaultModelIds.length > 0 ? defaultModelIds : availableIds).slice(0, 2);
}

async function loadModelConfigs() {
  modelConfigLoading.value = true;
  modelConfigErrorMessage.value = "";

  try {
    modelConfigs.value = await listAvailableModels();
    selectDefaultModels();
  } catch (error) {
    modelConfigErrorMessage.value = error?.message || "模型配置加载失败";
  } finally {
    modelConfigLoading.value = false;
  }
}

async function submitTask() {
  if (!canSubmit.value) {
    return;
  }

  pendingModelIds.value = [...selectedModels.value];
  startWaitingTimer();
  await store.submitEvaluation({
    prompt: prompt.value,
    modelIds: selectedModels.value,
    enableJudge: enableJudge.value,
    judgeModelId: enableJudge.value ? judgeModelId.value : null,
    enableThinking: enableThinking.value,
    visibility: visibility.value
  });
  stopWaitingTimer();
}

async function handleFeedback({ responseId, feedbackType }) {
  try {
    const result = await store.submitFeedback(responseId, feedbackType);
    if (result?.active) {
      ElMessage.success(feedbackType === "like" ? "已点赞" : "已点踩");
    } else {
      ElMessage.success("已取消反馈");
    }
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || error?.message || "用户反馈提交失败");
  }
}

watch(enableJudge, (enabled) => {
  if (enabled && !judgeModelId.value) {
    judgeModelId.value = configuredModelConfigs.value[0]?.id || null;
  }
});

onMounted(loadModelConfigs);
onBeforeUnmount(stopWaitingTimer);
</script>
