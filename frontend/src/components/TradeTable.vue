<template>
  <table class="trade-table tv-table">
    <thead>
      <tr>
        <th>Date</th>
        <th>Open Time</th>
        <th>Close Time</th>
        <th>Hold</th>
        <th>Symbol</th>
        <th>Status</th>
        <th>Direction</th>
        <th>Buy Qty</th>
        <th>Sell Qty</th>
        <th>Open Qty</th>
        <th>Avg Open Cost</th>
        <th>Realized PnL</th>
        <th>Commission</th>
        <th>Action</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="row in rows" :key="row.id">
        <td>{{ row.trade_date }}</td>
        <td>{{ formatDateTime(row.opened_at) }}</td>
        <td>{{ formatDateTime(row.closed_at) }}</td>
        <td>{{ formatHold(row.opened_at, row.closed_at) }}</td>
        <td>{{ row.symbol }}</td>
        <td><span :class="['badge', row.status]">{{ row.status }}</span></td>
        <td>{{ row.direction || '-' }}</td>
        <td>{{ formatNumber(row.total_buy_qty) }}</td>
        <td>{{ formatNumber(row.total_sell_qty) }}</td>
        <td>{{ formatNumber(row.open_qty) }}</td>
        <td>{{ row.avg_open_cost ? formatNumber(row.avg_open_cost) : '-' }}</td>
        <td>{{ formatNumber(row.realized_pnl) }}</td>
        <td>{{ formatNumber(row.commission_total) }}</td>
        <td>
          <router-link
            class="inline-link"
            :to="{ path: `/trades/${row.id}`, query: { symbol: row.symbol, date: row.trade_date } }"
          >
            Detail
          </router-link>
        </td>
      </tr>
      <tr v-if="!rows.length">
        <td colspan="14" class="empty-row">No trades found.</td>
      </tr>
    </tbody>
  </table>
</template>

<script setup>
import { formatNumber } from '../utils/formatters'
defineProps({ rows: { type: Array, default: () => [] } })

function formatDateTime(value) {
  if (!value) return '-'
  const dt = new Date(value)
  if (Number.isNaN(dt.getTime())) return '-'
  return dt.toLocaleString('sv-SE', { hour12: false }).replace(' ', ' ')
}

function formatHold(openedAt, closedAt) {
  if (!openedAt || !closedAt) return '-'
  const start = new Date(openedAt)
  const end = new Date(closedAt)
  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) return '-'
  const diffMs = end.getTime() - start.getTime()
  if (diffMs < 0) return '-'
  const totalMinutes = Math.floor(diffMs / 60000)
  const days = Math.floor(totalMinutes / 1440)
  const hours = Math.floor((totalMinutes % 1440) / 60)
  const minutes = totalMinutes % 60
  if (days > 0) return `${days}d ${hours}h ${minutes}m`
  if (hours > 0) return `${hours}h ${minutes}m`
  return `${minutes}m`
}
</script>
