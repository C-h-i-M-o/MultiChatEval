<template>
  <main class="auth-shell">
    <section class="auth-card">
      <div class="auth-brand">
        <span class="brand-mark">M</span>
        <div>
          <p class="eyebrow">MultiChatEval v2</p>
          <h1>多模型评测平台</h1>
        </div>
      </div>

      <div>
        <p class="panel-label">{{ isRegister ? "Create account" : "Welcome back" }}</p>
        <h2>{{ isRegister ? "注册账号" : "登录系统" }}</h2>
        <p class="auth-description">
          {{ isRegister ? "注册后即可创建公开或私有评测。" : "登录后继续查看评测任务与模型结果。" }}
        </p>
      </div>

      <el-form label-position="top" @submit.prevent="submit">
        <el-form-item label="用户名">
          <el-input v-model="username" autocomplete="username" maxlength="64" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input
            v-model="password"
            type="password"
            show-password
            :autocomplete="isRegister ? 'new-password' : 'current-password'"
            maxlength="128"
            @keyup.enter="submit"
          />
        </el-form-item>
        <el-button class="auth-submit" type="primary" :loading="authStore.loading" @click="submit">
          {{ isRegister ? "注册并登录" : "登录" }}
        </el-button>
      </el-form>

      <p class="auth-switch">
        {{ isRegister ? "已有账号？" : "还没有账号？" }}
        <RouterLink :to="isRegister ? '/login' : '/register'">
          {{ isRegister ? "返回登录" : "立即注册" }}
        </RouterLink>
      </p>
    </section>
  </main>
</template>

<script setup>
import { computed, ref } from "vue";
import { ElMessage } from "element-plus";
import { useRoute, useRouter } from "vue-router";

import { useAuthStore } from "../stores/auth";

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();
const username = ref("");
const password = ref("");
const isRegister = computed(() => route.name === "register");

async function submit() {
  const credentials = {
    username: username.value.trim(),
    password: password.value
  };
  if (!credentials.username || !credentials.password) {
    ElMessage.warning("请输入用户名和密码");
    return;
  }

  try {
    if (isRegister.value) {
      await authStore.register(credentials);
    } else {
      await authStore.login(credentials);
    }
    const redirectPath = typeof route.query.redirect === "string" ? route.query.redirect : "/";
    await router.replace(redirectPath);
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || "认证失败，请检查输入");
  }
}
</script>
