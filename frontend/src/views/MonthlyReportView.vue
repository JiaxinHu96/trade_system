<template>
  <div>
    <div class="page-header">
      <h1>Monthly Report</h1>
      <p>按月查看交易表现、胜率、盈亏比和当月 trade 明细。</p>
    </div>

    <div class="card toolbar compact-toolbar">
      <select v-model="selectedMonth" @change="loadReport">
        <option v-for="month in availableMonths" :key="month" :value="month">{{ month }}</option>
      </select>
      <button @click="loadReport">Refresh</button>
    </div>

    <div class="grid grid-4">
      <div class="card"><div class="stat-label">Selected Month</div><div class="stat-value medium">{{ report.selected_month || '-' }}</div></div>
      <div class="card"><div class="stat-label">Win Rate</div><div class="stat-value medium">{{ report.selected_summary?.win_rate || '-' }}%</div></div>
      <div class="card"><div class="stat-label">PnL Ratio</div><div class="stat-value medium">{{ report.selected_summary?.pnl_ratio || '-' }}</div></div>
      <div class="card"><div class="stat-label">Profit Factor</div><div class="stat-value medium">{{ report.selected_summary?.profit_factor || '-' }}</div></div>
    </div>

    <div class="grid grid-4">
      <div class="card"><div class="stat-label">Trades</div><div class="stat-value medium">{{ report.selected_summary?.trade_count || 0 }}</div></div>
      <div class="card"><div class="stat-label">Closed Trades</div><div class="stat-value medium">{{ report.selected_summary?.closed_trade_count || 0 }}</div></div>
      <div class="card"><div class="stat-label">Realized PnL</div><div class="stat-value medium">{{ report.selected_summary?.total_realized_pnl || 0 }}</div></div>
      <div class="card"><div class="stat-label">Commission</div><div class="stat-value medium">{{ report.selected_summary?.total_commission || 0 }}</div></div>
    </div>

    <div class="grid grid-2" style="margin-bottom:18px;">
      <SimpleTrendChart title="Monthly Realized PnL" :points="monthlyTrendPoints" />
      <SimpleBarChart title="Selected Month PnL by Symbol" :items="symbolBreakdownItems" />
    </div>

    <div class="card">
      <div class="section-title">Monthly Summary Table</div>
      <table class="trade-table">
        <thead>
          <tr><th>Month</th><th>Trades</th><th>Closed</th><th>Wins</th><th>Losses</th><th>Win Rate</th><th>Realized PnL</th><th>Commission</th></tr>
        </thead>
        <tbody>
          <tr v-for="item in report.month_summaries || []" :key="item.month">
            <td>{{ item.month }}</td><td>{{ item.trade_count }}</td><td>{{ item.closed_trade_count }}</td><td>{{ item.winning_trade_count }}</td><td>{{ item.losing_trade_count }}</td><td>{{ item.win_rate }}%</td><td>{{ item.total_realized_pnl }}</td><td>{{ item.total_commission }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="card">
      <div class="section-title">Selected Month Trade Groups</div>
      <TradeTable :rows="report.selected_groups || []" />
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { fetchTradeMonthlyReport } from '../api/trades'
import SimpleTrendChart from '../components/SimpleTrendChart.vue'
import SimpleBarChart from '../components/SimpleBarChart.vue'
import TradeTable from '../components/TradeTable.vue'

const report = ref({ month_summaries: [], selected_summary: {}, selected_groups: [], charts: {} })
const selectedMonth = ref('')
const availableMonths = ref([])

const monthlyTrendPoints = computed(() => (report.value.charts?.monthly_realized_pnl || []).map((item) => ({
  label: item.month.slice(2),
  value: Number(item.realized_pnl),
  valueLabel: item.realized_pnl,
})))

const symbolBreakdownItems = computed(() => (report.value.charts?.selected_symbol_breakdown || []).map((item) => ({
  label: item.symbol,
  value: Number(item.realized_pnl),
  valueLabel: item.realized_pnl,
})))

async function loadReport() {
  const params = selectedMonth.value ? { month: selectedMonth.value } : {}
  const res = await fetchTradeMonthlyReport(params)
  report.value = res.data
  availableMonths.value = res.data.available_months || []
  selectedMonth.value = res.data.selected_month || ''
}

onMounted(loadReport)
</script>
