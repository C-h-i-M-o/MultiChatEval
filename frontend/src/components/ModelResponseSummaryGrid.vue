<template>
  <section
    ref="gridRoot"
    class="response-summary-shell"
    :class="`response-summary-shell-${layoutMode}`"
  >
    <div v-if="layoutMode === 'grid'" class="response-summary-grid" :class="summaryGridClass">
      <article
        v-for="(response, index) in responses"
        :key="response.id"
        class="response-summary-card"
        :class="summaryCardClass(response, index)"
      >
        <header class="summary-card-head">
          <div>
            <p class="panel-label">模型名称</p>
            <h3>{{ response.modelName }}</h3>
          </div>
          <strong v-if="response.pending" class="summary-score pending-score">...</strong>
          <strong v-else class="summary-score" :class="{ failed: response.status !== 'success' }">
            {{ response.status === "success" ? normalizedScore(response).final : "失败" }}
          </strong>
        </header>

        <el-tag v-if="response.pending" type="warning" effect="plain">
          等待模型响应
        </el-tag>
        <el-tag v-else :type="response.status === 'success' ? 'success' : 'danger'" effect="plain">
          {{ response.status === "success" ? "调用成功" : "调用失败" }}
        </el-tag>

        <div v-if="response.pending" class="pending-answer summary-pending-answer" aria-label="模型响应等待中">
          <span></span>
          <span></span>
          <span></span>
        </div>
        <p v-else class="summary-answer-preview">
          {{ answerPreview(response.answer) }}
        </p>

        <dl class="metric-row summary-metrics">
          <div>
            <dt>耗时</dt>
            <dd>{{ response.pending ? `${elapsedSeconds}s` : `${response.latencyMs}ms` }}</dd>
          </div>
          <div>
            <dt>输出</dt>
            <dd>{{ response.pending ? "等待中" : response.outputTokens }}</dd>
          </div>
          <div>
            <dt>成本</dt>
            <dd>{{ response.pending ? "待估算" : `¥${response.estimatedCost}` }}</dd>
          </div>
        </dl>

        <div v-if="response.pending" class="pending-progress" aria-hidden="true">
          <i></i>
        </div>
        <div v-else class="summary-score-bars">
          <div
            v-for="dimension in summaryDimensions(response)"
            :key="dimension.key"
            class="summary-score-bar"
          >
            <span>{{ dimension.label }}</span>
            <i>
              <b class="summary-score-fill" :style="{ width: `${dimension.value * 10}%` }"></b>
            </i>
            <em>{{ dimension.value }}</em>
          </div>
        </div>

        <footer v-if="!response.pending" class="summary-card-actions">
          <div v-if="showActions" class="summary-feedback-actions">
            <el-button
              :type="normalizedFeedback(response).liked ? 'primary' : 'default'"
              :loading="feedbackSubmittingIds.includes(response.id)"
              @click="emitFeedback(response, 'like')"
            >
              点赞 {{ normalizedFeedback(response).likeCount }}
            </el-button>
            <el-button
              :type="normalizedFeedback(response).disliked ? 'danger' : 'default'"
              :loading="feedbackSubmittingIds.includes(response.id)"
              @click="emitFeedback(response, 'dislike')"
            >
              点踩 {{ normalizedFeedback(response).dislikeCount }}
            </el-button>
          </div>
          <el-button type="primary" plain @click="openDetail(response)">查看全文</el-button>
        </footer>
      </article>
    </div>

    <div v-else class="response-summary-list">
      <article
        v-for="response in responses"
        :key="response.id"
        class="response-summary-row"
        :class="{ pending: response.pending, failed: !response.pending && response.status !== 'success' }"
        @click="openDetailIfReady(response)"
      >
        <div class="summary-row-primary">
          <div class="summary-row-title">
            <div>
              <p class="panel-label">模型名称</p>
              <h3>{{ response.modelName }}</h3>
            </div>
            <el-tag v-if="response.pending" type="warning" effect="plain">
              等待模型响应
            </el-tag>
            <el-tag v-else :type="response.status === 'success' ? 'success' : 'danger'" effect="plain">
              {{ response.status === "success" ? "调用成功" : "调用失败" }}
            </el-tag>
          </div>

          <div v-if="response.pending" class="pending-answer summary-row-pending" aria-label="模型响应等待中">
            <span></span>
            <span></span>
          </div>
          <p v-else class="summary-row-preview">
            {{ answerPreview(response.answer) }}
          </p>
        </div>

        <dl class="summary-row-metrics">
          <div class="summary-row-score">
            <dt>综合分</dt>
            <dd :class="{ failed: !response.pending && response.status !== 'success' }">
              {{ response.pending ? "..." : response.status === "success" ? normalizedScore(response).final : "失败" }}
            </dd>
          </div>
          <div>
            <dt>耗时</dt>
            <dd>{{ response.pending ? `${elapsedSeconds}s` : `${response.latencyMs}ms` }}</dd>
          </div>
          <div>
            <dt>输出</dt>
            <dd>{{ response.pending ? "等待中" : response.outputTokens }}</dd>
          </div>
          <div>
            <dt>成本</dt>
            <dd>{{ response.pending ? "待估算" : `¥${response.estimatedCost}` }}</dd>
          </div>
        </dl>

        <footer v-if="!response.pending" class="summary-row-actions">
          <div v-if="showActions" class="summary-feedback-actions">
            <el-button
              :type="normalizedFeedback(response).liked ? 'primary' : 'default'"
              :loading="feedbackSubmittingIds.includes(response.id)"
              @click.stop="emitFeedback(response, 'like')"
            >
              点赞 {{ normalizedFeedback(response).likeCount }}
            </el-button>
            <el-button
              :type="normalizedFeedback(response).disliked ? 'danger' : 'default'"
              :loading="feedbackSubmittingIds.includes(response.id)"
              @click.stop="emitFeedback(response, 'dislike')"
            >
              点踩 {{ normalizedFeedback(response).dislikeCount }}
            </el-button>
          </div>
          <el-button type="primary" plain @click.stop="openDetail(response)">查看全文</el-button>
        </footer>
      </article>
    </div>

    <el-dialog
      v-model="detailVisible"
      :title="detailTitle"
      width="min(980px, 94vw)"
      class="response-detail-dialog"
      @opened="animateDialog"
    >
      <div ref="dialogRoot" class="response-detail-scroll">
        <ModelResponseCard
          v-if="selectedResponse"
          :key="selectedResponse.id"
          :response="selectedResponse"
          :elapsed-seconds="elapsedSeconds"
          :feedback-submitting="feedbackSubmittingIds.includes(selectedResponse.id)"
          :show-actions="showActions"
          embedded-detail
          @feedback="$emit('feedback', $event)"
        />
      </div>
    </el-dialog>
  </section>
