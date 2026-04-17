<template>
  <div class="tv-chart-card">
    <div class="tv-chart-head">
      <div>
        <div class="tv-chart-title">{{ title }}</div>
        <div v-if="subtitle" class="tv-chart-subtitle">{{ subtitle }}</div>
      </div>
      <div class="tv-chart-controls">
        <div v-if="showLegend" class="tv-chart-legend">
          <span v-for="serie in normalizedSeries" :key="serie.name" class="tv-legend-item">
            <span class="tv-legend-dot" :style="{ backgroundColor: serie.color }"></span>
            {{ serie.name }}
          </span>
        </div>
        <div class="tv-chart-action-row">
          <button
            v-if="allowSwitch"
            :class="['tv-mode-chip', { active: mode === 'bar' }]"
            @click="mode = 'bar'"
          >Bar</button>
          <button
            v-if="allowSwitch"
            :class="['tv-mode-chip', { active: mode === 'line' }]"
            @click="mode = 'line'"
          >Line</button>
          <button class="tv-icon-chip" @click="modalOpen = true" title="Expand chart">⤢</button>
        </div>
      </div>
    </div>

    <div v-if="!categories.length || !normalizedSeries.length" class="empty-row">No chart data.</div>

    <div v-else ref="wrapRef" class="tv-chart-wrap" :style="chartWrapStyle">
      <svg
        :viewBox="`0 0 ${svgWidth} ${svgHeight}`"
        class="tv-chart-svg"
        preserveAspectRatio="none"
        :style="{ width: `${svgWidth}px`, minWidth: `${svgWidth}px` }"
      >
        <g>
          <line
            v-for="tick in yTicks"
            :key="`grid-${tick.value}`"
            :x1="padLeft"
            :x2="svgWidth - padRight"
            :y1="tick.y"
            :y2="tick.y"
            class="tv-grid-line"
          />
          <line :x1="padLeft" :x2="padLeft" :y1="padTop" :y2="svgHeight - padBottom" class="tv-axis-line" />
          <line :x1="padLeft" :x2="svgWidth - padRight" :y1="zeroY" :y2="zeroY" class="tv-axis-line" />
          <text
            v-for="tick in yTicks"
            :key="`label-${tick.value}`"
            :x="padLeft - 8"
            :y="tick.y + 4"
            text-anchor="end"
            class="tv-axis-label"
          >{{ tick.label }}</text>

          <rect
            v-if="hoveredIndex !== null"
            :x="overlayRect(hoveredIndex).x"
            :y="padTop"
            :width="overlayRect(hoveredIndex).width"
            :height="chartBottom - padTop"
            class="tv-hover-band"
          />

          <template v-if="mode === 'bar'">
            <g v-for="(cat, catIndex) in categories" :key="`bar-group-${cat}`">
              <rect
                v-for="(serie, sIndex) in normalizedSeries"
                :key="`${serie.name}-${catIndex}`"
                :x="barRect(catIndex, sIndex).x"
                :y="barRect(catIndex, sIndex).y"
                :width="barRect(catIndex, sIndex).width"
                :height="barRect(catIndex, sIndex).height"
                :fill="serie.color"
                :class="['tv-bar', { active: hoveredIndex === catIndex }]"
              />
            </g>
          </template>

          <template v-else>
            <g v-for="serie in normalizedSeries" :key="`line-${serie.name}`">
              <path :d="linePath(serie.data)" :stroke="serie.color" class="tv-line-path" fill="none" />
              <circle
                v-for="(point, idx) in serie.data"
                :key="`${serie.name}-pt-${idx}`"
                :cx="xForIndex(idx)"
                :cy="yForValue(point)"
                r="4"
                :fill="serie.color"
                :class="['tv-line-point', { active: hoveredIndex === idx }]"
              />
            </g>
          </template>

          <g>
            <rect
              v-for="(cat, catIndex) in categories"
              :key="`overlay-${catIndex}`"
              :x="overlayRect(catIndex).x"
              :y="padTop"
              :width="overlayRect(catIndex).width"
              :height="chartBottom - padTop"
              class="tv-hover-overlay"
              @mousemove="showTooltip($event, catIndex)"
              @mouseenter="showTooltip($event, catIndex)"
              @mouseleave="hideTooltip"
            />
          </g>

          <text
            v-for="idx in visibleCategoryIndices"
            :key="`x-${idx}`"
            :x="xForIndex(idx)"
            :y="svgHeight - padBottom + 18"
            text-anchor="middle"
            class="tv-axis-label"
          >{{ categories[idx] }}</text>
        </g>
      </svg>

      <div
        v-if="tooltip.visible"
        class="tv-chart-tooltip"
        :style="{ left: `${tooltip.x}px`, top: `${tooltip.y}px` }"
      >
        <div class="tv-tooltip-title">{{ tooltip.category }}</div>
        <div v-for="item in tooltip.items" :key="item.name" class="tv-tooltip-row">
          <span class="tv-tooltip-dot" :style="{ backgroundColor: item.color }"></span>
          <span class="tv-tooltip-series">{{ item.name }}</span>
          <strong class="tv-tooltip-value">{{ formatNumber(item.value) }}</strong>
        </div>
      </div>
    </div>

    <div v-if="modalOpen" class="tv-chart-modal" @click.self="modalOpen = false">
      <div class="tv-chart-modal-card">
        <div class="tv-chart-modal-header">
          <div>
            <div class="tv-chart-title">{{ title }}</div>
            <div v-if="subtitle" class="tv-chart-subtitle">{{ subtitle }}</div>
          </div>
          <div class="tv-chart-action-row">
            <button
              v-if="allowSwitch"
              :class="['tv-mode-chip', { active: mode === 'bar' }]"
              @click="mode = 'bar'"
            >Bar</button>
            <button
              v-if="allowSwitch"
              :class="['tv-mode-chip', { active: mode === 'line' }]"
              @click="mode = 'line'"
            >Line</button>
            <button class="tv-icon-chip" @click="modalOpen = false" title="Close">✕</button>
          </div>
        </div>

        <div ref="modalWrapRef" class="tv-chart-wrap tv-chart-wrap-modal" :style="modalChartWrapStyle">
          <svg
            :viewBox="`0 0 ${modalSvgWidth} ${modalSvgHeight}`"
            class="tv-chart-svg"
            preserveAspectRatio="none"
            :style="{ width: `${modalSvgWidth}px`, minWidth: `${modalSvgWidth}px` }"
          >
            <g>
              <line
                v-for="tick in modalYTicks"
                :key="`m-grid-${tick.value}`"
                :x1="padLeft"
                :x2="modalSvgWidth - padRight"
                :y1="tick.y"
                :y2="tick.y"
                class="tv-grid-line"
              />
              <line :x1="padLeft" :x2="padLeft" :y1="padTop" :y2="modalSvgHeight - padBottom" class="tv-axis-line" />
              <line :x1="padLeft" :x2="modalSvgWidth - padRight" :y1="modalZeroY" :y2="modalZeroY" class="tv-axis-line" />
              <text
                v-for="tick in modalYTicks"
                :key="`m-label-${tick.value}`"
                :x="padLeft - 8"
                :y="tick.y + 4"
                text-anchor="end"
                class="tv-axis-label"
              >{{ tick.label }}</text>

              <rect
                v-if="hoveredIndex !== null"
                :x="modalOverlayRect(hoveredIndex).x"
                :y="padTop"
                :width="modalOverlayRect(hoveredIndex).width"
                :height="modalChartBottom - padTop"
                class="tv-hover-band"
              />

              <template v-if="mode === 'bar'">
                <g v-for="(cat, catIndex) in categories" :key="`m-bar-group-${cat}`">
                  <rect
                    v-for="(serie, sIndex) in normalizedSeries"
                    :key="`m-${serie.name}-${catIndex}`"
                    :x="modalBarRect(catIndex, sIndex).x"
                    :y="modalBarRect(catIndex, sIndex).y"
                    :width="modalBarRect(catIndex, sIndex).width"
                    :height="modalBarRect(catIndex, sIndex).height"
                    :fill="serie.color"
                    :class="['tv-bar', { active: hoveredIndex === catIndex }]"
                  />
                </g>
              </template>

              <template v-else>
                <g v-for="serie in normalizedSeries" :key="`m-line-${serie.name}`">
                  <path :d="modalLinePath(serie.data)" :stroke="serie.color" class="tv-line-path" fill="none" />
                  <circle
                    v-for="(point, idx) in serie.data"
                    :key="`m-${serie.name}-pt-${idx}`"
                    :cx="modalXForIndex(idx)"
                    :cy="modalYForValue(point)"
                    r="4.5"
                    :fill="serie.color"
                    :class="['tv-line-point', { active: hoveredIndex === idx }]"
                  />
                </g>
              </template>

              <rect
                v-for="(cat, catIndex) in categories"
                :key="`m-overlay-${catIndex}`"
                :x="modalOverlayRect(catIndex).x"
                :y="padTop"
                :width="modalOverlayRect(catIndex).width"
                :height="modalChartBottom - padTop"
                class="tv-hover-overlay"
                @mousemove="showTooltip($event, catIndex, true)"
                @mouseenter="showTooltip($event, catIndex, true)"
                @mouseleave="hideTooltip"
              />

              <text
                v-for="idx in modalVisibleCategoryIndices"
                :key="`m-x-${idx}`"
                :x="modalXForIndex(idx)"
                :y="modalSvgHeight - padBottom + 20"
                text-anchor="middle"
                class="tv-axis-label"
              >{{ categories[idx] }}</text>
            </g>
          </svg>

          <div
            v-if="tooltip.visible && tooltip.modal"
            class="tv-chart-tooltip"
            :style="{ left: `${tooltip.x}px`, top: `${tooltip.y}px` }"
          >
            <div class="tv-tooltip-title">{{ tooltip.category }}</div>
            <div v-for="item in tooltip.items" :key="item.name" class="tv-tooltip-row">
              <span class="tv-tooltip-dot" :style="{ backgroundColor: item.color }"></span>
              <span class="tv-tooltip-series">{{ item.name }}</span>
              <strong class="tv-tooltip-value">{{ formatNumber(item.value) }}</strong>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { formatNumber } from '../utils/formatters.js'

