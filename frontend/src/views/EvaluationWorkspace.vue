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
        <button class="nav-item active">对比评测</button>
        <button class="nav-item">模型配置</button>
        <button class="nav-item">历史任务</button>
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

    <section class="main-stage">
      <header class="topbar">
        <div>
          <p class="eyebrow">Evaluation Task</p>
          <h2>回答质量对比</h2>
        </div>
        <el-segmented v-model="mode" :options="modeOptions" :disabled="store.loading" />
      </header>

      <section class="query-panel">
        <div class="query-header">
          <div>
            <p class="panel-label">用户问题</p>
            <h3>创建一次多模型评测</h3>
          </div>
          <el-switch v-model="enableJudge" :disabled="store.loading" active-text="LLM 评审" />
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
            <el-checkbox-button :value="1">deepseek-v4-flash</el-checkbox-button>
            <el-checkbox-button :value="2">MiniMax-M2.5</el-checkbox-button>
            <el-checkbox-button :value="3">glm-4.7</el-checkbox-button>
          </el-checkbox-group>
          <el-button type="primary" :loading="store.loading" :disabled="!canSubmit" @click="submitTask">
            {{ store.loading ? "等待模型响应" : "开始评测" }}
          </el-button>
        </div>
      </section>

      <section v-if="store.loading" class="waiting-banner" aria-live="polite">
        <div>
          <p class="panel-label">模型调用中</p>
          <strong>正在调用 {{ pendingModelCards.length }} 个模型，已等待 {{ elapsedSeconds }}s</strong>
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
  </main>
</template>

<script setup>
import { computed, onBeforeUnmount, ref } from "vue";

import MarkdownRenderer from "../components/MarkdownRenderer.vue";
import ScoreBar from "../components/ScoreBar.vue";
import { useEvaluationStore } from "../stores/evaluation";

const store = useEvaluationStore();
const prompt = ref("");
const selectedModels = ref([1, 2]);
const enableJudge = ref(false);
const mode = ref("标准评测");
const modeOptions = ["快速评测", "标准评测", "深度评测"];
const elapsedSeconds = ref(0);
const pendingModelIds = ref([]);
let waitingTimerId = null;

const modelNameMap = {
  1: "deepseek-v4-flash",
  2: "MiniMax-M2.5",
  3: "glm-4.7"
};

const responses = computed(() => store.task?.responses || []);
const canSubmit = computed(() => {
  return !store.loading && Boolean(prompt.value.trim()) && selectedModels.value.length > 0;
});
const pendingModelCards = computed(() => {
  return pendingModelIds.value.map((modelId) => ({
    id: `pending-${modelId}`,
    modelName: modelNameMap[modelId] || `模型 ${modelId}`,
    pending: true
  }));
});
const displayResponses = computed(() => {
  if (store.loading) {
    return pendingModelCards.value;
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

async function submitTask() {
  if (!canSubmit.value) {
    return;
  }

  pendingModelIds.value = [...selectedModels.value];
  startWaitingTimer();
  await store.submitEvaluation({
    prompt: prompt.value,
    modelIds: selectedModels.value,
    enableJudge: enableJudge.value
  });
  stopWaitingTimer();
}

onBeforeUnmount(stopWaitingTimer);
</script>
