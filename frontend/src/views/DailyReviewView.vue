<template>
  <div>
    <div class="dashboard-hero card compact-header-card">
      <div>
        <div class="dashboard-kicker">Trading Journal</div>
        <h1 class="dashboard-title">Review Workspace</h1>
        <p class="dashboard-subtitle">先处理待办，再完成日复盘：Summary → Trades → Daily → Positions。</p>
      </div>
    </div>

    <section class="card">
      <div class="journal-form-grid">
        <label><span>Queue Date</span><input v-model="queueDate" type="date" @change="loadQueue" /></label>
        <div class="stat-pill"><div class="stat-label">Closed Trades</div><div class="stat-value medium">{{ queue.summary.closed_trade_count || 0 }}</div></div>
        <div class="stat-pill"><div class="stat-label">Open Positions</div><div class="stat-value medium">{{ queue.summary.open_position_count || 0 }}</div></div>
        <div class="stat-pill"><div class="stat-label">Daily Review</div><div class="stat-value medium">{{ queue.summary.daily_review_completed ? 'Done' : 'Pending' }}</div></div>
        <div class="stat-pill"><div class="stat-label">Completion</div><div class="stat-value medium">{{ completionRate }}%</div></div>
        <button @click="focusFirstPending" class="secondary">Start Review</button>
      </div>
    </section>

    <section class="card" ref="tradeSectionRef">
      <div class="section-title">Trade Review Cards</div>
      <div v-if="!queue.closed_trades?.length" class="empty-row">No closed trades for this day.</div>
      <div v-for="card in queue.closed_trades" :key="card.trade_group_id" class="journal-entry-card" style="margin-bottom: 12px;">
        <div class="journal-entry-head" style="justify-content: space-between; gap: 12px;">
          <div>
            <div><strong>{{ card.symbol }}</strong> <span :class="['badge', card.realized_pnl >= 0 ? 'badge-profit' : 'badge-loss']">{{ card.realized_pnl }}</span> <span class="badge">{{ card.status }}</span></div>
            <div class="muted-copy">Hold {{ card.hold_minutes || '-' }}m · Exec {{ card.executions_count }} · Shots {{ card.screenshots_count }}</div>
            <div class="muted-copy">Setup: {{ card.setup_name || '-' }} · Grade: {{ card.grade || '-' }} · Mistakes: {{ (card.mistake_tags || []).join(', ') || '-' }}</div>
            <div class="muted-copy">Missing: {{ (card.missing_items || []).join(' / ') || 'none' }}</div>
          </div>
          <div style="min-width: 180px;">
            <div class="progress-bar"><div class="progress-fill" :style="{ width: `${card.review_completeness || 0}%` }"></div></div>
            <div class="muted-copy" style="text-align:right;">{{ card.review_completeness || 0 }}%</div>
            <button class="secondary small-btn" @click="toggleCard(card.trade_group_id)">{{ expandedCards.includes(card.trade_group_id) ? 'Close' : 'Edit Review' }}</button>
          </div>
        </div>

        <div v-if="expandedCards.includes(card.trade_group_id)" class="accordion-body">
          <div class="journal-form-grid">
            <label><span>Strategy</span><input v-model="tradeReviewForms[card.trade_group_id].strategy" /></label>
            <label><span>Setup</span>
              <select v-model="tradeReviewForms[card.trade_group_id].setup">
                <option :value="null">-</option>
                <option v-for="item in setupTags" :key="item.id" :value="item.id">{{ item.name }}</option>
              </select>
            </label>
            <label><span>Grade</span><select v-model="tradeReviewForms[card.trade_group_id].final_grade"><option value="">-</option><option>A</option><option>B</option><option>C</option><option>D</option></select></label>
            <label><span>Would take again</span><select v-model="tradeReviewForms[card.trade_group_id].would_take_again"><option value="">-</option><option value="yes">Yes</option><option value="no">No</option><option value="with_changes">With changes</option></select></label>
          </div>
          <div class="journal-form-grid">
            <label><span>Entry Q</span><input type="number" min="1" max="5" v-model.number="tradeReviewForms[card.trade_group_id].entry_quality" /></label>
            <label><span>Exit Q</span><input type="number" min="1" max="5" v-model.number="tradeReviewForms[card.trade_group_id].exit_quality" /></label>
            <label><span>Risk Q</span><input type="number" min="1" max="5" v-model.number="tradeReviewForms[card.trade_group_id].risk_management" /></label>
            <label><span>Followed plan</span><select v-model="tradeReviewForms[card.trade_group_id].followed_plan"><option :value="null">-</option><option :value="true">Yes</option><option :value="false">No</option></select></label>
          </div>
          <label><span>Thesis</span><textarea v-model="tradeReviewForms[card.trade_group_id].thesis" rows="2"></textarea></label>
          <label><span>What to improve</span><textarea v-model="tradeReviewForms[card.trade_group_id].what_to_improve" rows="2"></textarea></label>

          <div><span>Mistake Tags</span><div class="chip-wrap">
            <button v-for="tag in mistakeTags" :key="tag.id" type="button" :class="['trade-option-chip', { active: (tradeReviewForms[card.trade_group_id].mistake_tags || []).includes(tag.id) }]" @click="toggleTradeMistakeTag(card.trade_group_id, tag.id)">{{ tag.name }}</button>
          </div></div>

          <div class="filter-action-row">
            <button @click="saveCardReview(card.trade_group_id)" :disabled="savingTrade === card.trade_group_id">{{ savingTrade === card.trade_group_id ? 'Saving...' : 'Save Trade Review' }}</button>
            <router-link class="inline-link" :to="`/trades/${card.trade_group_id}`">Open Detail</router-link>
          </div>
        </div>
      </div>
    </section>

    <section class="card" ref="dailySectionRef">
      <div class="section-title">Daily Session Review</div>
      <div class="tv-panel-tabs" style="margin-bottom: 10px;">
        <button :class="['tv-subtab', { active: dailyAccordion === 'context' }]" @click="dailyAccordion='context'">Market Context</button>
        <button :class="['tv-subtab', { active: dailyAccordion === 'execution' }]" @click="dailyAccordion='execution'">Execution Summary</button>
        <button :class="['tv-subtab', { active: dailyAccordion === 'lesson' }]" @click="dailyAccordion='lesson'">Lessons & Plan</button>
        <button :class="['tv-subtab', { active: dailyAccordion === 'tags' }]" @click="dailyAccordion='tags'">Tags & Save</button>
      </div>

      <div v-if="dailyAccordion === 'context'" class="journal-form-grid">
        <label><span>Market Regime</span><input v-model="form.market_regime" /></label>
        <label><span>Daily Bias</span><input v-model="form.daily_bias" /></label>
        <label><span>Session Focus</span><select v-model="form.session"><option value="">-</option><option>open</option><option>midday</option><option>close</option><option>overnight</option></select></label>
        <label><span>Market condition</span><select v-model="form.market_condition"><option value="">-</option><option>trend</option><option>range</option><option>breakout</option><option>reversal</option><option>news</option></select></label>
      </div>

      <div v-if="dailyAccordion === 'execution'" class="journal-form-grid">
        <label><span>Strategy focus</span><input v-model="form.strategy" /></label>
        <label><span>Conviction today (1-10)</span><input type="number" min="1" max="10" v-model.number="form.confidence_score" /></label>
        <label><span>Discipline (1-10)</span><input type="number" min="1" max="10" v-model.number="form.discipline_score" /></label>
        <label><span>Emotional control (1-10)</span><input type="number" min="1" max="10" v-model.number="form.emotional_control_score" /></label>
        <label><span>Max daily loss respected</span><select v-model="maxLossSelection"><option value="">Unknown</option><option value="true">Yes</option><option value="false">No</option></select></label>
      </div>

      <div v-if="dailyAccordion === 'lesson'" class="journal-text-grid">
        <label><span>Market Summary</span><textarea v-model="form.market_summary" rows="3"></textarea></label>
        <label><span>Biggest Mistake</span><textarea v-model="form.biggest_mistake" rows="3"></textarea></label>
        <label><span>Main Lesson</span><textarea v-model="form.lessons" rows="3"></textarea></label>
        <label><span>Tomorrow Plan</span><textarea v-model="form.next_day_plan" rows="3"></textarea></label>
      </div>

      <div v-if="dailyAccordion === 'tags'">
        <div><span>Daily Mistake Tags</span><div class="chip-wrap">
          <button v-for="tag in mistakeTags" :key="tag.id" type="button" :class="['trade-option-chip', { active: (form.mistake_tags || []).includes(tag.id) }]" @click="toggleDailyMistakeTag(tag.id)">{{ tag.name }}</button>
        </div></div>
        <div class="filter-action-row">
          <button @click="saveDailyReview" :disabled="savingDaily">{{ savingDaily ? 'Saving...' : 'Save Draft' }}</button>
          <button class="secondary" @click="saveDailyReview">Mark Complete</button>
        </div>
      </div>
    </section>

    <section class="card" ref="positionSectionRef">
      <div class="section-title">Open Position Checkpoints</div>
      <div v-if="!queue.open_positions?.length" class="empty-row">No open positions.</div>
      <div v-for="item in queue.open_positions" :key="item.trade_group_id" class="journal-entry-card" style="margin-bottom:10px;">
        <div class="journal-entry-head"><div><strong>{{ item.symbol }}</strong> · Qty {{ item.open_qty }} · Avg cost {{ item.avg_open_cost || '-' }}</div><button class="secondary small-btn" @click="togglePosition(item.trade_group_id)">{{ expandedPositions.includes(item.trade_group_id) ? 'Close' : 'Checkpoint' }}</button></div>
        <div v-if="expandedPositions.includes(item.trade_group_id)" class="accordion-body">
          <div class="journal-form-grid">
            <label><span>Thesis status</span><select v-model="positionForms[item.trade_group_id].status"><option value="open">still valid</option><option value="reduced">weakened</option><option value="closed">invalid</option></select></label>
          </div>
          <label><span>Why hold overnight</span><textarea v-model="positionForms[item.trade_group_id].carry_reason" rows="2"></textarea></label>
          <label><span>Risk tomorrow</span><textarea v-model="positionForms[item.trade_group_id].gap_risk_note" rows="2"></textarea></label>
          <label><span>Next action</span><textarea v-model="positionForms[item.trade_group_id].next_session_plan" rows="2"></textarea></label>
          <div class="filter-action-row"><button @click="saveCheckpoint(item.trade_group_id)" :disabled="savingPosition === item.trade_group_id">{{ savingPosition === item.trade_group_id ? 'Saving...' : 'Save Checkpoint' }}</button></div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import {
  createDailyReview,
  fetchMistakeTags,
  fetchReviewQueue,
  fetchSetupTags,
  savePositionCheckpoint,
  saveTradeReview,
} from '../api/journal'

