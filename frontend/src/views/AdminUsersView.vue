<template>
  <section class="main-stage users-stage">
    <header class="topbar">
      <div>
        <p class="eyebrow">Token Quotas</p>
        <h2>用户额度</h2>
      </div>
      <el-button :loading="loading" @click="loadUsers">刷新</el-button>
    </header>

    <section class="users-summary">
      <div>
        <span>普通用户</span>
        <strong>{{ normalUserCount }}</strong>
      </div>
      <div>
        <span>今日总用量</span>
        <strong>{{ totalUsedTokens.toLocaleString("zh-CN") }}</strong>
      </div>
      <p>额度按北京时间自然日统计。管理员账号不受每日 Token 上限限制。</p>
    </section>

    <section class="config-panel">
      <el-table v-loading="loading" :data="users" row-key="id">
        <el-table-column prop="username" label="用户名" min-width="150" />
        <el-table-column label="角色" width="110">
          <template #default="{ row }">
            <el-tag :type="row.role === 'admin' ? 'warning' : 'info'" effect="plain">
              {{ row.role === "admin" ? "管理员" : "普通用户" }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'danger'" effect="plain">
              {{ row.status === "active" ? "正常" : "已禁用" }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="今日已用" min-width="150">
          <template #default="{ row }">{{ row.usedTokens.toLocaleString("zh-CN") }}</template>
        </el-table-column>
        <el-table-column label="每日额度" min-width="180">
          <template #default="{ row }">
            <span v-if="row.role === 'admin'">不限额</span>
            <el-input-number
              v-else
              v-model="draftLimits[row.id]"
              :min="0"
              :step="10000"
              controls-position="right"
            />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.role !== 'admin'"
              type="primary"
              plain
              :loading="savingIds.includes(row.id)"
              @click="saveQuota(row)"
            >
              保存
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import { ElMessage } from "element-plus";

import { listAdminUsers, updateUserQuota } from "../utils/api";

const users = ref([]);
const loading = ref(false);
const savingIds = ref([]);
const draftLimits = reactive({});

const normalUserCount = computed(() => users.value.filter((user) => user.role === "user").length);
const totalUsedTokens = computed(() => users.value.reduce((total, user) => total + user.usedTokens, 0));

async function loadUsers() {
  loading.value = true;
  try {
    users.value = await listAdminUsers();
    users.value.forEach((user) => {
      if (user.dailyLimit !== null) {
        draftLimits[user.id] = user.dailyLimit;
      }
    });
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || error?.message || "用户额度加载失败");
  } finally {
    loading.value = false;
  }
}

async function saveQuota(user) {
  savingIds.value = [...savingIds.value, user.id];
  try {
    const updated = await updateUserQuota(user.id, { dailyLimit: draftLimits[user.id] });
    users.value = users.value.map((item) => (item.id === updated.id ? updated : item));
    draftLimits[updated.id] = updated.dailyLimit;
    ElMessage.success("每日额度已更新");
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || error?.message || "额度更新失败");
  } finally {
    savingIds.value = savingIds.value.filter((id) => id !== user.id);
  }
}

onMounted(loadUsers);
</script>
