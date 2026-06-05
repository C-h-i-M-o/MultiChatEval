<template>
  <section class="main-stage history-stage">
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
            <el-tag :type="selectedHistoryStatusTagType" effect="plain">
              {{ selectedHistoryStatusText }}
            </el-tag>
          </div>

          <div
            v-if="store.selectedHistoryTask.responses.length === 0"
            class="history-empty-detail"
            :class="{ timeout: selectedHistoryTaskIsStale }"
          >
            <p class="panel-label">{{ selectedHistoryStatusText }}</p>
            <h4>{{ emptyDetailTitle }}</h4>
            <p>{{ emptyDetailDescription }}</p>
            <el-button :loading="store.historyDetailLoading" @click="loadHistoryTask(store.selectedHistoryTask.taskId)">
              重新加载
            </el-button>
          </div>

          <div v-else class="history-response-list">
            <ModelResponseCard
              v-for="response in store.selectedHistoryTask.responses"
              :key="response.id"
              :response="response"
              :feedback-submitting="store.feedbackSubmittingIds.includes(response.id)"
              show-actions
              @feedback="handleFeedback"
            />
          </div>
        </div>
      </section>
    </section>
  </section>
</template>

<script setup>
import { computed, onMounted } from "vue";
import { ElMessage } from "element-plus";

import ModelResponseCard from "../components/ModelResponseCard.vue";
import { useEvaluationStore } from "../stores/evaluation";

const store = useEvaluationStore();
const HISTORY_PENDING_TIMEOUT_MS = 120 * 1000;
const selectedHistoryItem = computed(() => {
  return store.historyItems.find((taskItem) => taskItem.taskId === store.selectedHistoryTask?.taskId) || null;
});
const selectedHistoryTaskStatusSource = computed(() => {
  return selectedHistoryItem.value || store.selectedHistoryTask;
});
const selectedHistoryTaskIsStale = computed(() => {
  return selectedHistoryTaskStatusSource.value ? isStalePendingTask(selectedHistoryTaskStatusSource.value) : false;
});
const selectedHistoryStatusText = computed(() => {
  return selectedHistoryTaskStatusSource.value ? historyStatusText(selectedHistoryTaskStatusSource.value) : "未知状态";
});
const selectedHistoryStatusTagType = computed(() => {
  return selectedHistoryTaskStatusSource.value ? historyStatusTagType(selectedHistoryTaskStatusSource.value) : "info";
});
const emptyDetailTitle = computed(() => {
  if (selectedHistoryTaskIsStale.value) {
    return "任务超时未完成";
  }
  if (store.selectedHistoryTask?.status === "pending" || store.selectedHistoryTask?.status === "running") {
    return "模型回答仍在生成";
  }
  return "暂无模型回答";
});
const emptyDetailDescription = computed(() => {
  if (selectedHistoryTaskIsStale.value) {
    return "该任务超过等待时间后仍未产生模型回答，可以刷新历史任务或重新发起评测。";
  }
  if (store.selectedHistoryTask?.status === "pending" || store.selectedHistoryTask?.status === "running") {
    return "模型请求尚未完成，可以稍后重新加载详情查看最新结果。";
  }
  return "该任务没有可展示的模型回答。";
});

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

onMounted(() => {
  store.loadHistory(1, store.historyPageSize);
});
</script>
