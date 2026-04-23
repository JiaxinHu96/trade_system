<template>
  <div>
    <div class="dashboard-hero card compact-header-card">
      <div>
        <div class="dashboard-kicker">Trading Journal</div>
        <h1 class="dashboard-title">Review Workspace</h1>
        <p class="dashboard-subtitle">先处理待办，再完成日复盘：Summary → Trades → Daily → Positions。</p>
      </div>
    </div>

    <section class="card tv-tabbed-panel tv-tabbed-panel-compact">
      <div class="tv-panel-tabs">
        <button :class="['tv-subtab', { active: journalTab === 'workspace' }]" @click="journalTab='workspace'">Review Workspace</button>
        <button :class="['tv-subtab', { active: journalTab === 'timeline' }]" @click="openTimelineTab">Journal Timeline</button>
      </div>
    </section>

    <template v-if="journalTab === 'workspace'">
    <section class="card">
      <div class="journal-form-grid workspace-summary-grid">
        <label><span>Queue Date</span><input v-model="queueDate" type="date" @change="loadQueue" @click="openDatePicker" @focus="openDatePicker" /></label>
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
      <div class="trade-card-grid">
        <div v-for="card in queue.closed_trades" :key="card.trade_group_id" class="journal-entry-card trade-review-card">
          <div class="trade-review-head">
            <div>
              <div><strong>{{ card.symbol }}</strong> <span :class="['badge', card.realized_pnl >= 0 ? 'badge-profit' : 'badge-loss']">{{ card.realized_pnl }}</span> <span class="badge">{{ card.status }}</span></div>
              <div class="muted-copy">Hold {{ card.hold_minutes || '-' }}m · Exec {{ card.executions_count }} · Shots {{ card.screenshots_count }}</div>
              <div class="muted-copy">Setup: {{ card.setup_name || '-' }} · Grade: {{ card.grade || '-' }} · Mistakes: {{ (card.mistake_tags || []).join(', ') || '-' }}</div>
              <div class="muted-copy">Missing: {{ (card.missing_items || []).join(' / ') || 'none' }}</div>
            </div>
            <div class="trade-review-progress">
              <div class="progress-bar"><div class="progress-fill" :style="{ width: `${card.review_completeness || 0}%` }"></div></div>
              <div class="muted-copy trade-review-percent">{{ card.review_completeness || 0 }}%</div>
            </div>
          </div>
          <div class="trade-review-actions">
            <button class="secondary small-btn" @click="toggleCard(card.trade_group_id)">
              {{ expandedCards.includes(card.trade_group_id) ? 'Close' : 'Edit Review' }}
            </button>
          </div>

          <div v-if="expandedCards.includes(card.trade_group_id)" class="accordion-body compact-trade-body">
            <div class="journal-form-grid trade-review-form-grid">
              <label><span>Strategy</span><input v-model="tradeReviewForms[card.trade_group_id].strategy" /></label>
              <label><span>Setup</span>
                <select v-model="tradeReviewForms[card.trade_group_id].setup">
                  <option :value="null">-</option>
                  <option v-for="item in setupTags" :key="item.id" :value="item.id">{{ item.name }}</option>
                </select>
              </label>
              <label><span>Grade</span><select v-model="tradeReviewForms[card.trade_group_id].final_grade"><option value="">-</option><option>A</option><option>B</option><option>C</option><option>D</option></select></label>
              <label><span>Would take again</span><select v-model="tradeReviewForms[card.trade_group_id].would_take_again"><option value="">-</option><option value="yes">Yes</option><option value="no">No</option><option value="with_changes">With changes</option></select></label>
              <label><span>Entry Q</span><input type="number" min="1" max="5" v-model.number="tradeReviewForms[card.trade_group_id].entry_quality" /></label>
              <label><span>Exit Q</span><input type="number" min="1" max="5" v-model.number="tradeReviewForms[card.trade_group_id].exit_quality" /></label>
              <label><span>Risk Q</span><input type="number" min="1" max="5" v-model.number="tradeReviewForms[card.trade_group_id].risk_management" /></label>
              <label><span>Followed plan</span><select v-model="tradeReviewForms[card.trade_group_id].followed_plan"><option :value="null">-</option><option :value="true">Yes</option><option :value="false">No</option></select></label>
            </div>
            <div class="trade-review-text-grid">
              <label><span>Thesis</span><textarea v-model="tradeReviewForms[card.trade_group_id].thesis" rows="2"></textarea></label>
              <label><span>What to improve</span><textarea v-model="tradeReviewForms[card.trade_group_id].what_to_improve" rows="2"></textarea></label>
            </div>

            <div><span>Mistake Tags</span><div class="chip-wrap">
              <button v-for="tag in mistakeTags" :key="tag.id" type="button" :class="['trade-option-chip', { active: (tradeReviewForms[card.trade_group_id].mistake_tags || []).includes(tag.id) }]" @click="toggleTradeMistakeTag(card.trade_group_id, tag.id)">{{ tag.name }}</button>
            </div></div>

            <label>
              <span>Screenshots</span>
              <div class="helper-row">
                <input type="file" accept="image/*" multiple @change="uploadTradeScreenshots(card.trade_group_id, $event)" />
                <span class="muted-copy" v-if="uploadingTrade === card.trade_group_id">Uploading...</span>
              </div>
            </label>
            <div v-if="(tradeReviewForms[card.trade_group_id].screenshots || []).length" class="image-grid compact-image-grid">
              <div v-for="(url, idx) in tradeReviewForms[card.trade_group_id].screenshots" :key="`${url}-${idx}`" class="image-tile">
                <img :src="url" alt="trade screenshot" class="image-preview" />
                <button type="button" class="secondary small-btn" @click="removeTradeScreenshot(card.trade_group_id, idx)">Remove</button>
              </div>
            </div>

            <div class="filter-action-row">
              <button @click="saveCardReview(card.trade_group_id)" :disabled="savingTrade === card.trade_group_id">{{ savingTrade === card.trade_group_id ? 'Saving...' : 'Save Trade Review' }}</button>
              <router-link class="inline-link" :to="`/trades/${card.trade_group_id}`">Open Detail</router-link>
            </div>
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

      <div v-if="dailyAccordion === 'context'" class="journal-form-grid workspace-field-grid">
        <label><span>Market Regime</span><input v-model="form.market_regime" /></label>
        <label><span>Daily Bias</span><input v-model="form.daily_bias" /></label>
        <label><span>Session Focus</span><select v-model="form.session"><option value="">-</option><option>open</option><option>midday</option><option>close</option><option>overnight</option></select></label>
        <label><span>Market condition</span><select v-model="form.market_condition"><option value="">-</option><option>trend</option><option>range</option><option>breakout</option><option>reversal</option><option>news</option></select></label>
      </div>

      <div v-if="dailyAccordion === 'execution'" class="journal-form-grid workspace-field-grid">
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
        <label>
          <span>Daily Session Screenshots</span>
          <div class="helper-row">
            <input type="file" accept="image/*" multiple @change="uploadDailyScreenshots" />
            <span class="muted-copy" v-if="uploadingDailyImage">Uploading...</span>
          </div>
        </label>
        <div v-if="form.image_urls?.length" class="image-grid compact-image-grid">
          <div v-for="(url, idx) in form.image_urls" :key="`${url}-${idx}`" class="image-tile">
            <img :src="url" alt="daily screenshot" class="image-preview" />
            <button type="button" class="secondary small-btn" @click="removeDailyScreenshot(idx)">Remove</button>
          </div>
        </div>
        <div class="filter-action-row">
          <button @click="saveDailyReview('draft')" :disabled="savingDaily">{{ savingDaily ? 'Saving...' : 'Save Draft' }}</button>
          <button class="secondary" @click="saveDailyReview('completed')" :disabled="savingDaily">Mark Complete</button>
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
    </template>

    <section v-else class="card">
      <div class="section-title">Journal Timeline</div>
      <div class="journal-form-grid timeline-filter-grid">
        <label><span>Date From</span><input v-model="timelineDateFrom" type="date" @change="loadTimeline" @click="openDatePicker" @focus="openDatePicker" /></label>
        <label><span>Date To</span><input v-model="timelineDateTo" type="date" @change="loadTimeline" @click="openDatePicker" @focus="openDatePicker" /></label>
        <button class="secondary" @click="loadTimeline">Refresh</button>
      </div>
      <div v-if="!dailyTimeline.length" class="empty-row">No daily reviews yet.</div>
      <div v-for="item in dailyTimeline" :key="item.id" class="review-item">
        <strong>{{ item.review_date }}</strong> · {{ item.market_regime || '-' }} / {{ item.daily_bias || '-' }} · {{ item.market_summary || '-' }} · Trades {{ (item.related_trade_groups_display || []).map((t) => t.symbol).join(', ') || '-' }}
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import {
  createDailyReview,
  fetchDailyReviews,
  fetchMistakeTags,
  fetchReviewQueue,
  fetchSetupTags,
  savePositionCheckpoint,
  saveTradeReview,
  uploadDailyReviewImages,
} from '../api/journal'

