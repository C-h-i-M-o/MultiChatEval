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
        :type="feedback.liked ? 'primary' : 'default'"
        :loading="feedbackSubmitting"
        @click="emitFeedback('like')"
      >
        点赞 {{ feedback.likeCount }}
      </el-button>
      <el-button
        :type="feedback.disliked ? 'danger' : 'default'"
        :loading="feedbackSubmitting"
        @click="emitFeedback('dislike')"
      >
        点踩 {{ feedback.dislikeCount }}
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
              <dt>规则分</dt>
              <dd>{{ score.ruleFinal ?? score.final }}</dd>
            </div>
            <div>
              <dt>LLM 评审</dt>
              <dd>{{ judgeScoreText }}</dd>
            </div>
            <div>
              <dt>耗时</dt>
              <dd>{{ response.latencyMs || 0 }}ms</dd>
            </div>
            <div>
              <dt>输出</dt>
              <dd>{{ response.outputTokens || 0 }}</dd>
            </div>
          </dl>
        </div>

        <article v-if="score.judgeComment" class="score-detail-item judge-detail-item">
          <header>
            <span>LLM 评审理由</span>
            <strong>{{ judgeScoreText }}</strong>
            <em>权重 40%</em>
          </header>
          <p>{{ score.judgeComment }}</p>
          <ul v-if="judgeDetailItems.length">
            <li v-for="detail in judgeDetailItems" :key="detail">{{ detail }}</li>
          </ul>
        </article>

        <article class="score-detail-item feedback-detail-item">
          <header>
            <span>用户反馈</span>
            <strong>{{ feedbackSummaryText }}</strong>
            <em>不计入当前评分</em>
          </header>
          <p>
            点赞 {{ feedback.likeCount }} 次，点踩 {{ feedback.dislikeCount }} 次；当前匿名用户反馈为{{ currentFeedbackText }}。
          </p>
        </article>

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
  },
  feedbackSubmitting: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(["feedback"]);

const score = computed(() => {
  return props.response.score || {
    relevance: 0,
    completeness: 0,
    clarity: 0,
    format: 0,
    safety: 0,
    final: 0,
    ruleFinal: 0,
    judgeFinal: null,
    judgeComment: null,
    judgeDetails: {}
  };
});

const detailVisible = ref(false);

const feedback = computed(() => {
  return props.response.feedback || {
    liked: false,
    disliked: false,
    likeCount: 0,
    dislikeCount: 0
  };
});

const feedbackSummaryText = computed(() => {
  if (feedback.value.liked) {
    return "已点赞";
  }
  if (feedback.value.disliked) {
    return "已点踩";
  }
  return "未反馈";
});

const currentFeedbackText = computed(() => {
  if (feedback.value.liked) {
    return "点赞";
  }
  if (feedback.value.disliked) {
    return "点踩";
  }
  return "未选择";
});

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

const judgeScoreText = computed(() => {
  return score.value.judgeFinal === null || score.value.judgeFinal === undefined
    ? "未启用"
    : `${score.value.judgeFinal} / 10`;
});

const judgeDetailItems = computed(() => {
  const details = score.value.judgeDetails || {};
  return Object.entries(details).flatMap(([label, items]) => {
    if (!Array.isArray(items)) {
      return [];
    }
    return items.map((item) => `${judgeDetailLabel(label)}：${item}`);
  });
});

function makeScoreDimension(key, label, value, weight, details) {
  return {
    key,
    label,
    value: value || 0,
    weight,
    details: details[key]?.length ? details[key] : ["暂无命中项明细"]
  };
}

function judgeDetailLabel(key) {
  const labels = {
    strengths: "优点",
    weaknesses: "缺点",
    recommendation: "建议",
    dimensionScores: "维度分"
  };
  return labels[key] || key;
}

function emitFeedback(feedbackType) {
  emit("feedback", {
    responseId: props.response.id,
    feedbackType
  });
}
</script>
