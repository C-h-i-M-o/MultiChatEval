<template>
  <main class="workspace-shell">
    <aside class="sidebar">
      <div class="brand-block">
        <span class="brand-mark">M</span>
        <div>
          <p class="eyebrow">MultiChatEval</p>
          <h1>多模型评测工作台</h1>
        </div>
      </div>

      <nav class="nav-list" aria-label="主导航">
        <button class="nav-item" :class="{ active: activeView === 'evaluation' }" @click="activeView = 'evaluation'">
          对比评测
        </button>
        <button class="nav-item" :class="{ active: activeView === 'configs' }" @click="activeView = 'configs'">
          模型配置
        </button>
        <button class="nav-item" :class="{ active: activeView === 'history' }" @click="openHistory">
          历史任务
        </button>
        <button class="nav-item">反馈统计</button>
      </nav>

      <section class="panel compact">
        <p class="panel-label">默认流程</p>
        <ol class="step-list">
          <li>输入问题</li>
          <li>选择模型</li>
          <li>并发回答</li>
          <li>规则评分</li>
          <li>反馈归档</li>
        </ol>
      </section>
    </aside>

    <section v-if="activeView === 'evaluation'" class="main-stage">
      <header class="topbar">
        <div>
          <p class="eyebrow">Evaluation Task</p>
          <h2>回答质量对比</h2>
        </div>
      </header>

      <section v-if="showApiKeyNotice" class="api-key-notice">
        <div>
          <p class="panel-label">模型密钥</p>
          <h3>请先配置模型 API Key</h3>
          <p>系统内置模型不会读取 .env 中的密钥。请进入模型配置，为 DeepSeek、MiniMax、GLM 或自定义模型填写自己的 API Key。</p>
        </div>
        <el-button type="primary" @click="activeView = 'configs'">去配置</el-button>
      </section>

      <section class="query-panel">
        <div class="query-header">
          <div>
            <p class="panel-label">用户问题</p>
            <h3>创建一次多模型评测</h3>
          </div>
          <div class="query-switches">
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
      </section>

      <el-alert
        v-if="modelConfigErrorMessage"
        :title="modelConfigErrorMessage"
        type="warning"
        show-icon
      />

      <el-alert
        v-if="!modelConfigLoading && configuredModelConfigs.length === 0"
        title="暂无可评测模型，请先在模型配置中填写 API Key 并启用至少一个模型"
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

      <section class="result-grid" :class="resultGridClass">
        <article
          v-for="response in displayResponses"
          :key="response.id"
          class="response-card"
          :class="{ pending: response.pending }"
        >
          <div class="response-head">
            <div>
              <p class="panel-label">模型名称</p>
              <h3>{{ response.modelName }}</h3>
            </div>
            <strong v-if="response.pending" class="pending-score">...</strong>
            <strong v-else :class="{ failed: response.status !== 'success' }">
              {{ response.status === "success" ? response.score.final : "失败" }}
            </strong>
          </div>

          <el-tag v-if="response.pending" type="warning" effect="plain">
            等待模型响应
          </el-tag>
          <el-tag v-else :type="response.status === 'success' ? 'success' : 'danger'" effect="plain">
            {{ response.status === "success" ? "调用成功" : "调用失败" }}
          </el-tag>

          <div v-if="response.pending" class="pending-answer" aria-label="模型响应等待中">
            <span></span>
            <span></span>
            <span></span>
          </div>
          <MarkdownRenderer v-else :content="response.answer || ''" />

          <dl v-if="response.pending" class="metric-row pending-metrics">
            <div>
              <dt>耗时</dt>
              <dd>{{ elapsedSeconds }}s</dd>
            </div>
            <div>
              <dt>输出</dt>
              <dd>等待中</dd>
            </div>
            <div>
              <dt>成本</dt>
              <dd>待估算</dd>
            </div>
          </dl>
          <dl v-else class="metric-row">
            <div>
              <dt>耗时</dt>
              <dd>{{ response.latencyMs }}ms</dd>
            </div>
            <div>
              <dt>输出</dt>
              <dd>{{ response.outputTokens }}</dd>
            </div>
            <div>
              <dt>成本</dt>
              <dd>¥{{ response.estimatedCost }}</dd>
            </div>
          </dl>

          <div v-if="response.pending" class="pending-progress" aria-hidden="true">
            <i></i>
          </div>
          <div v-else class="score-bars">
            <ScoreBar label="相关性" :value="response.score.relevance" />
            <ScoreBar label="完整性" :value="response.score.completeness" />
            <ScoreBar label="清晰度" :value="response.score.clarity" />
            <ScoreBar label="格式" :value="response.score.format" />
          </div>

          <footer v-if="!response.pending" class="card-actions">
            <el-button>采纳</el-button>
            <el-button>点赞</el-button>
            <el-button>详情</el-button>
          </footer>
        </article>
      </section>
    </section>

    <section v-else-if="activeView === 'history'" class="main-stage history-stage">
      <header class="topbar">
        <div>
          <p class="eyebrow">History</p>
          <h2>历史任务</h2>
        </div>
        <el-button :loading="store.historyLoading" @click="refreshHistory">刷新</el-button>
      </header>

      <el-alert v-if="store.historyErrorMessage" :title="store.historyErrorMessage" type="error" show-icon />

      <section class="history-layout">
        <section class="history-panel">
          <div class="history-list-head">
            <div>
              <p class="panel-label">任务列表</p>
              <h3>最近评测</h3>
            </div>
            <span>{{ store.historyTotal }} 条</span>
          </div>

          <el-empty v-if="!store.historyLoading && store.historyItems.length === 0" description="暂无历史任务" />

          <div v-else class="history-list">
            <button
              v-for="taskItem in store.historyItems"
              :key="taskItem.taskId"
              class="history-item"
              :class="{ active: store.selectedHistoryTask?.taskId === taskItem.taskId }"
              @click="loadHistoryTask(taskItem.taskId)"
            >
              <span class="history-item-title">{{ taskItem.prompt }}</span>
              <span class="history-item-meta">
                {{ formatTime(taskItem.createdAt) }} · {{ taskItem.responseCount }} 个回答
              </span>
              <el-tag :type="historyStatusTagType(taskItem)" effect="plain">
                {{ historyStatusText(taskItem) }}
              </el-tag>
            </button>
          </div>

          <el-pagination
            class="history-pagination"
            background
            layout="sizes, prev, pager, next"
            :current-page="store.historyPage"
            :page-size="store.historyPageSize"
            :page-sizes="[10, 20, 50]"
            :total="store.historyTotal"
            @current-change="changeHistoryPage"
            @size-change="changeHistoryPageSize"
          />
        </section>

        <section class="history-detail">
          <el-empty
            v-if="!store.historyDetailLoading && !store.selectedHistoryTask"
            description="请选择一个历史任务"
          />

          <div v-else-if="store.selectedHistoryTask" class="history-detail-body">
            <div class="history-detail-head">
              <div>
                <p class="panel-label">任务详情</p>
                <h3>{{ store.selectedHistoryTask.prompt }}</h3>
              </div>
              <el-tag :type="statusTagType(store.selectedHistoryTask.status)" effect="plain">
                {{ statusText(store.selectedHistoryTask.status) }}
              </el-tag>
            </div>

            <div class="history-response-list">
              <article
                v-for="response in store.selectedHistoryTask.responses"
                :key="response.id"
                class="response-card"
              >
                <div class="response-head">
                  <div>
                    <p class="panel-label">模型名称</p>
                    <h3>{{ response.modelName }}</h3>
                  </div>
                  <strong :class="{ failed: response.status !== 'success' }">
                    {{ response.status === "success" ? response.score.final : "失败" }}
                  </strong>
                </div>

                <el-tag :type="response.status === 'success' ? 'success' : 'danger'" effect="plain">
                  {{ response.status === "success" ? "调用成功" : "调用失败" }}
                </el-tag>

                <MarkdownRenderer :content="response.answer || ''" />

                <dl class="metric-row">
                  <div>
                    <dt>耗时</dt>
                    <dd>{{ response.latencyMs }}ms</dd>
                  </div>
                  <div>
                    <dt>输出</dt>
                    <dd>{{ response.outputTokens }}</dd>
                  </div>
                  <div>
                    <dt>成本</dt>
                    <dd>¥{{ response.estimatedCost }}</dd>
                  </div>
                </dl>

                <div class="score-bars">
                  <ScoreBar label="相关性" :value="response.score.relevance" />
                  <ScoreBar label="完整性" :value="response.score.completeness" />
                  <ScoreBar label="清晰度" :value="response.score.clarity" />
                  <ScoreBar label="格式" :value="response.score.format" />
                </div>
              </article>
            </div>
          </div>
        </section>
      </section>
    </section>

    <ModelConfigPanel
      v-else
      class="main-stage"
      :configs="modelConfigs"
      :loading="modelConfigLoading"
      @refresh="loadModelConfigs"
    />
  </main>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue";