const queueDate = ref(new Date().toISOString().slice(0, 10))
const journalTab = ref('workspace')
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
const uploadingTrade = ref(null)
const uploadingDailyImage = ref(false)
const maxLossSelection = ref('')
const tradeSectionRef = ref(null)
const dailySectionRef = ref(null)
const positionSectionRef = ref(null)
const dailyTimeline = ref([])
const timelineDateFrom = ref('')
const timelineDateTo = ref('')

const form = ref({ review_date: queueDate.value, review_status: 'draft', strategy: '', market_regime: '', daily_bias: '', market_summary: '', biggest_mistake: '', lessons: '', next_day_plan: '', related_trade_groups: [], session: '', market_condition: '', confidence_score: null, discipline_score: null, emotional_control_score: null, max_daily_loss_respected: null, mistake_tags: [], image_urls: [] })

const completionRate = computed(() => {
  const total = (queue.value.summary.closed_trade_count || 0) + (queue.value.summary.open_position_count || 0) + 1
  const doneTrades = (queue.value.closed_trades || []).filter((t) => (t.review_completeness || 0) >= 80).length
  const donePositions = (queue.value.open_positions || []).filter((p) => p.latest_checkpoint_id).length
  const doneDaily = queue.value.summary.daily_review_completed ? 1 : 0
  return total ? Math.round(((doneTrades + donePositions + doneDaily) / total) * 100) : 0
})

