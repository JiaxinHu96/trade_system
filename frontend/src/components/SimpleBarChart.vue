<template>
  <div class="chart-card compact-chart-card">
    <div class="chart-title">{{ title }}</div>
    <div v-if="!items.length" class="empty-row">No chart data.</div>
    <div v-else class="bar-chart-list compact-bar-list">
      <div v-for="item in normalizedItems" :key="item.label" class="bar-row">
        <div class="bar-row-head">
          <span class="bar-label">{{ item.label }}</span>
          <span class="bar-value">{{ item.valueLabel }}</span>
        </div>
        <div class="bar-track">
          <div class="bar-fill" :class="{ negative: item.rawValue < 0 }" :style="{ width: item.width + '%' }"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { formatNumber } from '../utils/formatters'

const props = defineProps({
  title: String,
  items: { type: Array, default: () => [] },
})

const normalizedItems = computed(() => {
  const maxAbs = Math.max(...props.items.map((item) => Math.abs(Number(item.value))), 1)
  return props.items.map((item) => ({
    ...item,
    rawValue: Number(item.value),
    width: Math.max(4, Math.abs(Number(item.value)) / maxAbs * 100),
    valueLabel: item.valueLabel ?? formatNumber(item.value),
  }))
})
</script>
