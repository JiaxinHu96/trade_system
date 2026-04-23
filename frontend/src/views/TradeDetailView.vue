<template>
  <div>
    <div class="page-header detail-header-row">
      <div>
        <h1>Trade Detail</h1>
        <p>成交明细 + 就地复盘面板（结构化字段）。</p>
      </div>
      <button class="secondary" @click="goBack">← Back</button>
    </div>

    <div v-if="loading" class="card">Loading...</div>
    <template v-else-if="trade">
      <div class="grid grid-2">
        <div class="card">
          <div class="section-title">Trade Summary</div>
          <table class="kv-table"><tbody>
            <tr><td>Symbol</td><td>{{ trade.symbol }}</td></tr>
            <tr><td>Status</td><td>{{ trade.status }}</td></tr>
            <tr><td>Direction</td><td>{{ trade.direction || '-' }}</td></tr>
            <tr><td>Realized PnL</td><td>{{ fmt(trade.realized_pnl) }}</td></tr>
            <tr><td>Commission</td><td>{{ fmt(trade.commission_total) }}</td></tr>
          </tbody></table>
        </div>

        <div class="card">
          <div class="section-title">Trade Review (on-page)</div>
          <div class="journal-form-grid">
            <label><span>Strategy</span><input v-model="reviewForm.strategy" /></label>
            <label><span>Session</span><select v-model="reviewForm.session"><option value="">-</option><option>open</option><option>midday</option><option>close</option><option>overnight</option></select></label>
            <label><span>Final Grade</span><select v-model="reviewForm.final_grade"><option value="">-</option><option>A</option><option>B</option><option>C</option><option>D</option></select></label>
            <label><span>Realized R</span><input v-model="reviewForm.realized_r" type="number" step="0.01" /></label>
          </div>
          <div class="journal-form-grid">
            <label><span>Entry quality (1-5)</span><input v-model.number="reviewForm.entry_quality" type="number" min="1" max="5" /></label>
            <label><span>Exit quality (1-5)</span><input v-model.number="reviewForm.exit_quality" type="number" min="1" max="5" /></label>
            <label><span>Risk mgmt (1-5)</span><input v-model.number="reviewForm.risk_management" type="number" min="1" max="5" /></label>
            <label><span>Followed plan?</span><select v-model="followedPlanSelection"><option value="">Unknown</option><option value="true">Yes</option><option value="false">No</option></select></label>
          </div>
          <label><span>Thesis</span><textarea v-model="reviewForm.thesis" rows="2"></textarea></label>
          <label><span>Entry trigger</span><textarea v-model="reviewForm.entry_trigger" rows="2"></textarea></label>
          <label><span>Invalidation / Stop</span><textarea v-model="reviewForm.invalidation" rows="2"></textarea></label>
          <label><span>Planned target</span><textarea v-model="reviewForm.planned_target" rows="2"></textarea></label>
          <label><span>What I did well</span><textarea v-model="reviewForm.what_i_did_well" rows="2"></textarea></label>
          <label><span>What to improve</span><textarea v-model="reviewForm.what_to_improve" rows="2"></textarea></label>
          <div class="filter-action-row"><button @click="saveReview" :disabled="saving">{{ saving ? 'Saving...' : 'Save Trade Review' }}</button></div>
        </div>
      </div>

      <div class="card">
        <div class="section-title">Raw Executions</div>
        <table class="trade-table">
          <thead><tr><th>Time</th><th>Side</th><th>Qty</th><th>Price</th></tr></thead>
          <tbody>
            <tr v-for="item in trade.raw_executions" :key="item.id"><td>{{ item.executed_at }}</td><td>{{ item.side }}</td><td>{{ fmt(item.quantity) }}</td><td>{{ fmt(item.price) }}</td></tr>
            <tr v-if="!trade.raw_executions?.length"><td colspan="4" class="empty-row">No executions.</td></tr>
          </tbody>
        </table>
      </div>
    </template>
  </div>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { fetchTradeGroupDetail } from '../api/trades'
import { saveTradeReview } from '../api/journal'
import { formatNumber } from '../utils/formatters'

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const saving = ref(false)
const trade = ref(null)
const fmt = (v) => formatNumber(v)
const reviewForm = ref({ trade_group: null, strategy: '', session: '', thesis: '', entry_trigger: '', invalidation: '', planned_target: '', entry_quality: null, exit_quality: null, risk_management: null, followed_plan: null, what_i_did_well: '', what_to_improve: '', realized_r: null, final_grade: '' })
const followedPlanSelection = ref('')

watch(followedPlanSelection, (value) => { reviewForm.value.followed_plan = value === '' ? null : value === 'true' })

function populateReviewForm() {
  const source = trade.value?.trade_review
  reviewForm.value.trade_group = trade.value?.id
  if (!source) return
  Object.assign(reviewForm.value, source)
  followedPlanSelection.value = source.followed_plan == null ? '' : String(source.followed_plan)
}

async function loadTrade() {
  loading.value = true
  try {
    const res = await fetchTradeGroupDetail(route.params.id)
    trade.value = res.data
    populateReviewForm()
  } finally {
    loading.value = false
  }
}

async function saveReview() {
  saving.value = true
  try {
    await saveTradeReview(reviewForm.value)
    await loadTrade()
  } finally {
    saving.value = false
  }
}

function goBack() { if (window.history.length > 1) router.back(); else router.push('/trades') }
onMounted(loadTrade)
</script>
