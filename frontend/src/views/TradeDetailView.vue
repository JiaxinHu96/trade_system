<template>
  <div>
    <div class="page-header detail-header-row">
      <div>
        <h1>Trade Detail</h1>
        <p>查看某一笔 trade group 的聚合结果、原始 executions、fills 和关联复盘。</p>
      </div>
      <button class="secondary" @click="goBack">← Back</button>
    </div>

    <div v-if="loading" class="card">Loading...</div>
    <div v-else-if="notFound" class="card">
      <div class="section-title">Trade not found</div>
      <p class="muted-copy">当前记录可能在重建分组后已变更。请返回列表重新选择。</p>
    </div>
    <template v-else-if="trade">
      <div class="grid grid-4">
        <div class="card"><div class="stat-label">Symbol</div><div class="stat-value medium">{{ trade.symbol }}</div></div>
        <div class="card"><div class="stat-label">Date</div><div class="stat-value medium">{{ trade.trade_date }}</div></div>
        <div class="card"><div class="stat-label">Status</div><div class="stat-value medium">{{ trade.status }}</div></div>
        <div class="card"><div class="stat-label">Realized PnL</div><div class="stat-value medium">{{ fmt(trade.realized_pnl) }}</div></div>
      </div>

      <div class="grid grid-2">
        <div class="card">
          <div class="section-title">Trade Summary</div>
          <table class="kv-table">
            <tbody>
              <tr><td>Direction</td><td>{{ trade.direction || '-' }}</td></tr>
              <tr><td>Asset Class</td><td>{{ trade.asset_class || '-' }}</td></tr>
              <tr><td>Buy Qty</td><td>{{ fmt(trade.total_buy_qty) }}</td></tr>
              <tr><td>Sell Qty</td><td>{{ fmt(trade.total_sell_qty) }}</td></tr>
              <tr><td>Open Qty</td><td>{{ fmt(trade.open_qty) }}</td></tr>
              <tr><td>Avg Buy Price</td><td>{{ fmt(trade.avg_buy_price) }}</td></tr>
              <tr><td>Avg Sell Price</td><td>{{ fmt(trade.avg_sell_price) }}</td></tr>
              <tr><td>Avg Open Cost</td><td>{{ fmt(trade.avg_open_cost) }}</td></tr>
              <tr><td>Commission</td><td>{{ fmt(trade.commission_total) }}</td></tr>
            </tbody>
          </table>
        </div>
        <div class="card">
          <div class="section-title">Linked Daily Reviews</div>
          <div v-if="trade.linked_daily_reviews?.length">
            <div v-for="review in trade.linked_daily_reviews" :key="review.id" class="review-item">
              <div class="review-date">{{ review.review_date }}</div>
              <p>{{ review.market_summary || '-' }}</p>
            </div>
          </div>
          <div v-else class="empty-row">No linked daily reviews.</div>
        </div>
      </div>

      <div class="card">
        <div class="section-title">Raw Executions</div>
        <table class="trade-table">
          <thead>
            <tr>
              <th>Time</th><th>Exec ID</th><th>Side</th><th>Qty</th><th>Price</th><th>Commission</th><th>Exchange</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in trade.raw_executions" :key="item.id">
              <td>{{ item.executed_at }}</td><td>{{ item.execution_id }}</td><td>{{ item.side }}</td><td>{{ fmt(item.quantity) }}</td><td>{{ fmt(item.price) }}</td><td>{{ fmt(item.commission) }}</td><td>{{ item.exchange }}</td>
            </tr>
            <tr v-if="!trade.raw_executions?.length"><td colspan="7" class="empty-row">No executions.</td></tr>
          </tbody>
        </table>
      </div>

      <div class="card">
        <div class="section-title">Trade Fills</div>
        <table class="trade-table">
          <thead>
            <tr><th>Time</th><th>Side</th><th>Qty</th><th>Price</th><th>Signed Qty</th><th>Commission</th></tr>
          </thead>
          <tbody>
            <tr v-for="item in trade.fills" :key="item.id">
              <td>{{ item.executed_at }}</td><td>{{ item.side }}</td><td>{{ fmt(item.quantity) }}</td><td>{{ fmt(item.price) }}</td><td>{{ fmt(item.signed_qty) }}</td><td>{{ fmt(item.commission) }}</td>
            </tr>
            <tr v-if="!trade.fills?.length"><td colspan="6" class="empty-row">No fills.</td></tr>
          </tbody>
        </table>
      </div>
    </template>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { fetchTradeGroupDetail, fetchTradeGroups } from '../api/trades'
import { formatNumber } from '../utils/formatters'

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const trade = ref(null)
const notFound = ref(false)
const fmt = (v) => formatNumber(v)

async function loadTrade() {
  loading.value = true
  notFound.value = false
  try {
    const res = await fetchTradeGroupDetail(route.params.id)
    trade.value = res.data
  } catch (err) {
    if (err?.response?.status === 404) {
      const fallbackSymbol = route.query?.symbol
      const fallbackDate = route.query?.date
      if (fallbackSymbol && fallbackDate) {
        const fallbackRes = await fetchTradeGroups({ symbol: fallbackSymbol, date: fallbackDate, page_size: 1 })
        trade.value = fallbackRes.data?.results?.[0] || null
      }
      notFound.value = !trade.value
      return
    }
    throw err
  } finally {
    loading.value = false
  }
}

function goBack() {
  if (window.history.length > 1) router.back()
  else router.push('/trades')
}

onMounted(loadTrade)
</script>
