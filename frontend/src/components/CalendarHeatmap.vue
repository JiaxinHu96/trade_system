<template>
  <div class="chart-card">
    <div class="heatmap-header">
      <div>
        <div class="chart-title">Trading Calendar</div>
        <div class="heatmap-subtitle">Click a day to filter the dashboard</div>
      </div>
      <div class="heatmap-controls">
        <button class="secondary small-btn" @click="changeMonth(-1)">‹</button>
        <div class="heatmap-month">{{ monthLabel }}</div>
        <button class="secondary small-btn" @click="changeMonth(1)">›</button>
      </div>
    </div>
    <div class="heatmap-grid week-head">
      <div v-for="day in ['Sun','Mon','Tue','Wed','Thu','Fri','Sat']" :key="day" class="heatmap-weekday">{{ day }}</div>
    </div>
    <div class="heatmap-grid">
      <button
        v-for="cell in cells"
        :key="cell.key"
        :class="['heatmap-cell', { muted: !cell.inMonth, active: selectedDate === cell.iso, positive: cell.value > 0, negative: cell.value < 0 }]"
        @click="cell.iso && $emit('select-date', cell.iso)"
        :disabled="!cell.iso"
      >
        <span class="heatmap-day">{{ cell.day }}</span>
        <span class="heatmap-value">{{ cell.valueLabel }}</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  points: { type: Array, default: () => [] },
  selectedDate: { type: String, default: '' },
})
const emit = defineEmits(['select-date'])

const monthCursor = ref(null)

const pointMap = computed(() => {
  const map = {}
  for (const p of props.points) map[p.date] = Number(p.realized_pnl)
  return map
})

watch(() => props.points, (points) => {
  if (!monthCursor.value && points.length) {
    monthCursor.value = points[points.length - 1].date.slice(0, 7)
  }
}, { immediate: true })

const monthLabel = computed(() => {
  if (!monthCursor.value) return 'No data'
  const [year, month] = monthCursor.value.split('-').map(Number)
  return new Date(year, month - 1, 1).toLocaleDateString(undefined, { month: 'long', year: 'numeric' })
})

const cells = computed(() => {
  if (!monthCursor.value) return []
  const [year, month] = monthCursor.value.split('-').map(Number)
  const first = new Date(year, month - 1, 1)
  const start = new Date(first)
  start.setDate(1 - first.getDay())
  const result = []
  for (let i = 0; i < 42; i += 1) {
    const current = new Date(start)
    current.setDate(start.getDate() + i)
    const iso = current.toISOString().slice(0, 10)
    const inMonth = current.getMonth() === month - 1
    const value = pointMap.value[iso] ?? null
    result.push({
      key: iso,
      iso: inMonth ? iso : '',
      inMonth,
      day: current.getDate(),
      value,
      valueLabel: value === null ? '' : (value > 0 ? `+${value.toFixed(1)}` : value.toFixed(1)),
    })
  }
  return result
})

function changeMonth(delta) {
  if (!monthCursor.value) return
  const [year, month] = monthCursor.value.split('-').map(Number)
  const next = new Date(year, month - 1 + delta, 1)
  monthCursor.value = `${next.getFullYear()}-${String(next.getMonth() + 1).padStart(2, '0')}`
}
</script>