</template>

<script setup>
import { gsap } from "gsap";
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from "vue";

import ModelResponseCard from "./ModelResponseCard.vue";

const props = defineProps({
  responses: {
    type: Array,
    default: () => []
  },
  elapsedSeconds: {
    type: Number,
    default: 0
  },
  feedbackSubmittingIds: {
    type: Array,
    default: () => []
  },
  showActions: {
    type: Boolean,
    default: false
  },
  layoutMode: {
    type: String,
    default: "grid",
    validator: (value) => ["grid", "list"].includes(value)
  }
});

const emit = defineEmits(["feedback"]);

const gridRoot = ref(null);
const dialogRoot = ref(null);
const detailVisible = ref(false);
const selectedResponse = ref(null);
let gridContext = null;

const summaryGridClass = computed(() => {
  return `summary-grid-count-${Math.min(Math.max(props.responses.length, 1), 9)}`;
});

const detailTitle = computed(() => {
  return selectedResponse.value ? `${selectedResponse.value.modelName} · 完整回答` : "完整回答";
});

const responseAnimationKey = computed(() => {
  const responsesKey = props.responses
    .map((response) => `${response.id}:${response.pending ? "pending" : response.status}`)
    .join("|");
  return `${props.layoutMode}:${responsesKey}`;
});

function normalizedScore(response) {
  return response.score || {
    relevance: 0,
    completeness: 0,
    clarity: 0,
    format: 0,
    safety: 0,
    final: 0
  };
}

function normalizedFeedback(response) {
  return response.feedback || {
    liked: false,
    disliked: false,
    likeCount: 0,
    dislikeCount: 0
  };
}

