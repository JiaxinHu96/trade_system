<template>
  <div :class="['card', 'stat-card', { compact }]">
    <div class="stat-label">{{ label }}</div>
    <div class="stat-value" :class="{ compact }">{{ displayValue }}</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { formatNumber } from '../utils/formatters'

const props = defineProps({
  label: String,
  value: [String, Number],
  compact: { type: Boolean, default: false },
})

const displayValue = computed(() => {
  if (typeof props.value === 'string' && isNaN(Number(props.value))) return props.value
  return formatNumber(props.value)
})
</script>