import MarkdownRenderer from "../components/MarkdownRenderer.vue";
import ModelConfigPanel from "../components/ModelConfigPanel.vue";
import ScoreBar from "../components/ScoreBar.vue";
import { useEvaluationStore } from "../stores/evaluation";
import { listModelConfigs } from "../utils/api";

const store = useEvaluationStore();
const activeView = ref("evaluation");
const prompt = ref("");
const selectedModels = ref([]);
const enableJudge = ref(false);
const enableThinking = ref(false);
const elapsedSeconds = ref(0);
const pendingModelIds = ref([]);
const modelConfigs = ref([]);
const modelConfigLoading = ref(false);
const modelConfigErrorMessage = ref("");
let waitingTimerId = null;

const responses = computed(() => store.task?.responses || []);
const configuredModelConfigs = computed(() => {
  return modelConfigs.value.filter((modelConfig) => modelConfig.enabled && modelConfig.hasApiKey);
});
const showApiKeyNotice = computed(() => {
  return !modelConfigLoading.value && modelConfigs.value.length > 0 && modelConfigs.value.every((modelConfig) => !modelConfig.hasApiKey);
});
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
  return !store.loading && Boolean(prompt.value.trim()) && selectedModels.value.length > 0;
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
const resultGridClass = computed(() => {
  const count = displayResponses.value.length;
  if (count === 1) {
    return "one-card";
  }
  if (count === 2) {
    return "two-cards";
  }
  return "three-cards";
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
    modelConfigs.value = await listModelConfigs();
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
    enableThinking: enableThinking.value
  });
  stopWaitingTimer();
}

