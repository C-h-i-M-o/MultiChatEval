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
        <dd><CostDetailsPopover :response="response" /></dd>
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
      <el-button v-if="!embeddedDetail" @click="detailVisible = true">详情</el-button>
    </footer>

    <section v-if="embeddedDetail && !response.pending" class="score-detail embedded-score-detail">
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
            <dt>基础分</dt>
            <dd>{{ score.baseFinal ?? score.final }}</dd>
          </div>
          <div>
            <dt>反馈分</dt>
            <dd>{{ feedbackScoreText }}</dd>
          </div>
          <div>
            <dt>耗时</dt>
            <dd>{{ response.latencyMs || 0 }}ms</dd>
          </div>
          <div>
            <dt>总 Token</dt>
            <dd>{{ response.totalTokens || 0 }}</dd>
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
          <em>权重 10%</em>
        </header>
        <p>
          点赞 {{ feedback.likeCount }} 次，点踩 {{ feedback.dislikeCount }} 次；当前匿名用户反馈为{{ currentFeedbackText }}。
        </p>
        <p>{{ feedbackFormulaText }}</p>
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

      <section class="comment-panel">
        <header class="comment-panel-head">
          <div>
            <p class="panel-label">公开讨论</p>
            <h4>回答评论</h4>
          </div>
          <span>{{ commentTotal }} 条</span>
        </header>

        <div class="comment-composer">
          <el-input
            v-model="commentContent"
            type="textarea"
            :rows="3"
            maxlength="1000"
            show-word-limit
            resize="vertical"
            placeholder="写下你对这个回答的看法"
          />
          <div class="comment-composer-actions">
            <span>评论公开展示，不参与评分。</span>
            <el-button
              type="primary"
              :loading="commentSubmitting"
              :disabled="!commentContent.trim()"
              @click="submitComment"
            >
              发布评论
            </el-button>
          </div>
        </div>

        <div v-loading="commentsLoading" class="comment-list">
          <article v-for="comment in comments" :key="comment.id" class="comment-item">
            <header>
              <div>
                <strong>{{ comment.username }}</strong>
                <time>{{ formatCommentTime(comment.createdAt) }}</time>
              </div>
              <el-button
                v-if="comment.canDelete"
                link
                type="danger"
                :loading="deletingCommentIds.includes(comment.id)"
                @click="removeComment(comment)"
              >
                删除
              </el-button>
            </header>
            <p>{{ comment.content }}</p>
          </article>
          <el-empty v-if="!commentsLoading && !comments.length" description="还没有评论，来写第一条吧" />
        </div>

        <el-pagination
          v-if="commentTotal > commentPageSize"
          class="comment-pagination"
          background
          layout="prev, pager, next"
          :current-page="commentPage"
          :page-size="commentPageSize"
          :total="commentTotal"
          @current-change="changeCommentPage"
        />
      </section>
    </section>

    <el-dialog v-else v-model="detailVisible" title="评分详情" width="min(760px, 94vw)" class="score-detail-dialog">
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
              <dt>基础分</dt>
              <dd>{{ score.baseFinal ?? score.final }}</dd>
            </div>
            <div>
              <dt>反馈分</dt>
              <dd>{{ feedbackScoreText }}</dd>
            </div>
            <div>
              <dt>耗时</dt>
              <dd>{{ response.latencyMs || 0 }}ms</dd>
            </div>
            <div>
              <dt>总 Token</dt>
              <dd>{{ response.totalTokens || 0 }}</dd>
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
            <em>权重 10%</em>
          </header>
          <p>
            点赞 {{ feedback.likeCount }} 次，点踩 {{ feedback.dislikeCount }} 次；当前匿名用户反馈为{{ currentFeedbackText }}。
          </p>
          <p>{{ feedbackFormulaText }}</p>
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

        <section class="comment-panel">
          <header class="comment-panel-head">
            <div>
              <p class="panel-label">公开讨论</p>
              <h4>回答评论</h4>
            </div>
            <span>{{ commentTotal }} 条</span>
          </header>

          <div class="comment-composer">
            <el-input
              v-model="commentContent"
              type="textarea"
              :rows="3"
              maxlength="1000"
              show-word-limit
              resize="vertical"
              placeholder="写下你对这个回答的看法"
            />
            <div class="comment-composer-actions">
              <span>评论公开展示，不参与评分。</span>
              <el-button
                type="primary"
                :loading="commentSubmitting"
                :disabled="!commentContent.trim()"
                @click="submitComment"
              >
                发布评论
              </el-button>
            </div>
          </div>

          <div v-loading="commentsLoading" class="comment-list">
            <article v-for="comment in comments" :key="comment.id" class="comment-item">
              <header>
                <div>
                  <strong>{{ comment.username }}</strong>
                  <time>{{ formatCommentTime(comment.createdAt) }}</time>
                </div>
                <el-button
                  v-if="comment.canDelete"
                  link
                  type="danger"
                  :loading="deletingCommentIds.includes(comment.id)"
                  @click="removeComment(comment)"
                >
                  删除
                </el-button>
              </header>
              <p>{{ comment.content }}</p>
            </article>
            <el-empty v-if="!commentsLoading && !comments.length" description="还没有评论，来写第一条吧" />
          </div>

          <el-pagination
            v-if="commentTotal > commentPageSize"
            class="comment-pagination"
            background
            layout="prev, pager, next"
            :current-page="commentPage"
            :page-size="commentPageSize"
            :total="commentTotal"
            @current-change="changeCommentPage"
          />
        </section>
      </section>
    </el-dialog>
  </article>
