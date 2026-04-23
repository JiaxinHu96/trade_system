<template>
  <div>
    <div class="dashboard-hero card compact-header-card">
      <div>
        <div class="dashboard-kicker">Trading Journal</div>
        <h1 class="dashboard-title">Review Queue</h1>
        <p class="dashboard-subtitle">自动待复盘：已平仓卡片 + 持仓checkpoint + 当日日复盘总表。</p>
      </div>
    </div>

    <section class="card">
      <div class="journal-form-grid">
        <label><span>Queue Date</span><input v-model="queueDate" type="date" @change="loadQueue" /></label>
        <div><span class="stat-label">Closed trades</span><div class="stat-value medium">{{ queue.summary.closed_trade_count || 0 }}</div></div>
        <div><span class="stat-label">Open positions</span><div class="stat-value medium">{{ queue.summary.open_position_count || 0 }}</div></div>
        <div><span class="stat-label">Daily review</span><div class="stat-value medium">{{ queue.summary.daily_review_completed ? 'Done' : 'Pending' }}</div></div>
      </div>
    </section>

    <section class="card journal-form-card">
      <div class="section-title">Daily Session Review（总表）</div>
      <div class="journal-form-grid">
        <label><span>Market Regime</span><input v-model="form.market_regime" /></label>
        <label><span>Daily Bias</span><input v-model="form.daily_bias" /></label>
        <label><span>Strategy</span><input v-model="form.strategy" /></label>
        <label><span>Session</span><select v-model="form.session"><option value="">-</option><option>open</option><option>midday</option><option>close</option><option>overnight</option></select></label>
        <label><span>Market condition</span><select v-model="form.market_condition"><option value="">-</option><option>trend</option><option>range</option><option>breakout</option><option>reversal</option><option>news</option></select></label>
        <label><span>Confidence (1-10)</span><input v-model.number="form.confidence_score" type="number" min="1" max="10" /></label>
        <label><span>Rule followed</span><select v-model="ruleFollowedSelection"><option value="">Unknown</option><option value="true">Yes</option><option value="false">No</option></select></label>
        <label><span>Trade grade</span><select v-model="form.trade_quality_grade"><option value="">-</option><option>A+</option><option>A</option><option>B</option><option>C</option></select></label>
        <label><span>Would take again</span><select v-model="wouldTakeAgainSelection"><option value="">Unknown</option><option value="true">Yes</option><option value="false">No</option></select></label>
      </div>
      <div class="journal-text-grid">
        <label><span>Market Summary</span><textarea v-model="form.market_summary" rows="3"></textarea></label>
        <label><span>Biggest Mistake</span><textarea v-model="form.biggest_mistake" rows="3"></textarea></label>
        <label><span>Main Lesson</span><textarea v-model="form.lessons" rows="3"></textarea></label>
        <label><span>Tomorrow Plan</span><textarea v-model="form.next_day_plan" rows="3"></textarea></label>
        <label><span>Mistake tags (comma IDs)</span><input v-model="dailyMistakeInput" placeholder="1,2" /></label>
      </div>
      <div class="filter-action-row"><button @click="saveDailyReview" :disabled="savingDaily">{{ savingDaily ? 'Saving...' : 'Save Daily Review' }}</button></div>
    </section>

    <section class="card">
      <div class="section-title">Trade Review Cards（单笔复盘）</div>
      <div v-if="!queue.closed_trades?.length" class="empty-row">No closed trades for this day.</div>
      <div v-for="card in queue.closed_trades" :key="card.trade_group_id" class="journal-entry-card" style="margin-bottom:12px;">
        <div class="journal-entry-head">
          <div>
            <strong>{{ card.symbol }}</strong>
            <div class="muted-copy">PnL {{ card.realized_pnl }} · Hold {{ card.hold_minutes || '-' }}m · {{ card.status }}</div>
            <div class="muted-copy">Execs {{ card.executions_count }} · Screenshots {{ card.screenshots_count }} · 完整度 {{ card.review_completeness }}%</div>
          </div>
          <button class="secondary small-btn" @click="toggleCard(card.trade_group_id)">{{ expandedCards.includes(card.trade_group_id) ? '收起' : '复盘' }}</button>
        </div>

        <div v-if="expandedCards.includes(card.trade_group_id)" class="accordion-body">
          <div class="journal-form-grid">
            <label><span>Setup ID</span><input v-model.number="tradeReviewForms[card.trade_group_id].setup" type="number" min="1" /></label>
            <label><span>Entry quality</span><input v-model.number="tradeReviewForms[card.trade_group_id].entry_quality" type="number" min="1" max="5" /></label>
            <label><span>Exit quality</span><input v-model.number="tradeReviewForms[card.trade_group_id].exit_quality" type="number" min="1" max="5" /></label>
            <label><span>Final grade</span><select v-model="tradeReviewForms[card.trade_group_id].final_grade"><option value="">-</option><option>A</option><option>B</option><option>C</option><option>D</option></select></label>
          </div>
          <label><span>Thesis</span><textarea v-model="tradeReviewForms[card.trade_group_id].thesis" rows="2"></textarea></label>
          <label><span>Mistake tags (comma IDs)</span><input v-model="mistakeInputs[card.trade_group_id]" placeholder="1,2" /></label>
          <label><span>What to improve</span><textarea v-model="tradeReviewForms[card.trade_group_id].what_to_improve" rows="2"></textarea></label>
          <div class="filter-action-row">
            <button @click="saveCardReview(card.trade_group_id)" :disabled="savingTrade === card.trade_group_id">{{ savingTrade === card.trade_group_id ? 'Saving...' : 'Save Trade Review' }}</button>
            <router-link class="inline-link" :to="`/trades/${card.trade_group_id}`">Open Detail</router-link>
          </div>
        </div>
      </div>
    </section>

    <section class="card">
      <div class="section-title">Open Positions（checkpoint 待写）</div>
      <div v-if="!queue.open_positions?.length" class="empty-row">No open positions.</div>
      <div v-for="item in queue.open_positions" :key="item.trade_group_id" class="review-item">
        <strong>{{ item.symbol }}</strong> · Open Qty {{ item.open_qty }} · Latest checkpoint: {{ item.latest_checkpoint_date || 'none' }}
      </div>
    </section>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { createDailyReview, fetchReviewQueue, saveTradeReview } from '../api/journal'