const props = defineProps({
  title: String,
  subtitle: String,
  categories: { type: Array, default: () => [] },
  series: { type: Array, default: () => [] },
  defaultType: { type: String, default: 'bar' },
  height: { type: Number, default: 250 },
  allowSwitch: { type: Boolean, default: true },
  showLegend: { type: Boolean, default: true },
})

const mode = ref(props.defaultType)
const modalOpen = ref(false)
watch(() => props.defaultType, v => { mode.value = v })

const wrapRef = ref(null)
const modalWrapRef = ref(null)
const width = ref(640)
const modalWidth = ref(1100)
let ro = null
let modalRo = null

const padLeft = 48
const padRight = 18
const padTop = 18
const padBottom = 38

const svgHeight = computed(() => props.height)
const modalSvgHeight = computed(() => 420)
const normalizedSeries = computed(() => props.series.map((s, idx) => ({
  name: s.name || `Series ${idx + 1}`,
  color: s.color || ['#22c55e', '#ef4444', '#2563eb', '#f59e0b'][idx % 4],
  data: (s.data || []).map(v => Number(v || 0)),
})))

const minPixelsPerCategory = computed(() => {
  const seriesCount = Math.max(normalizedSeries.value.length, 1)
  if (mode.value === 'bar') return Math.max(22, 12 * seriesCount + 10)
  return 26
})

