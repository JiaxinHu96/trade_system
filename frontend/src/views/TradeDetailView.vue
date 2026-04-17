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
        <div class="section-title">Trade Journal (Editable)</div>
        <div class="journal-text-grid">
          <label><span>Thesis</span><textarea v-model="journal.thesis" rows="3"></textarea></label>
          <label><span>Execution Notes</span><textarea v-model="journal.execution_notes" rows="3"></textarea></label>
          <label><span>Exit Notes</span><textarea v-model="journal.exit_notes" rows="3"></textarea></label>
          <label><span>Rating (1-10)</span><input v-model.number="journal.rating" type="number" min="1" max="10" /></label>
        </div>
        <div class="filter-action-row">
          <button @click="saveJournal" :disabled="journalSaving">{{ journalSaving ? 'Saving...' : 'Save Journal' }}</button>
        </div>

        <div v-if="journalImageUrl" class="image-grid compact-image-grid" style="margin-top: 12px">
          <a :href="journalImageUrl" target="_blank" class="image-link-card">
            <img :src="journalImageUrl" alt="auto trade snapshot" class="image-preview" />
          </a>
        </div>
        <div v-else class="muted-copy">No auto snapshot yet. Run sync to generate a chart image with buy/sell markers.</div>
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
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { fetchTradeGroupDetail } from '../api/trades'
import { fetchTradeJournalByTradeGroup, saveTradeJournal } from '../api/journal'
import { formatNumber } from '../utils/formatters'

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const trade = ref(null)
const journalId = ref(null)
const journalSaving = ref(false)
const journal = ref({ thesis: '', execution_notes: '', exit_notes: '', rating: null, tv_snapshot_url: '' })
const fmt = (v) => formatNumber(v)
const journalImageUrl = computed(() => {
  if (!journal.value.tv_snapshot_url) return ''
  const value = journal.value.tv_snapshot_url
  if (value.startsWith('http://') || value.startsWith('https://')) return value
  return `${import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'}${value}`
})

async function loadJournal() {
  const res = await fetchTradeJournalByTradeGroup(route.params.id)
  const existing = res.data.results?.[0]
  if (!existing) {
    journalId.value = null
    journal.value = { thesis: '', execution_notes: '', exit_notes: '', rating: null, tv_snapshot_url: '' }
    return
  }
  journalId.value = existing.id
  journal.value = {
    thesis: existing.thesis || '',
    execution_notes: existing.execution_notes || '',
    exit_notes: existing.exit_notes || '',
    rating: existing.rating,
    tv_snapshot_url: existing.tv_snapshot_url || '',
  }
}

async function loadTrade() {
  loading.value = true
  try {
    const res = await fetchTradeGroupDetail(route.params.id)
    trade.value = res.data
    await loadJournal()
  } finally {
    loading.value = false
  }
}

async function saveJournalEntry() {
  journalSaving.value = true
  try {
    const payload = {
      trade_group: Number(route.params.id),
      thesis: journal.value.thesis,
      execution_notes: journal.value.execution_notes,
      exit_notes: journal.value.exit_notes,
      rating: journal.value.rating,
    }
    const res = await saveTradeJournal(payload)
    journalId.value = res.data.id
    journal.value.tv_snapshot_url = res.data.tv_snapshot_url || journal.value.tv_snapshot_url
  } finally {
    journalSaving.value = false
  }
}

function saveJournal() {
  saveJournalEntry().catch((err) => {
    alert(err?.response?.data?.detail || 'Save failed')
  })
}

function goBack() {
  if (window.history.length > 1) router.back()
  else router.push('/trades')
}

onMounted(loadTrade)
</script>