const queueDate = ref(new Date().toISOString().slice(0, 10))
const queue = ref({ summary: {}, closed_trades: [], open_positions: [] })
const expandedCards = ref([])
const tradeReviewForms = ref({})
const mistakeInputs = ref({})
const savingTrade = ref(null)
const savingDaily = ref(false)
const ruleFollowedSelection = ref('')
const wouldTakeAgainSelection = ref('')
const dailyMistakeInput = ref('')

const form = ref({
  review_date: queueDate.value,
  strategy: '',
  market_regime: '',
  daily_bias: '',
  market_summary: '',
  biggest_mistake: '',
  lessons: '',
  next_day_plan: '',
  related_trade_groups: [],
  session: '',
  market_condition: '',
  confidence_score: null,
  rule_followed: null,
  trade_quality_grade: '',
  would_take_again: null,
  mistake_tags: [],
})

function toggleCard(id) {
  expandedCards.value = expandedCards.value.includes(id)
    ? expandedCards.value.filter((v) => v !== id)
    : [...expandedCards.value, id]
}

function hydrateCardForms(cards) {
  const next = {}
  const mistakes = {}
  cards.forEach((card) => {
    const review = card.trade_review || {}
    next[card.trade_group_id] = {
      trade_group: card.trade_group_id,
      setup: review.setup || null,
      thesis: review.thesis || '',
      entry_quality: review.entry_quality,
      exit_quality: review.exit_quality,
      what_to_improve: review.what_to_improve || '',
      final_grade: review.final_grade || '',
      mistake_tags: review.mistake_tags || [],
    }
    mistakes[card.trade_group_id] = (review.mistake_tags || []).join(',')
  })
  tradeReviewForms.value = next
  mistakeInputs.value = mistakes
}

