<template>
  <div class="chart-card compact-chart-card">
    <div class="chart-head">
      <div class="chart-title">{{ title }}</div>
      <div class="chart-mode-switch">
        <button
          class="mode-chip"
          :class="{ active: mode === 'bar' }"
          @click="mode = 'bar'"
        >
          Bar
        </button>
        <button
          class="mode-chip"
          :class="{ active: mode === 'line' }"
          @click="mode = 'line'"
        >
          Line
        </button>
      </div>
    </div>

    <div v-if="!normalizedPoints.length" class="empty-row compact-empty">No chart data.</div>

    <template v-else>
      <div v-if="mode === 'bar'" class="mini-bar-chart">
        <div v-for="point in normalizedPoints" :key="point.label" class="mini-bar-col">
          <div class="mini-bar-value">{{ point.valueLabel }}</div>
          <div class="mini-bar-track">
            <div
              class="mini-bar-fill"
              :class="point.value >= 0 ? 'positive' : 'negative'"
              :style="{ height: point.height + '%' }"
            ></div>
          </div>
          <div class="mini-bar-label">{{ point.label }}</div>
        </div>
      </div>

      <div v-else class="line-chart-wrap">
        <svg viewBox="0 0 600 200" preserveAspectRatio="none" class="line-chart-svg">
          <defs>
            <linearGradient id="chart-fill-positive" x1="0" x2="0" y1="0" y2="1">
              <stop offset="0%" stop-color="rgba(37,99,235,0.28)" />
              <stop offset="100%" stop-color="rgba(37,99,235,0.04)" />
            </linearGradient>
          </defs>
          <polyline
            class="chart-line"
            fill="none"
            :points="linePoints"
          />
          <polygon class="chart-area" :points="areaPoints" />
          <g v-for="point in svgPoints" :key="point.label">
            <circle class="chart-dot" :cx="point.x" :cy="point.y" r="4" />
          </g>
        </svg>
        <div class="line-chart-labels">
          <span v-for="point in normalizedPoints" :key="point.label">{{ point.label }}</span>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { formatNumber } from '../utils/formatters'

const props = defineProps({
  title: String,
  points: { type: Array, default: () => [] },
  initialMode: { type: String, default: 'bar' },
})

const mode = ref(props.initialMode)

const normalizedPoints = computed(() => {
  if (!props.points.length) return []
  const values = props.points.map((item) => Number(item.value) || 0)
  const maxAbs = Math.max(...values.map((v) => Math.abs(v)), 1)
  return props.points.map((item) => {
    const value = Number(item.value) || 0
    return {
      ...item,
      value,
      valueLabel: item.valueLabel ?? formatNumber(value),
      height: Math.max(6, Math.abs(value) / maxAbs * 100),
    }
  })
})

const svgPoints = computed(() => {
  const items = normalizedPoints.value
  if (!items.length) return []
  const values = items.map((item) => item.value)
  const min = Math.min(...values)
  const max = Math.max(...values)
  const range = max - min || 1

  return items.map((item, index) => {
    const x = items.length === 1 ? 300 : (index / (items.length - 1)) * 560 + 20
    const y = 170 - ((item.value - min) / range) * 130
    return { ...item, x, y }
  })
})

const linePoints = computed(() => svgPoints.value.map((point) => `${point.x},${point.y}`).join(' '))

const areaPoints = computed(() => {
  if (!svgPoints.value.length) return ''
  const first = svgPoints.value[0]
  const last = svgPoints.value[svgPoints.value.length - 1]
  const middle = svgPoints.value.map((point) => `${point.x},${point.y}`).join(' ')
  return `${first.x},180 ${middle} ${last.x},180`
})
</script>
