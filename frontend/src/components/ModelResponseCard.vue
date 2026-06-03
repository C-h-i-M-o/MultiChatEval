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
      <ScoreBar label="安全性" :value="score.safety" />
    </div>

    <footer v-if="showActions && !response.pending" class="card-actions">
      <el-button
        :type="feedback.accepted ? 'primary' : 'default'"
        :loading="activeFeedbackType === 'accepted'"
        :disabled="response.status !== 'success'"
        @click="toggleFeedback('accepted')"
      >
        {{ feedback.accepted ? "已采纳" : "采纳" }}
      </el-button>
      <el-button
        :type="feedback.liked ? 'primary' : 'default'"
        :loading="activeFeedbackType === 'like'"
        @click="toggleFeedback('like')"
      >
        {{ feedback.liked ? "已点赞" : "点赞" }}
      </el-button>
      <el-button @click="detailVisible = true">详情</el-button>
    </footer>

    <el-dialog v-model="detailVisible" title="评分详情" width="680px" class="score-detail-dialog">
      <section class="score-detail">
        <div class="score-summary">
          <div>
            <p class="panel-label">综合分</p>
            <strong>{{ score.final }}</strong>
          </div>
          <dl>
            <div>
              <dt>耗时</dt>
              <dd>{{ response.latencyMs || 0 }}ms</dd>
            </div>
            <div>
              <dt>输出</dt>
              <dd>{{ response.outputTokens || 0 }}</dd>
            </div>
            <div>
              <dt>反馈</dt>
              <dd>{{ feedbackText }}</dd>
            </div>
          </dl>
        </div>

        <div class="score-detail-list">
          <article v-for="dimension in scoreDimensions" :key="dimension.key" class="score-detail-item">
            <header>
              <span>{{ dimension.label }}</span>
              <strong>{{ dimension.value }} / 10</strong>
              <em>权重 {{ dimension.weight }}</em>
            </header>
            <ul>
              <li v-for="detail in dimension.details" :key="detail">{{ detail }}</li>
            </ul>
          </article>
        </div>
      </section>
    </el-dialog>
  </article>
</template>

<script setup>
import { computed, ref } from "vue";
import { ElMessage } from "element-plus";

import MarkdownRenderer from "./MarkdownRenderer.vue";
import ScoreBar from "./ScoreBar.vue";
import { useEvaluationStore } from "../stores/evaluation";

const store = useEvaluationStore();

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
    safety: 0,
    final: 0
  };
});

const feedback = computed(() => {
  return props.response.feedback || {
    liked: false,
    accepted: false,
    likeCount: 0,
    acceptedCount: 0
  };
});

const detailVisible = ref(false);
const activeFeedbackType = ref("");

const scoreDimensions = computed(() => {
  const details = score.value.details || {};
  return [
    makeScoreDimension("relevance", "相关性", score.value.relevance, "30%", details),
    makeScoreDimension("completeness", "完整性", score.value.completeness, "25%", details),
    makeScoreDimension("clarity", "清晰度", score.value.clarity, "20%", details),
    makeScoreDimension("format", "格式", score.value.format, "15%", details),
    makeScoreDimension("safety", "安全性", score.value.safety, "10%", details)
  ];
});

const feedbackText = computed(() => {
  const labels = [];
  if (feedback.value.accepted) {
    labels.push("已采纳");
  }
  if (feedback.value.liked) {
    labels.push("已点赞");
  }
  return labels.length > 0 ? labels.join("、") : "暂无";
});

async function toggleFeedback(feedbackType) {
  activeFeedbackType.value = feedbackType;
  try {
    await store.toggleResponseFeedback(props.response.id, feedbackType);
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || error?.message || "反馈提交失败");
  } finally {
    activeFeedbackType.value = "";
  }
}

function makeScoreDimension(key, label, value, weight, details) {
  return {
    key,
    label,
    value: value || 0,
    weight,
    details: details[key]?.length ? details[key] : ["暂无命中项明细"]
  };
}
</script>