async function openHistory() {
  activeView.value = "history";
  await store.loadHistory(1, store.historyPageSize);
}

async function refreshHistory() {
  await store.loadHistory(store.historyPage, store.historyPageSize);
}

async function changeHistoryPage(page) {
  await store.loadHistory(page, store.historyPageSize);
}

async function changeHistoryPageSize(pageSize) {
  await store.loadHistory(1, pageSize);
}

async function loadHistoryTask(taskId) {
  await store.loadHistoryTask(taskId);
}

const HISTORY_PENDING_TIMEOUT_MS = 120 * 1000;

function historyStatusText(taskItem) {
  if (isStalePendingTask(taskItem)) {
    return "超时未完成";
  }
  return statusText(taskItem.status);
}

function historyStatusTagType(taskItem) {
  if (isStalePendingTask(taskItem)) {
    return "danger";
  }
  return statusTagType(taskItem.status);
}

function statusText(status) {
  if (status === "completed") {
    return "已完成";
  }
  if (status === "failed") {
    return "失败";
  }
  return "进行中";
}

function statusTagType(status) {
  if (status === "completed") {
    return "success";
  }
  if (status === "running" || status === "pending") {
    return "warning";
  }
  return "danger";
}

function isStalePendingTask(taskItem) {
  if (taskItem.status !== "pending" || taskItem.completedAt) {
    return false;
  }
  const createdAt = parseBackendTime(taskItem.createdAt);
  if (Number.isNaN(createdAt.getTime())) {
    return false;
  }
  return Date.now() - createdAt.getTime() >= HISTORY_PENDING_TIMEOUT_MS;
}

function formatTime(value) {
  if (!value) {
    return "未知时间";
  }
  const date = parseBackendTime(value);
  return new Intl.DateTimeFormat("zh-CN", {
    timeZone: "Asia/Shanghai",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false
  }).format(date);
}

function parseBackendTime(value) {
  if (typeof value !== "string") {
    return new Date(value);
  }
  const hasTimezone = /(?:Z|[+-]\d{2}:?\d{2})$/.test(value);
  return new Date(hasTimezone ? value : `${value}Z`);
}

onMounted(loadModelConfigs);
onBeforeUnmount(stopWaitingTimer);
</script>
