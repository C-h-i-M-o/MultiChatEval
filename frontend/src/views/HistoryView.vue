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
            <el-tag :type="statusTagType(store.selectedHistoryTask.status)" effect="plain">
              {{ statusText(store.selectedHistoryTask.status) }}
            </el-tag>
          </div>

          <div class="history-response-list">
            <ModelResponseCard
              v-for="response in store.selectedHistoryTask.responses"
              :key="response.id"
              :response="response"
              show-actions
            />
          </div>
        </div>
      </section>
    </section>
  </section>
</template>

<script setup>
import { onMounted } from "vue";

import ModelResponseCard from "../components/ModelResponseCard.vue";
import { useEvaluationStore } from "../stores/evaluation";

const store = useEvaluationStore();
const HISTORY_PENDING_TIMEOUT_MS = 120 * 1000;

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
