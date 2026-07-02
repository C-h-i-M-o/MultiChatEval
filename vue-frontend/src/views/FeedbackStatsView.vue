<template>
  <section class="main-stage feedback-stage">
    <header class="topbar feedback-topbar">
      <div>
        <p class="eyebrow">{{ authStore.isAdmin ? "System Signals" : "My Signals" }}</p>
        <h2>{{ authStore.isAdmin ? "全局反馈统计" : "我的反馈统计" }}</h2>
      </div>
      <div class="feedback-toolbar">
        <el-radio-group v-model="rangeName" size="small" @change="handleRangeChange">
          <el-radio-button v-for="option in feedbackRangeOptions" :key="option.value" :value="option.value">
            {{ option.label }}
          </el-radio-button>
        </el-radio-group>
        <el-button :loading="loading" @click="loadStats">刷新</el-button>
      </div>
    </header>

    <section class="feedback-hero">
      <div>
        <p class="panel-label">{{ authStore.isAdmin ? "管理视角" : "个人视角" }}</p>
        <h3>{{ authStore.isAdmin ? "把分散的评价信号，收束成模型质量脉络。" : "看看你的评测，正在积累怎样的质量信号。" }}</h3>
      </div>
      <p>
        {{
          authStore.isAdmin
            ? "覆盖全部公开、私有与历史匿名数据；互动明细仅管理员可见。"
            : "只统计你创建的评测表现与本人提交的互动，不展示其他用户身份。"
        }}
      </p>
    </section>

    <div v-loading="loading" class="feedback-content">
      <template v-if="stats">
        <section class="feedback-kpi-grid" aria-label="反馈统计摘要">
          <article class="feedback-kpi">
            <span>评测任务</span>
            <strong>{{ formatInteger(stats.summary.taskCount) }}</strong>
            <small>当前范围内创建</small>
          </article>
          <article class="feedback-kpi accent-score">
            <span>平均最终分</span>
            <strong>{{ formatScore(stats.summary.averageFinalScore) }}</strong>
            <small>{{ stats.summary.scoredCount }} 条有效评分</small>
          </article>
          <article class="feedback-kpi">
            <span>模型调用</span>
            <strong>{{ formatInteger(stats.summary.callCount) }}</strong>
            <small>含成功与失败回答</small>
          </article>
          <article class="feedback-kpi accent-like">
            <span>点赞率</span>
            <strong>{{ formatRate(stats.summary.likeRate) }}</strong>
            <small>{{ stats.summary.likeCount }} 赞 · {{ stats.summary.dislikeCount }} 踩</small>
          </article>
          <article class="feedback-kpi">
            <span>评论</span>
            <strong>{{ formatInteger(stats.summary.commentCount) }}</strong>
            <small>评论不参与评分</small>
          </article>
        </section>

        <section v-if="!authStore.isAdmin" class="feedback-section interaction-summary-section">
          <header class="feedback-section-head">
            <div>
              <p class="panel-label">My Activity</p>
              <h3>我的互动</h3>
            </div>
            <p>这里统计你主动提交的反馈，不等同于你的评测收到的反馈。</p>
          </header>
          <div class="personal-interaction-grid">
            <div><span>我点过赞</span><strong>{{ stats.myInteractions.likeCount }}</strong></div>
            <div><span>我点过踩</span><strong>{{ stats.myInteractions.dislikeCount }}</strong></div>
            <div><span>我发过评论</span><strong>{{ stats.myInteractions.commentCount }}</strong></div>
          </div>
        </section>

        <section class="feedback-section">
          <header class="feedback-section-head">
            <div>
              <p class="panel-label">Model Ledger</p>
              <h3>模型表现账本</h3>
            </div>
            <p>均分仅计算已有评分的数据，Judge 均分自动忽略空值。</p>
          </header>
          <el-table :data="stats.models" :row-key="modelRowKey" empty-text="当前范围内暂无模型数据">
            <el-table-column prop="modelName" label="模型" min-width="170" fixed="left" />
            <el-table-column label="调用 / 已评分" min-width="125">
              <template #default="{ row }">{{ row.callCount }} / {{ row.scoredCount }}</template>
            </el-table-column>
            <el-table-column label="最终分" min-width="90">
              <template #default="{ row }"><strong>{{ formatScore(row.averageFinalScore) }}</strong></template>
            </el-table-column>
            <el-table-column label="规则分" min-width="90">
              <template #default="{ row }">{{ formatScore(row.averageRuleScore) }}</template>
            </el-table-column>
            <el-table-column label="Judge" min-width="90">
              <template #default="{ row }">{{ formatScore(row.averageJudgeScore) }}</template>
            </el-table-column>
            <el-table-column label="点赞率" min-width="110">
              <template #default="{ row }">{{ formatRate(row.likeRate) }}</template>
            </el-table-column>
            <el-table-column label="赞 / 踩 / 评" min-width="125">
              <template #default="{ row }">{{ row.likeCount }} / {{ row.dislikeCount }} / {{ row.commentCount }}</template>
            </el-table-column>
          </el-table>
        </section>

        <section class="feedback-section trend-section">
          <header class="feedback-section-head">
            <div>
              <p class="panel-label">Daily Pulse</p>
              <h3>每日反馈脉冲</h3>
            </div>
            <p>轨道长度表示当日互动量，评分与调用按回答创建日期归档。</p>
          </header>
          <el-empty v-if="!stats.trend.length" description="当前范围内暂无趋势数据" />
          <div v-else class="feedback-trend-list">
            <article v-for="point in stats.trend" :key="point.date" class="feedback-trend-row">
              <time>{{ formatDate(point.date) }}</time>
              <div class="trend-rail" aria-hidden="true">
                <span :style="{ width: trendWidth(point, stats.trend) }"></span>
              </div>
              <div class="trend-score"><span>均分</span><strong>{{ formatScore(point.averageFinalScore) }}</strong></div>
              <div class="trend-counts">{{ point.callCount }} 调用 · {{ point.likeCount }} 赞 · {{ point.dislikeCount }} 踩 · {{ point.commentCount }} 评</div>
            </article>
          </div>
        </section>

        <section v-if="authStore.isAdmin" class="feedback-section activity-section">
          <header class="feedback-section-head activity-head">
            <div>
              <p class="panel-label">Audit Stream</p>
              <h3>最近互动明细</h3>
            </div>
            <div class="activity-filters">
              <el-select v-model="activityType" aria-label="互动类型" @change="handleActivityFilterChange">
                <el-option label="全部互动" value="all" />
                <el-option label="点赞" value="like" />
                <el-option label="点踩" value="dislike" />
                <el-option label="评论" value="comment" />
              </el-select>
              <el-select
                v-model="modelConfigId"
                clearable
                aria-label="模型筛选"
                placeholder="全部模型"
                @change="handleActivityFilterChange"
              >
                <el-option
                  v-for="model in stats.models.filter((item) => item.modelConfigId !== null)"
                  :key="model.modelConfigId"
                  :label="model.modelName"
                  :value="model.modelConfigId"
                />
              </el-select>
            </div>
          </header>
          <el-table :data="stats.activities.items" :row-key="activityRowKey" empty-text="没有符合条件的互动明细">
            <el-table-column label="类型" width="90">
              <template #default="{ row }">
                <el-tag :type="activityTagType(row.activityType)" effect="plain">
                  {{ activityTypeLabel(row.activityType) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="username" label="用户" min-width="120" />
            <el-table-column prop="modelName" label="模型" min-width="150" />
            <el-table-column prop="prompt" label="问题" min-width="220" show-overflow-tooltip />
            <el-table-column label="内容" min-width="220" show-overflow-tooltip>
              <template #default="{ row }">{{ row.content || "—" }}</template>
            </el-table-column>
            <el-table-column label="时间" min-width="170">
              <template #default="{ row }">{{ formatDateTime(row.createdAt) }}</template>
            </el-table-column>
          </el-table>
          <el-pagination
            v-if="stats.activities.total > 0"
            class="feedback-pagination"
            background
            layout="total, sizes, prev, pager, next"
            :total="stats.activities.total"
            :current-page="activityPage"
            :page-size="activityPageSize"
            :page-sizes="[10, 20, 50]"
            @current-change="handleActivityPageChange"
            @size-change="handleActivityPageSizeChange"
          />
        </section>
      </template>

      <el-empty v-else-if="!loading" description="反馈统计暂时不可用">
        <el-button type="primary" plain @click="loadStats">重新加载</el-button>
      </el-empty>
    </div>
  </section>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { ElMessage } from "element-plus";

import { useAuthStore } from "../stores/auth";
import { getAdminFeedbackStats, getPersonalFeedbackStats } from "../utils/api";
import { getApiErrorMessage } from "../utils/errors";
import {
  activityRowKey,
  activityTypeLabel,
  feedbackRangeOptions,
  formatRate,
  formatScore,
  modelRowKey,
  trendWidth
} from "../utils/feedbackStats";

const authStore = useAuthStore();
const stats = ref(null);
const loading = ref(false);
const rangeName = ref("30d");
const activityType = ref("all");
const modelConfigId = ref(null);
const activityPage = ref(1);
const activityPageSize = ref(20);

async function loadStats() {
  loading.value = true;
  try {
    stats.value = authStore.isAdmin
      ? await getAdminFeedbackStats({
          range: rangeName.value,
          activityType: activityType.value,
          modelConfigId: modelConfigId.value || undefined,
          page: activityPage.value,
          pageSize: activityPageSize.value
        })
      : await getPersonalFeedbackStats(rangeName.value);
  } catch (error) {
    stats.value = null;
    ElMessage.error(getApiErrorMessage(error, "反馈统计加载失败"));
  } finally {
    loading.value = false;
  }
}

function handleRangeChange() {
  activityPage.value = 1;
  loadStats();
}

function handleActivityFilterChange() {
  activityPage.value = 1;
  loadStats();
}

function handleActivityPageChange(page) {
  activityPage.value = page;
  loadStats();
}

function handleActivityPageSizeChange(pageSize) {
  activityPageSize.value = pageSize;
  activityPage.value = 1;
  loadStats();
}

function formatInteger(value) {
  return Number(value || 0).toLocaleString("zh-CN");
}

function formatDate(value) {
  return new Intl.DateTimeFormat("zh-CN", {
    timeZone: "Asia/Shanghai",
    month: "2-digit",
    day: "2-digit"
  }).format(new Date(`${value}T00:00:00+08:00`));
}

function formatDateTime(value) {
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

function activityTagType(type) {
  return { like: "success", dislike: "danger", comment: "info" }[type] || "info";
}

onMounted(loadStats);
</script>