const minChartPixelWidth = computed(() => {
  const categoryCount = Math.max(props.categories.length, 1)
  return padLeft + padRight + (categoryCount * minPixelsPerCategory.value)
})

const minModalChartPixelWidth = computed(() => {
  const categoryCount = Math.max(props.categories.length, 1)
  return padLeft + padRight + (categoryCount * (minPixelsPerCategory.value + 6))
})

const svgWidth = computed(() => Math.max(width.value, 320, minChartPixelWidth.value))
const innerWidth = computed(() => svgWidth.value - padLeft - padRight)
const innerHeight = computed(() => svgHeight.value - padTop - padBottom)
const chartBottom = computed(() => svgHeight.value - padBottom)

const modalSvgWidth = computed(() => Math.max(modalWidth.value, 820, minModalChartPixelWidth.value))
const modalInnerWidth = computed(() => modalSvgWidth.value - padLeft - padRight)
const modalInnerHeight = computed(() => modalSvgHeight.value - padTop - padBottom)
const modalChartBottom = computed(() => modalSvgHeight.value - padBottom)

const chartWrapStyle = computed(() => ({
  height: `${svgHeight.value}px`,
  minHeight: `${svgHeight.value}px`,
  overflowX: svgWidth.value > width.value ? 'auto' : 'hidden',
  overflowY: 'hidden',
}))