const queueDate = ref(new Date().toISOString().slice(0, 10))
const queue = ref({ summary: {}, closed_trades: [], open_positions: [] })
const dailyAccordion = ref('context')
const expandedCards = ref([])
const expandedPositions = ref([])
const tradeReviewForms = ref({})
const positionForms = ref({})
const setupTags = ref([])
const mistakeTags = ref([])
const savingTrade = ref(null)
const savingDaily = ref(false)
const savingPosition = ref(null)
const maxLossSelection = ref('')
const tradeSectionRef = ref(null)
const dailySectionRef = ref(null)
const positionSectionRef = ref(null)

const form = ref({ review_date: queueDate.value, strategy: '', market_regime: '', daily_bias: '', market_summary: '', biggest_mistake: '', lessons: '', next_day_plan: '', related_trade_groups: [], session: '', market_condition: '', confidence_score: null, discipline_score: null, emotional_control_score: null, max_daily_loss_respected: null, mistake_tags: [] })

const completionRate = computed(() => {
  const total = (queue.value.summary.closed_trade_count || 0) + (queue.value.summary.open_position_count || 0) + 1
  const doneTrades = (queue.value.closed_trades || []).filter((t) => (t.review_completeness || 0) >= 80).length
  const donePositions = (queue.value.open_positions || []).filter((p) => p.latest_checkpoint_id).length
  const doneDaily = queue.value.summary.daily_review_completed ? 1 : 0
  return total ? Math.round(((doneTrades + donePositions + doneDaily) / total) * 100) : 0
})

