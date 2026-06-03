<template>
  <article class="response-card" :class="{ pending: response.pending }">
    <div class="response-head">
      <div>
        <p class="panel-label">模型名称</p>
        <h3>{{ response.modelName }}</h3>
      </div>
      <strong v-if="response.pending" class="pending-score">...</strong>
      <strong v-else :class="{ failed: response.status !== 'success' }">
        {{ response.status === "success" ? score.final : "失败" }}
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
      <ScoreBar label="相关性" :value="score.relevance" />
      <ScoreBar label="完整性" :value="score.completeness" />
      <ScoreBar label="清晰度" :value="score.clarity" />
      <ScoreBar label="格式" :value="score.format" />
    </div>

    <footer v-if="showActions && !response.pending" class="card-actions">
      <el-button>采纳</el-button>
      <el-button>点赞</el-button>
      <el-button>详情</el-button>
    </footer>
  </article>
</template>

<script setup>
import { computed } from "vue";

import MarkdownRenderer from "./MarkdownRenderer.vue";
import ScoreBar from "./ScoreBar.vue";

const props = defineProps({
  response: {
    type: Object,
    required: true
  },
  elapsedSeconds: {
    type: Number,
    default: 0
  },
  showActions: {
    type: Boolean,
    default: false
  }
});

const score = computed(() => {
  return props.response.score || {
    relevance: 0,
    completeness: 0,
    clarity: 0,
    format: 0,
    final: 0
  };
});
</script>