const modalChartWrapStyle = computed(() => ({
  height: `${modalSvgHeight.value}px`,
  minHeight: `${modalSvgHeight.value}px`,
  overflowX: modalSvgWidth.value > modalWidth.value ? 'auto' : 'hidden',
  overflowY: 'hidden',
}))

const allValues = computed(() => normalizedSeries.value.flatMap(s => s.data))
const minValue = computed(() => Math.min(0, ...allValues.value, 0))
const maxValue = computed(() => Math.max(0, ...allValues.value, 1))
const rangeValue = computed(() => {
  const raw = maxValue.value - minValue.value
  return raw === 0 ? 1 : raw
})

function yForValueWith(v, h) {
  return padTop + ((maxValue.value - Number(v)) / rangeValue.value) * h
}
function xForIndexWith(idx, w) {
  if (props.categories.length <= 1) return padLeft + w / 2
  return padLeft + (idx / (props.categories.length - 1)) * w
}
function groupWidthWith(w) {
  return w / Math.max(props.categories.length, 1)
}
function overlayRectWith(catIndex, w) {
  const band = groupWidthWith(w)
  return { x: padLeft + (catIndex * band), width: Math.max(band, 12) }
}
function barRectWith(catIndex, seriesIndex, w, h, zeroYValue) {
  const groupWidth = groupWidthWith(w)
  const usable = Math.max(16, groupWidth * 0.74)
  const single = usable / Math.max(normalizedSeries.value.length, 1)
  const x = padLeft + (catIndex * groupWidth) + ((groupWidth - usable) / 2) + (seriesIndex * single)
  const value = normalizedSeries.value[seriesIndex].data[catIndex] || 0
  const y = Math.min(yForValueWith(value, h), zeroYValue)
  const height = Math.max(2, Math.abs(yForValueWith(value, h) - zeroYValue))
  return { x, y, width: Math.max(7, single - 3), height }
}
function linePathWith(data, w, h) {
  return data.map((v, idx) => `${idx === 0 ? 'M' : 'L'} ${xForIndexWith(idx, w)} ${yForValueWith(v, h)}`).join(' ')
}
function visibleIndicesWith(w) {
  const slots = Math.max(2, Math.floor(w / 74))
  const step = Math.max(1, Math.ceil(props.categories.length / slots))
  const indices = []
  for (let i = 0; i < props.categories.length; i += step) indices.push(i)
  if (props.categories.length > 1 && indices[indices.length - 1] !== props.categories.length - 1) {
    indices.push(props.categories.length - 1)
  }
  return indices
}
function yTicksWith(h) {
  const count = 4
  const ticks = []
  for (let i = 0; i <= count; i += 1) {
    const value = minValue.value + (rangeValue.value * i / count)
    ticks.push({ value, y: yForValueWith(value, h), label: formatNumber(value) })
  }
  return ticks.reverse()
}