function toggleCard(id) { expandedCards.value = expandedCards.value.includes(id) ? expandedCards.value.filter((v) => v !== id) : [...expandedCards.value, id] }
function togglePosition(id) { expandedPositions.value = expandedPositions.value.includes(id) ? expandedPositions.value.filter((v) => v !== id) : [...expandedPositions.value, id] }

function toggleDailyMistakeTag(tagId) {
  const set = new Set(form.value.mistake_tags || [])
  if (set.has(tagId)) set.delete(tagId)
  else set.add(tagId)
  form.value.mistake_tags = Array.from(set)
}

function toggleTradeMistakeTag(tradeGroupId, tagId) {
  const set = new Set(tradeReviewForms.value[tradeGroupId].mistake_tags || [])
  if (set.has(tagId)) set.delete(tagId)
  else set.add(tagId)
  tradeReviewForms.value[tradeGroupId].mistake_tags = Array.from(set)
}

function hydrateCardForms(cards) {
  const next = {}
  cards.forEach((card) => {
    const review = card.trade_review || {}
    next[card.trade_group_id] = {
      trade_group: card.trade_group_id,
      strategy: review.strategy || '',
      setup: review.setup || null,
      final_grade: review.final_grade || '',
      would_take_again: review.would_take_again || '',
      thesis: review.thesis || '',
      entry_quality: review.entry_quality,
      exit_quality: review.exit_quality,
      risk_management: review.risk_management,
      followed_plan: review.followed_plan ?? null,
      what_to_improve: review.what_to_improve || '',
      mistake_tags: review.mistake_tags || [],
    }
  })
  tradeReviewForms.value = next
}