function toggleCard(id) { expandedCards.value = expandedCards.value.includes(id) ? expandedCards.value.filter((v) => v !== id) : [...expandedCards.value, id] }
function togglePosition(id) { expandedPositions.value = expandedPositions.value.includes(id) ? expandedPositions.value.filter((v) => v !== id) : [...expandedPositions.value, id] }
function openDatePicker(event) {
  const dateInput = event?.target
  if (dateInput && typeof dateInput.showPicker === 'function') dateInput.showPicker()
}

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
      screenshots: review.screenshots || [],
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
    form.value = { review_date: queueDate.value, review_status: 'draft', strategy: '', market_regime: '', daily_bias: '', market_summary: '', biggest_mistake: '', lessons: '', next_day_plan: '', related_trade_groups: queue.value.closed_trades.map((item) => item.trade_group_id), session: '', market_condition: '', confidence_score: null, discipline_score: null, emotional_control_score: null, max_daily_loss_respected: null, mistake_tags: [], image_urls: [] }
    maxLossSelection.value = ''
    return
  }
  form.value = {
    review_date: queueDate.value,
    review_status: dailyReview.review_status || 'draft',
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
    image_urls: (dailyReview.images || []).map((item) => item.image_url),
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

async function loadTimeline() {
  const params = { page_size: 20 }
  if (timelineDateFrom.value) params.date_from = timelineDateFrom.value
  if (timelineDateTo.value) params.date_to = timelineDateTo.value
  const timelineRes = await fetchDailyReviews(params)
  dailyTimeline.value = timelineRes.data?.results || []
}

async function openTimelineTab() {
  journalTab.value = 'timeline'
  if (!dailyTimeline.value.length) await loadTimeline()
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

async function uploadTradeScreenshots(tradeGroupId, event) {
  const files = event?.target?.files
  if (!files?.length) return
  uploadingTrade.value = tradeGroupId
  try {
    const res = await uploadDailyReviewImages(files)
    const urls = res.data?.image_urls || (res.data?.image_url ? [res.data.image_url] : [])
    const prev = tradeReviewForms.value[tradeGroupId].screenshots || []
    tradeReviewForms.value[tradeGroupId].screenshots = [...prev, ...urls]
  } finally {
    uploadingTrade.value = null
    if (event?.target) event.target.value = ''
  }
}

function removeTradeScreenshot(tradeGroupId, index) {
  const arr = [...(tradeReviewForms.value[tradeGroupId].screenshots || [])]
  arr.splice(index, 1)
  tradeReviewForms.value[tradeGroupId].screenshots = arr
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

async function uploadDailyScreenshots(event) {
  const files = event?.target?.files
  if (!files?.length) return
  uploadingDailyImage.value = true
  try {
    const res = await uploadDailyReviewImages(files)
    const urls = res.data?.image_urls || (res.data?.image_url ? [res.data.image_url] : [])
    form.value.image_urls = [...(form.value.image_urls || []), ...urls]
  } finally {
    uploadingDailyImage.value = false
    if (event?.target) event.target.value = ''
  }
}

function removeDailyScreenshot(index) {
  const arr = [...(form.value.image_urls || [])]
  arr.splice(index, 1)
  form.value.image_urls = arr
}

async function saveDailyReview(mode = 'draft') {
  savingDaily.value = true
  try {
    const payload = { ...form.value, review_date: queueDate.value }
    payload.review_status = mode
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
  await loadTimeline()
  nextTick(() => focusFirstPending())
})
</script>

<style scoped>
.workspace-summary-grid {
  grid-template-columns: repeat(auto-fit, minmax(180px, 220px));
  gap: 10px 14px;
  align-items: end;
}

.trade-card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
  gap: 12px;
}

.trade-review-card {
  margin-bottom: 0;
  padding: 14px;
}

.trade-review-head {
  display: flex;
  justify-content: space-between;
  gap: 10px;
}

.trade-review-progress {
  min-width: 72px;
  display: grid;
  gap: 4px;
  align-content: start;
}

.trade-review-percent {
  text-align: right;
}

.trade-review-actions {
  margin-top: 8px;
}

.compact-trade-body {
  padding-top: 10px;
}

.trade-review-form-grid {
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 8px 10px;
  margin-bottom: 10px;
}

.trade-review-text-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 8px 10px;
}

.workspace-field-grid {
  grid-template-columns: repeat(auto-fit, minmax(220px, 320px));
  gap: 10px 16px;
}

.workspace-field-grid label,
.workspace-summary-grid label {
  gap: 6px;
}

.workspace-field-grid :deep(input),
.workspace-field-grid :deep(select),
.workspace-summary-grid :deep(input),
.timeline-filter-grid :deep(input),
.trade-review-form-grid :deep(input),
.trade-review-form-grid :deep(select),
.trade-review-text-grid :deep(textarea) {
  padding: 8px 10px;
}

.trade-review-text-grid :deep(textarea) {
  min-height: 72px;
}

.timeline-filter-grid {
  grid-template-columns: repeat(auto-fit, minmax(200px, 260px));
  gap: 10px 12px;
  align-items: end;
}

@media (max-width: 900px) {
  .trade-card-grid,
  .workspace-summary-grid,
  .workspace-field-grid,
  .timeline-filter-grid {
    grid-template-columns: 1fr;
  }
}
</style>