const zeroY = computed(() => yForValueWith(0, innerHeight.value))
const modalZeroY = computed(() => yForValueWith(0, modalInnerHeight.value))
const yTicks = computed(() => yTicksWith(innerHeight.value))
const modalYTicks = computed(() => yTicksWith(modalInnerHeight.value))

function xForIndex(idx) { return xForIndexWith(idx, innerWidth.value) }
function modalXForIndex(idx) { return xForIndexWith(idx, modalInnerWidth.value) }
function yForValue(v) { return yForValueWith(v, innerHeight.value) }
function modalYForValue(v) { return yForValueWith(v, modalInnerHeight.value) }
function barRect(catIndex, seriesIndex) { return barRectWith(catIndex, seriesIndex, innerWidth.value, innerHeight.value, zeroY.value) }
function modalBarRect(catIndex, seriesIndex) { return barRectWith(catIndex, seriesIndex, modalInnerWidth.value, modalInnerHeight.value, modalZeroY.value) }
function linePath(data) { return linePathWith(data, innerWidth.value, innerHeight.value) }
function modalLinePath(data) { return linePathWith(data, modalInnerWidth.value, modalInnerHeight.value) }
function overlayRect(catIndex) { return overlayRectWith(catIndex, innerWidth.value) }
function modalOverlayRect(catIndex) { return overlayRectWith(catIndex, modalInnerWidth.value) }

const visibleCategoryIndices = computed(() => visibleIndicesWith(innerWidth.value))
const modalVisibleCategoryIndices = computed(() => visibleIndicesWith(modalInnerWidth.value))

const hoveredIndex = ref(null)
const tooltip = ref({ visible: false, x: 0, y: 0, category: '', items: [], modal: false })

function showTooltip(event, categoryIndex, isModal = false) {
  const targetWrap = isModal ? modalWrapRef.value : wrapRef.value
  const rect = targetWrap?.getBoundingClientRect()
  if (!rect) return
  hoveredIndex.value = categoryIndex
  tooltip.value = {
    visible: true,
    modal: isModal,
    x: event.clientX - rect.left + 12,
    y: event.clientY - rect.top - 10,
    category: props.categories[categoryIndex],
    items: normalizedSeries.value.map((serie) => ({
      name: serie.name,
      color: serie.color,
      value: serie.data[categoryIndex] ?? 0,
    })),
  }
}
function hideTooltip() {
  tooltip.value.visible = false
  hoveredIndex.value = null
}

function syncWidths() {
  if (wrapRef.value) {
    width.value = Math.max(wrapRef.value.clientWidth || 0, 320)
  }
  if (modalWrapRef.value) {
    modalWidth.value = Math.max(modalWrapRef.value.clientWidth || 0, 820)
  }
}

function scheduleWidthSync() {
  nextTick(() => {
    syncWidths()
    requestAnimationFrame(() => syncWidths())
    setTimeout(() => syncWidths(), 60)
    setTimeout(() => syncWidths(), 180)
  })
}

function attachResize() {
  syncWidths()
  if (wrapRef.value) {
    ro = new ResizeObserver((entries) => {
      width.value = Math.max(entries[0].contentRect.width || 0, 320)
    })
    ro.observe(wrapRef.value)
  }
}
function attachModalResize() {
  syncWidths()
  if (modalWrapRef.value) {
    modalRo = new ResizeObserver((entries) => {
      modalWidth.value = Math.max(entries[0].contentRect.width || 0, 820)
    })
    modalRo.observe(modalWrapRef.value)
  }
}
watch(modalOpen, (open) => {
  if (open) {
    setTimeout(() => attachModalResize(), 20)
  } else if (modalRo) {
    modalRo.disconnect()
    modalRo = null
    tooltip.value.visible = false
  }
})

watch(
  () => [props.categories.length, normalizedSeries.value.length, mode.value],
  () => {
    scheduleWidthSync()
  },
  { flush: 'post' }
)

onMounted(() => {
  attachResize()
  window.addEventListener('resize', syncWidths)
  scheduleWidthSync()
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', syncWidths)
  if (ro) ro.disconnect()
  if (modalRo) modalRo.disconnect()
})
</script>
