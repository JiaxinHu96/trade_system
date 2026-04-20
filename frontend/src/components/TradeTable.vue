<template>
  <table class="trade-table tv-table">
    <thead>
      <tr>
        <th>Date</th>
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
        <td colspan="11" class="empty-row">No trades found.</td>
      </tr>
    </tbody>
  </table>
</template>

<script setup>
import { formatNumber } from '../utils/formatters'
defineProps({ rows: { type: Array, default: () => [] } })
</script>
