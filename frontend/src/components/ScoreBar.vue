<template>
  <div class="score-bar">
    <span>{{ label }}</span>
    <div class="bar-track">
      <i :style="{ width: `${normalizedValue}%` }"></i>
    </div>
    <strong>{{ value }}</strong>
  </div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  label: {
    type: String,
    required: true
  },
  value: {
    type: Number,
    required: true
  }
});

const normalizedValue = computed(() => Math.max(0, Math.min(props.value * 10, 100)));
</script>
