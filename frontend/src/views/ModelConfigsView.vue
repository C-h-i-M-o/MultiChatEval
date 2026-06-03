<template>
  <ModelConfigPanel
    class="main-stage"
    :configs="modelConfigs"
    :loading="modelConfigLoading"
    @refresh="loadModelConfigs"
  />
</template>

<script setup>
import { onMounted, ref } from "vue";
import { ElMessage } from "element-plus";

import ModelConfigPanel from "../components/ModelConfigPanel.vue";
import { listModelConfigs } from "../utils/api";

const modelConfigs = ref([]);
const modelConfigLoading = ref(false);

async function loadModelConfigs() {
  modelConfigLoading.value = true;

  try {
    modelConfigs.value = await listModelConfigs();
  } catch (error) {
    ElMessage.error(error?.message || "模型配置加载失败");
  } finally {
    modelConfigLoading.value = false;
  }
}

onMounted(loadModelConfigs);
</script>
