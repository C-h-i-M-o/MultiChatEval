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
        <RouterLink to="/" class="nav-item" active-class="active" exact-active-class="active">
          对比评测
        </RouterLink>
        <RouterLink v-if="authStore.isAdmin" to="/models" class="nav-item" active-class="active">
          模型配置
        </RouterLink>
        <RouterLink to="/history" class="nav-item" active-class="active">
          历史任务
        </RouterLink>
      </nav>

      <section class="sidebar-user">
        <div>
          <p class="panel-label">当前用户</p>
          <strong>{{ authStore.user?.username }}</strong>
          <span>{{ authStore.isAdmin ? "管理员" : "普通用户" }}</span>
        </div>
        <el-button text class="sidebar-logout" @click="logout">退出</el-button>
      </section>

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

    <RouterView />
  </main>
</template>

<script setup>
import { useRouter } from "vue-router";

import { useAuthStore } from "../stores/auth";

const router = useRouter();
const authStore = useAuthStore();

async function logout() {
  await authStore.logout();
  await router.replace("/login");
}
</script>
