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
        <el-segmented v-model="mode" :options="modeOptions" />
      </header>

      <section class="query-panel">
        <div class="query-header">
          <div>
            <p class="panel-label">用户问题</p>
            <h3>创建一次多模型评测</h3>
          </div>
          <el-switch v-model="enableJudge" active-text="LLM 评审" />
        </div>

        <el-input
          v-model="prompt"
          type="textarea"
          :rows="5"
          resize="none"
          placeholder="例如：请解释什么是软件工程中的适配器模式，并给出一个简单例子。"
        />

        <div class="model-row">
          <el-checkbox-group v-model="selectedModels">
            <el-checkbox-button :value="1">deepseek-v4-flash</el-checkbox-button>
            <el-checkbox-button :value="2">MiniMax-M2.5</el-checkbox-button>
            <el-checkbox-button :value="3">glm-4.7</el-checkbox-button>
          </el-checkbox-group>
          <el-button type="primary" :loading="store.loading" @click="submitTask">开始评测</el-button>
        </div>
      </section>

      <el-alert v-if="store.errorMessage" :title="store.errorMessage" type="error" show-icon />

      <section class="result-grid" :class="resultGridClass">
        <article v-for="response in responses" :key="response.id" class="response-card">
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

          <p class="answer-text">{{ response.answer }}</p>

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

          <footer class="card-actions">
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
import { computed, ref } from "vue";

import ScoreBar from "../components/ScoreBar.vue";
import { useEvaluationStore } from "../stores/evaluation";

const store = useEvaluationStore();
const prompt = ref("请解释什么是软件工程中的适配器模式，并给出一个简单例子。");
const selectedModels = ref([1, 2]);
const enableJudge = ref(false);
const mode = ref("标准评测");
const modeOptions = ["快速评测", "标准评测", "深度评测"];

const responses = computed(() => store.task?.responses || []);
const resultGridClass = computed(() => {
  const count = responses.value.length;
  if (count === 1) {
    return "one-card";
  }
  if (count === 2) {
    return "two-cards";
  }
  return "three-cards";
});

async function submitTask() {
  await store.submitEvaluation({
    prompt: prompt.value,
    modelIds: selectedModels.value,
    enableJudge: enableJudge.value
  });
}
</script>