function hydratePositionForms(positions) {
  const next = {}
  positions.forEach((item) => {
    next[item.trade_group_id] = {
      trade_group: item.trade_group_id,
      review_date: queueDate.value,
      status: 'open',
      carry_reason: '',
      gap_risk_note: '',
      next_session_plan: '',
    }
  })
  positionForms.value = next
}

function hydrateDailyReview(dailyReview) {
  if (!dailyReview) {
    form.value = { review_date: queueDate.value, strategy: '', market_regime: '', daily_bias: '', market_summary: '', biggest_mistake: '', lessons: '', next_day_plan: '', related_trade_groups: queue.value.closed_trades.map((item) => item.trade_group_id), session: '', market_condition: '', confidence_score: null, discipline_score: null, emotional_control_score: null, max_daily_loss_respected: null, mistake_tags: [] }
    maxLossSelection.value = ''
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
    related_trade_groups: (dailyReview.related_trade_groups || []).length ? dailyReview.related_trade_groups : queue.value.closed_trades.map((item) => item.trade_group_id),
    session: dailyReview.session || '',
    market_condition: dailyReview.market_condition || '',
    confidence_score: dailyReview.confidence_score,
    discipline_score: dailyReview.discipline_score,
    emotional_control_score: dailyReview.emotional_control_score,
    max_daily_loss_respected: dailyReview.max_daily_loss_respected,
    mistake_tags: dailyReview.mistake_tags || [],
  }
  maxLossSelection.value = dailyReview.max_daily_loss_respected == null ? '' : String(dailyReview.max_daily_loss_respected)
}

async function loadMetaTags() {
  const [setupRes, mistakeRes] = await Promise.all([fetchSetupTags(), fetchMistakeTags()])
  setupTags.value = setupRes.data?.results || setupRes.data || []
  mistakeTags.value = mistakeRes.data?.results || mistakeRes.data || []
}

async function loadQueue() {
  const res = await fetchReviewQueue(queueDate.value)
  queue.value = res.data || { summary: {}, closed_trades: [], open_positions: [] }
  hydrateCardForms(queue.value.closed_trades || [])
  hydratePositionForms(queue.value.open_positions || [])
  hydrateDailyReview(queue.value.daily_review)
}

async function saveCardReview(tradeGroupId) {
  savingTrade.value = tradeGroupId
  try {
    await saveTradeReview({ ...tradeReviewForms.value[tradeGroupId] })
    await loadQueue()
  } finally {
    savingTrade.value = null
  }
}

async function saveCheckpoint(tradeGroupId) {
  savingPosition.value = tradeGroupId
  try {
    await savePositionCheckpoint({ ...positionForms.value[tradeGroupId] })
    await loadQueue()
  } finally {
    savingPosition.value = null
  }
}

async function saveDailyReview() {
  savingDaily.value = true
  try {
    const payload = { ...form.value, review_date: queueDate.value }
    payload.max_daily_loss_respected = maxLossSelection.value === '' ? null : maxLossSelection.value === 'true'
    await createDailyReview(payload)
    await loadQueue()
  } finally {
    savingDaily.value = false
  }
}

function focusFirstPending() {
  if ((queue.value.closed_trades || []).length) {
    tradeSectionRef.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    return
  }
  if (!queue.value.summary.daily_review_completed) {
    dailySectionRef.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    return
  }
  positionSectionRef.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

onMounted(async () => {
  await loadMetaTags()
  await loadQueue()
  nextTick(() => focusFirstPending())
})
</script>
