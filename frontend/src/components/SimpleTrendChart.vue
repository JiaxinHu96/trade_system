<template>
  <div class="chart-card compact-chart-card">
    <div class="chart-title-row">
      <div>
        <div class="chart-title">{{ title }}</div>
        <div class="chart-subtitle">Hover for tooltip · clearer axes · smarter date labels</div>
      </div>
      <div class="chart-toggle-group">
        <button class="chart-toggle" :class="{ active: mode === 'bar' }" @click="mode = 'bar'">Bar</button>
        <button class="chart-toggle" :class="{ active: mode === 'line' }" @click="mode = 'line'">Line</button>
      </div>
    </div>

    <div v-if="!normalizedPoints.length" class="empty-row">No chart data.</div>
    <div v-else class="svg-chart-shell" @mouseleave="tooltip = null">
      <svg :viewBox="`0 0 ${width} ${height}`" class="svg-chart">
        <g>
          <line
            v-for="tick in yTicks"
            :key="`grid-${tick.value}`"
            :x1="margins.left"
            :x2="width - margins.right"
            :y1="tick.y"
            :y2="tick.y"
            class="chart-grid-line"
          />

          <line :x1="margins.left" :x2="margins.left" :y1="margins.top" :y2="height - margins.bottom" class="chart-axis" />
          <line :x1="margins.left" :x2="width - margins.right" :y1="zeroY" :y2="zeroY" class="chart-axis" />

          <text
            v-for="tick in yTicks"
            :key="`label-${tick.value}`"
            :x="margins.left - 8"
            :y="tick.y + 4"
            text-anchor="end"
            class="chart-axis-label"
          >
            {{ tick.label }}
          </text>

          <template v-if="mode === 'bar'">
            <g v-for="point in normalizedPoints" :key="`bar-${point.index}`">
              <rect
                :x="point.barX"
                :y="point.rectY"
                :width="point.barWidth"
                :height="point.rectHeight"
                rx="6"
                :class="point.value >= 0 ? 'chart-bar-positive' : 'chart-bar-negative'"
                @mousemove="showTooltip($event, point)"
              />
            </g>
          </template>

          <template v-else>
            <path :d="linePath" class="chart-line" fill="none" />
            <circle
              v-for="point in normalizedPoints"
              :key="`dot-${point.index}`"
              :cx="point.centerX"
              :cy="point.y"
              r="4.5"
              class="chart-dot"
              @mousemove="showTooltip($event, point)"
            />
          </template>

          <text
            v-for="point in xTickPoints"
            :key="`x-${point.index}`"
            :x="point.centerX"
            :y="height - 10"
            text-anchor="middle"
            class="chart-axis-label x"
          >
            {{ point.label }}
          </text>
        </g>
      </svg>

      <div
        v-if="tooltip"
        class="chart-tooltip"
        :style="{ left: `${tooltip.x}px`, top: `${tooltip.y}px` }"
      >
        <div class="chart-tooltip-label">{{ tooltip.label }}</div>
        <div class="chart-tooltip-value">{{ tooltip.valueLabel }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { formatNumber } from '../utils/formatters'

const props = defineProps({
  title: String,
  points: { type: Array, default: () => [] },
})

const mode = ref('bar')
const tooltip = ref(null)
const width = 820
const height = 310
const margins = { top: 20, right: 20, bottom: 44, left: 56 }
const plotWidth = width - margins.left - margins.right
const plotHeight = height - margins.top - margins.bottom

const normalizedPoints = computed(() => {
  const points = props.points.map((item, index) => ({
    ...item,
    index,
    value: Number(item.value),
    valueLabel: item.valueLabel ?? formatNumber(item.value),
  }))
  if (!points.length) return []

  const minValue = Math.min(...points.map((p) => p.value), 0)
  const maxValue = Math.max(...points.map((p) => p.value), 0)
  const range = maxValue - minValue || 1
  const step = points.length > 1 ? plotWidth / (points.length - 1) : 0
  const barSlot = plotWidth / Math.max(points.length, 1)
  const barWidth = Math.max(12, Math.min(28, barSlot * 0.6))

  const yScale = (value) => margins.top + ((maxValue - value) / range) * plotHeight
  const zeroLine = yScale(0)

  return points.map((point, index) => {
    const centerX = margins.left + (points.length === 1 ? plotWidth / 2 : step * index)
    const y = yScale(point.value)
    return {
      ...point,
      centerX,
      y,
      barWidth,
      barX: centerX - barWidth / 2,
      rectY: point.value >= 0 ? y : zeroLine,
      rectHeight: Math.max(2, Math.abs(zeroLine - y)),
      zeroLine,
    }
  })
})

const minMax = computed(() => {
  const values = normalizedPoints.value.map((p) => p.value)
  const min = values.length ? Math.min(...values, 0) : 0
  const max = values.length ? Math.max(...values, 0) : 0
  return { min, max, range: max - min || 1 }
})

const zeroY = computed(() => {
  const { min, max, range } = minMax.value
  return margins.top + ((max - 0) / range) * plotHeight
})

const yTicks = computed(() => {
  const { min, max } = minMax.value
  const tickCount = 5
  return Array.from({ length: tickCount }, (_, idx) => {
    const value = max - ((max - min) * idx) / (tickCount - 1)
    const y = margins.top + (idx * plotHeight) / (tickCount - 1)
    return { value, y, label: formatNumber(value) }
  })
})

const xTickPoints = computed(() => {
  const points = normalizedPoints.value
  if (!points.length) return []
  const maxLabels = 8
  const step = Math.max(1, Math.ceil(points.length / maxLabels))
  return points.filter((point, idx) => idx % step === 0 || idx === points.length - 1)
})

const linePath = computed(() => {
  const points = normalizedPoints.value
  if (!points.length) return ''
  return points
    .map((point, idx) => `${idx === 0 ? 'M' : 'L'} ${point.centerX} ${point.y}`)
    .join(' ')
})

function showTooltip(event, point) {
  const shell = event.currentTarget.ownerSVGElement.getBoundingClientRect()
  tooltip.value = {
    label: point.label,
    valueLabel: point.valueLabel,
    x: event.clientX - shell.left + 12,
    y: event.clientY - shell.top - 10,
  }
}
</script>