function summaryDimensions(response) {
  const score = normalizedScore(response);
  return [
    { key: "relevance", label: "相关", value: score.relevance || 0 },
    { key: "completeness", label: "完整", value: score.completeness || 0 },
    { key: "clarity", label: "清晰", value: score.clarity || 0 }
  ];
}

function answerPreview(answer) {
  const source = answer || "暂无回答内容";
  const withoutThink = source
    .replace(/<think>[\s\S]*?<\/think>/gi, "")
    .replace(/<think>[\s\S]*/gi, "");
  const plainText = withoutThink
    .replace(/```[\s\S]*?```/g, " 代码块 ")
    .replace(/[#>*_`|[\]()~-]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
  return plainText || "暂无回答内容";
}

function emitFeedback(response, feedbackType) {
  emit("feedback", {
    responseId: response.id,
    feedbackType
  });
}

function openDetail(response) {
  selectedResponse.value = response;
  detailVisible.value = true;
}

function openDetailIfReady(response) {
  if (!response.pending) {
    openDetail(response);
  }
}

function summaryCardClass(response, index) {
  return [
    {
      pending: response.pending,
      failed: !response.pending && response.status !== "success"
    },
    `summary-card-span-${summaryCardSpan(props.responses.length, index)}`
  ];
}

function summaryCardSpan(count, index) {
  if (count <= 1) {
    return 6;
  }
  if (count === 2 || count === 4) {
    return 3;
  }
  if (count === 3 || count === 6 || count === 9) {
    return 2;
  }
  if (count === 5) {
    return index < 3 ? 2 : 3;
  }
  if (count === 7) {
    return index < 3 ? 2 : 3;
  }
  if (count === 8) {
    return index < 6 ? 2 : 3;
  }
  return 2;
}

function animateCards() {
  nextTick(() => {
    if (!gridRoot.value) {
      return;
    }
    gridContext?.revert();
    gridContext = gsap.context(() => {
      const cards = Array.from(
        gridRoot.value.querySelectorAll(
          props.layoutMode === "list" ? ".response-summary-row" : ".response-summary-card"
        )
      );
      const fills = Array.from(gridRoot.value.querySelectorAll(".summary-score-fill"));
      const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      if (!cards.length) {
        return;
      }
      if (reduceMotion) {
        gsap.fromTo(cards, { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.18, stagger: 0.03 });
        return;
      }
      gsap.fromTo(
        cards,
        {
          autoAlpha: 0,
          y: props.layoutMode === "list" ? 10 : 18,
          scale: props.layoutMode === "list" ? 1 : 0.97
        },
        {
          autoAlpha: 1,
          y: 0,
          scale: 1,
          duration: props.layoutMode === "list" ? 0.3 : 0.42,
          ease: props.layoutMode === "list" ? "power2.out" : "back.out(1.35)",
          stagger: { each: props.layoutMode === "list" ? 0.04 : 0.055, from: "start" },
          clearProps: "transform,opacity,visibility"
        }
      );
      if (fills.length) {
        gsap.fromTo(
          fills,
          { scaleX: 0, transformOrigin: "left center" },
          {
            scaleX: 1,
            duration: 0.62,
            ease: "power3.out",
            stagger: 0.025,
            clearProps: "transform"
          }
        );
      }
    }, gridRoot.value);
  });
}

function animateDialog() {
  if (!dialogRoot.value || window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    return;
  }
  gsap.fromTo(
    dialogRoot.value,
    { autoAlpha: 0, y: 18, scale: 0.985 },
    {
      autoAlpha: 1,
      y: 0,
      scale: 1,
      duration: 0.34,
      ease: "power3.out",
      clearProps: "transform,opacity,visibility"
    }
  );
}

watch(responseAnimationKey, animateCards, { immediate: true });

watch(
  () => props.responses,
  (responses) => {
    if (!selectedResponse.value) {
      return;
    }
    const nextResponse = responses.find((response) => response.id === selectedResponse.value.id);
    if (nextResponse) {
      selectedResponse.value = nextResponse;
    }
  },
  { deep: true }
);

onMounted(() => {
  animateCards();
});

onUnmounted(() => {
  gridContext?.revert();
});
</script>