function hydrateDailyReview(dailyReview) {
  if (!dailyReview) {
    form.value = {
      review_date: queueDate.value,
      strategy: '',
      market_regime: '',
      daily_bias: '',
      market_summary: '',
      biggest_mistake: '',
      lessons: '',
      next_day_plan: '',
      related_trade_groups: queue.value.closed_trades.map((item) => item.trade_group_id),
      session: '',
      market_condition: '',
      confidence_score: null,
      rule_followed: null,
      trade_quality_grade: '',
      would_take_again: null,
      mistake_tags: [],
    }
    ruleFollowedSelection.value = ''
    wouldTakeAgainSelection.value = ''
    dailyMistakeInput.value = ''
    return
  }

  form.value = {
    review_date: queueDate.value,
    strategy: dailyReview.strategy || '',
    market_regime: dailyReview.market_regime || '',
    daily_bias: dailyReview.daily_bias || '',
    market_summary: dailyReview.market_summary || '',
    biggest_mistake: dailyReview.biggest_mistake || '',
    lessons: dailyReview.lessons || '',
    next_day_plan: dailyReview.next_day_plan || '',
    related_trade_groups: (dailyReview.related_trade_groups || []).length
      ? dailyReview.related_trade_groups
      : queue.value.closed_trades.map((item) => item.trade_group_id),
    session: dailyReview.session || '',
    market_condition: dailyReview.market_condition || '',
    confidence_score: dailyReview.confidence_score,
    rule_followed: dailyReview.rule_followed ?? null,
    trade_quality_grade: dailyReview.trade_quality_grade || '',
    would_take_again: dailyReview.would_take_again ?? null,
    mistake_tags: dailyReview.mistake_tags || [],
  }
  ruleFollowedSelection.value = dailyReview.rule_followed == null ? '' : String(dailyReview.rule_followed)
  wouldTakeAgainSelection.value = dailyReview.would_take_again == null ? '' : String(dailyReview.would_take_again)
  dailyMistakeInput.value = (dailyReview.mistake_tags || []).join(',')
}

async function loadQueue() {
  const res = await fetchReviewQueue(queueDate.value)
  queue.value = res.data || { summary: {}, closed_trades: [], open_positions: [] }
  hydrateCardForms(queue.value.closed_trades || [])
  hydrateDailyReview(queue.value.daily_review)
}

async function saveCardReview(tradeGroupId) {
  savingTrade.value = tradeGroupId
  try {
    const payload = { ...tradeReviewForms.value[tradeGroupId] }
    payload.mistake_tags = (mistakeInputs.value[tradeGroupId] || '')
      .split(',')
      .map((item) => Number(item.trim()))
      .filter(Boolean)
    await saveTradeReview(payload)
    await loadQueue()
  } finally {
    savingTrade.value = null
  }
}

async function saveDailyReview() {
  savingDaily.value = true
  try {
    const payload = { ...form.value, review_date: queueDate.value }
    payload.rule_followed = ruleFollowedSelection.value === '' ? null : ruleFollowedSelection.value === 'true'
    payload.would_take_again = wouldTakeAgainSelection.value === '' ? null : wouldTakeAgainSelection.value === 'true'
    payload.mistake_tags = (dailyMistakeInput.value || '')
      .split(',')
      .map((item) => Number(item.trim()))
      .filter(Boolean)
    await createDailyReview(payload)
    await loadQueue()
  } finally {
    savingDaily.value = false
  }
}

onMounted(loadQueue)
</script>
