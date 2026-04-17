<template>
  <div class="tv-card chart-panel">
    <div class="chart-panel-header">
      <div>
        <div class="tv-widget-title">{{ title }}</div>
        <div v-if="subtitle" class="tv-widget-subtitle">{{ subtitle }}</div>
      </div>
      <div class="chart-mode-switch">
        <button :class="['mode-pill', { active: mode === 'bar' }]" @click="mode = 'bar'">Bar</button>
        <button :class="['mode-pill', { active: mode === 'line' }]" @click="mode = 'line'">Line</button>
      </div>
    </div>

    <div v-if="!normalized.length" class="empty-row">No chart data.</div>
    <div v-else class="svg-chart-wrap" @mouseleave="hoveredIndex = null">
      <svg :viewBox="`0 0 ${svgWidth} ${svgHeight}`" class="svg-chart">
        <g>
          <line
            v-for="tick in yTicks"
            :key="`grid-${tick.value}`"
            :x1="padLeft"
            :x2="svgWidth - padRight"
            :y1="tick.y"
            :y2="tick.y"
            class="chart-grid-line"
          />
          <text
            v-for="tick in yTicks"
            :key="`label-${tick.value}`"
            :x="padLeft - 8"
            :y="tick.y + 4"
            text-anchor="end"
            class="chart-axis-text"
          >{{ tick.label }}</text>
          <line :x1="padLeft" :x2="padLeft" :y1="padTop" :y2="chartBottom" class="chart-axis-line" />
          <line :x1="padLeft" :x2="svgWidth - padRight" :y1="chartBottom" :y2="chartBottom" class="chart-axis-line" />
        </g>

        <template v-if="mode === 'bar'">
          <g v-for="(item, index) in normalized" :key="`bar-${item.label}-${index}`" @mouseenter="hoveredIndex = index">
            <rect
              :x="item.barX"
              :y="item.barY"
              :width="item.barWidth"
              :height="item.barHeight"
              rx="5"
              :class="['chart-bar', item.value >= 0 ? 'positive' : 'negative', { hovered: hoveredIndex === index }]"
            />
          </g>
        </template>

        <template v-else>
          <polyline :points="linePoints" class="chart-line-path" fill="none" />
          <g v-for="(item, index) in normalized" :key="`point-${item.label}-${index}`" @mouseenter="hoveredIndex = index">
            <circle :cx="item.cx" :cy="item.valueY" r="4.5" class="chart-line-point" :class="{ hovered: hoveredIndex === index }" />
          </g>
        </template>

        <g>
          <text
            v-for="item in xTicks"
            :key="`x-${item.index}`"
            :x="item.cx"
            :y="svgHeight - 8"
            text-anchor="middle"
            class="chart-axis-text"
          >{{ item.label }}</text>
        </g>
      </svg>

      <div v-if="hoveredItem" class="chart-tooltip" :style="tooltipStyle">
        <div class="tooltip-label">{{ hoveredItem.fullLabel }}</div>
        <div class="tooltip-value">{{ hoveredItem.valueLabel }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { formatNumber } from '../utils/formatters'

const props = defineProps({
  title: String,
  subtitle: String,
  points: { type: Array, default: () => [] },
  defaultMode: { type: String, default: 'bar' },
})

const mode = ref(props.defaultMode)
const hoveredIndex = ref(null)

const svgWidth = 760
const svgHeight = 290
const padLeft = 48
const padRight = 14
const padTop = 18
const padBottom = 42
const chartBottom = svgHeight - padBottom
const chartWidth = svgWidth - padLeft - padRight
const chartHeight = chartBottom - padTop

const values = computed(() => props.points.map((p) => Number(p.value || 0)))
const minValue = computed(() => Math.min(0, ...values.value))
const maxValue = computed(() => Math.max(0, ...values.value))
const span = computed(() => Math.max(1, maxValue.value - minValue.value))

function scaleY(v) {
  return padTop + ((maxValue.value - v) / span.value) * chartHeight
}

const normalized = computed(() => {
  const n = props.points.length || 1
  const step = chartWidth / n
  const barWidth = Math.max(10, Math.min(26, step * 0.56))
  return props.points.map((p, index) => {
    const value = Number(p.value || 0)
    const cx = padLeft + step * index + step / 2
    const valueY = scaleY(value)
    const zeroY = scaleY(0)
    return {
      ...p,
      fullLabel: p.fullLabel || p.label,
      value,
      cx,
      valueY,
      barX: cx - barWidth / 2,
      barY: Math.min(valueY, zeroY),
      barHeight: Math.max(2, Math.abs(zeroY - valueY)),
      barWidth,
    }
  })
})

const linePoints = computed(() => normalized.value.map((p) => `${p.cx},${p.valueY}`).join(' '))

const yTicks = computed(() => {
  const ticks = 4
  return Array.from({ length: ticks + 1 }, (_, i) => {
    const value = minValue.value + (span.value * i) / ticks
    const y = scaleY(value)
    return { value, y, label: formatNumber(value) }
  })
})

const xTicks = computed(() => {
  const total = normalized.value.length
  const maxTicks = total <= 7 ? total : total <= 14 ? 7 : 6
  const step = Math.max(1, Math.ceil(total / maxTicks))
  return normalized.value.filter((_, index) => index % step === 0 || index === total - 1).map((item) => ({
    index: item.label + String(item.cx),
    cx: item.cx,
    label: item.label,
  }))
})

const hoveredItem = computed(() => (hoveredIndex.value === null ? null : normalized.value[hoveredIndex.value]))
const tooltipStyle = computed(() => {
  if (!hoveredItem.value) return {}
  const leftPct = ((hoveredItem.value.cx / svgWidth) * 100)
  const topPct = ((hoveredItem.value.valueY / svgHeight) * 100)
  return { left: `${Math.min(86, Math.max(10, leftPct))}%`, top: `${Math.max(10, topPct - 8)}%` }
})
</script>