</template>

<script setup>
import { ElMessage, ElMessageBox } from "element-plus";
import { computed, ref, watch } from "vue";

import {
  createResponseComment,
  deleteResponseComment,
  listResponseComments
} from "../utils/api";
import CostDetailsPopover from "./CostDetailsPopover.vue";
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
  },
  embeddedDetail: {
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
    baseFinal: 0,
    feedbackScore: null,
    judgeComment: null,
    judgeDetails: {}
  };
});

const detailVisible = ref(false);
const comments = ref([]);
const commentTotal = ref(0);
const commentPage = ref(1);
const commentPageSize = 10;
const commentsLoading = ref(false);
const commentSubmitting = ref(false);
const deletingCommentIds = ref([]);
const commentContent = ref("");

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

const feedbackScoreText = computed(() => {
  return score.value.feedbackScore === null || score.value.feedbackScore === undefined
    ? "暂无反馈"
    : `${score.value.feedbackScore} / 10`;
});

const feedbackFormulaText = computed(() => {
  if (score.value.feedbackScore === null || score.value.feedbackScore === undefined) {
    return "暂无点赞或点踩，最终分保持基础分不变。";
  }
  return `最终分 = 基础分 ${score.value.baseFinal} × 90% + 反馈分 ${score.value.feedbackScore} × 10%。`;
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

async function loadComments(page = commentPage.value) {
  if (!props.response.id) {
    return;
  }
  commentsLoading.value = true;
  try {
    const result = await listResponseComments(props.response.id, {
      page,
      pageSize: commentPageSize
    });
    comments.value = result.items;
    commentTotal.value = result.total;
    commentPage.value = result.page;
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || error?.message || "评论加载失败");
  } finally {
    commentsLoading.value = false;
  }
}

async function submitComment() {
  const content = commentContent.value.trim();
  if (!content || commentSubmitting.value) {
    return;
  }
  commentSubmitting.value = true;
  try {
    await createResponseComment(props.response.id, { content });
    commentContent.value = "";
    await loadComments(1);
    ElMessage.success("评论已发布");
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || error?.message || "评论发布失败");
  } finally {
    commentSubmitting.value = false;
  }
}

async function removeComment(comment) {
  try {
    await ElMessageBox.confirm("删除后无法恢复，确定删除这条评论吗？", "删除评论", {
      confirmButtonText: "删除",
      cancelButtonText: "取消",
      type: "warning"
    });
  } catch {
    return;
  }

  deletingCommentIds.value = [...deletingCommentIds.value, comment.id];
  try {
    await deleteResponseComment(comment.id);
    const nextTotal = Math.max(commentTotal.value - 1, 0);
    const lastPage = Math.max(Math.ceil(nextTotal / commentPageSize), 1);
    await loadComments(Math.min(commentPage.value, lastPage));
    ElMessage.success("评论已删除");
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || error?.message || "评论删除失败");
  } finally {
    deletingCommentIds.value = deletingCommentIds.value.filter((id) => id !== comment.id);
  }
}

async function changeCommentPage(page) {
  await loadComments(page);
}

function formatCommentTime(value) {
  if (!value) {
    return "";
  }
  return new Intl.DateTimeFormat("zh-CN", {
    timeZone: "Asia/Shanghai",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false
  }).format(new Date(value));
}

watch(detailVisible, (visible) => {
  if (visible) {
    loadComments(1);
  }
});

watch(
  () => props.embeddedDetail,
  (embedded) => {
    if (embedded) {
      loadComments(1);
    }
  },
  { immediate: true }
);

watch(
  () => props.response.id,
  () => {
    comments.value = [];
    commentTotal.value = 0;
    commentPage.value = 1;
    commentContent.value = "";
  }
);
</script>
