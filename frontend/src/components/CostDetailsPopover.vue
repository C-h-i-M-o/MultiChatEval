<template>
  <span
    class="cost-popover"
    @mouseenter="showDetails"
    @mouseleave="hideDetails"
    @focusin="showDetails"
    @focusout="hideDetails"
  >
    <button
      type="button"
      class="cost-popover-trigger"
      :aria-expanded="detailsVisible"
      aria-label="查看费用明细"
      @click.stop="toggleTouchDetails"
    >
      {{ totalText }}
    </button>
    <span v-if="detailsVisible" class="cost-popover-panel" role="tooltip">
      <span class="cost-popover-title">费用明细</span>
      <span v-for="item in items" :key="item.key" class="cost-detail-row">
        <span>
          {{ item.label }}
          <small>{{ item.tokens.toLocaleString("zh-CN") }} tokens</small>
        </span>
        <strong>{{ formatMoney(item.cost, response.currency) }}</strong>
      </span>
      <span class="cost-detail-total">
        <span>合计</span>
        <strong>{{ totalText }}</strong>
      </span>
    </span>
  </span>
</template>

<script setup>
import { computed, ref } from "vue";

import { formatMoney, normalizeCostDetails } from "../utils/billing";

const props = defineProps({
  response: {
    type: Object,
    required: true
  }
});

const detailsVisible = ref(false);
const items = computed(() => normalizeCostDetails(props.response));
const totalText = computed(() => formatMoney(props.response.estimatedCost, props.response.currency));

function supportsHover() {
  return window.matchMedia("(hover: hover) and (pointer: fine)").matches;
}

function showDetails() {
  detailsVisible.value = true;
}

function hideDetails() {
  detailsVisible.value = false;
}

function toggleTouchDetails() {
  if (!supportsHover()) {
    detailsVisible.value = !detailsVisible.value;
  }
}
</script>
