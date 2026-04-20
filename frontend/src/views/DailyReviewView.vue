<template>
  <div>
    <div class="dashboard-hero card compact-header-card">
      <div>
        <div class="dashboard-kicker">Trading Journal</div>
        <h1 class="dashboard-title">Journal</h1>
        <p class="dashboard-subtitle">记录当天市场观察、情绪、经验与图片，并把复盘直接关联到当天具体交易。</p>
      </div>
    </div>

    <div class="card tv-tabbed-panel">
      <div class="tv-panel-tabs">
        <button :class="['tv-subtab', { active: journalTab === 'entry' }]" @click="journalTab = 'entry'">Journal Entry</button>
        <button :class="['tv-subtab', { active: journalTab === 'timeline' }]" @click="journalTab = 'timeline'">Journal Timeline</button>
      </div>
    </div>

    <div class="journal-layout journal-layout-wide">
      <div class="card journal-form-card">
        <div v-if="journalTab !== 'entry'" class="muted-copy">切换到 “Journal Entry” 来填写当日复盘。</div>
        <template v-else>
        <div class="section-title">{{ editingId ? 'Edit Journal Entry' : 'New Journal Entry' }}</div>
        <div class="journal-form-grid">
          <label class="journal-date-field">
            <span>Date</span>
            <input ref="dateInputRef" v-model="form.review_date" type="date" @change="loadTradeOptions" @click="openDatePicker" @focus="openDatePicker" />
          </label>
        </div>

        <div class="journal-linked-trade-block">
          <div class="section-title minor">Linked Trade Group</div>
          <div class="journal-linked-trade-options">
            <button type="button" :class="['trade-option-chip', { active: form.related_trade_group === null }]" @click="form.related_trade_group = null">No linked trade</button>
            <button
              v-for="option in tradeOptions"
              :key="option.id"
              type="button"
              :class="['trade-option-chip', { active: form.related_trade_group === option.id }]"
              @click="form.related_trade_group = option.id"
            >
              <strong>{{ option.symbol }}</strong>
              <span>{{ option.status }}</span>
              <span>PnL {{ option.realized_pnl }}</span>
            </button>
          </div>
          <div v-if="!tradeOptions.length" class="muted-copy">No trade groups found for the selected day.</div>
        </div>

        <label>
          <span>Review Images</span>
          <div class="helper-row">
            <input type="file" accept="image/*" multiple @change="handleFileUpload" />
            <button type="button" class="secondary" @click="clearImages">Clear Images</button>
          </div>
        </label>

        <div v-if="form.image_urls.length" class="image-grid compact-image-grid">
          <div v-for="(url, idx) in form.image_urls" :key="url" class="image-tile">
            <img :src="url" alt="review preview" class="image-preview" />
            <button type="button" class="secondary small-btn" @click="removeImage(idx)">Remove</button>
          </div>
        </div>

        <div class="journal-text-grid">
          <label><span>Strategy</span><input v-model.trim="form.strategy" type="text" placeholder="如：开盘突破 / VWAP 回踩" /></label>
          <label><span>Market Summary</span><textarea v-model="form.market_summary" rows="4"></textarea></label>
          <label><span>Emotions</span><textarea v-model="form.emotions" rows="4"></textarea></label>
          <label><span>Thesis</span><textarea v-model="form.thesis" rows="4"></textarea></label>
          <label><span>Entry Logic</span><textarea v-model="form.entry_logic" rows="4"></textarea></label>
          <label><span>Exit Logic</span><textarea v-model="form.exit_logic" rows="4"></textarea></label>
          <label><span>Lessons</span><textarea v-model="form.lessons" rows="4"></textarea></label>
          <label><span>Next Day Plan</span><textarea v-model="form.next_day_plan" rows="4"></textarea></label>
        </div>
        <div class="filter-action-row">
          <button @click="submitReview" :disabled="loading || uploading">{{ savingLabel }}</button>
          <button v-if="editingId" class="secondary" @click="cancelEdit">Cancel</button>
        </div>
        </template>
      </div>

      <div class="card journal-list-card">
        <div v-if="journalTab !== 'timeline'" class="muted-copy">切换到 “Journal Timeline” 查看与筛选历史日记。</div>
        <template v-else>
        <div class="journal-list-head">
          <div class="section-title">Journal Timeline</div>
          <div class="journal-list-filters">
            <input v-model="listDateFilter" type="date" @change="loadReviews(1)" />
            <input v-model.trim="listStrategyFilter" type="text" placeholder="Filter by strategy" @keyup.enter="loadReviews(1)" />
            <button class="secondary small-btn" @click="loadReviews(1)">Search</button>
          </div>
        </div>

        <div v-for="item in reviews" :key="item.id" class="journal-entry-card accordion">
          <button class="journal-entry-head accordion-trigger" @click="toggleReview(item.id)">
            <div>
              <div class="review-date">{{ item.review_date }}</div>
              <div v-if="item.related_trade_group_display" class="review-linked-trade">
                {{ item.related_trade_group_display.symbol }} · {{ item.related_trade_group_display.trade_date }} · {{ item.related_trade_group_display.status }}
              </div>
            </div>
            <span class="accordion-indicator">{{ expandedReviewIds.includes(item.id) ? '−' : '+' }}</span>
          </button>

          <div v-if="expandedReviewIds.includes(item.id)" class="accordion-body">
            <div class="journal-entry-grid">
              <div><strong>Strategy</strong><p>{{ item.strategy || '-' }}</p></div>
              <div><strong>Market</strong><p>{{ item.market_summary || '-' }}</p></div>
              <div><strong>Emotions</strong><p>{{ item.emotions || '-' }}</p></div>
              <div><strong>Thesis</strong><p>{{ item.thesis || '-' }}</p></div>
              <div><strong>Entry Logic</strong><p>{{ item.entry_logic || '-' }}</p></div>
              <div><strong>Exit Logic</strong><p>{{ item.exit_logic || '-' }}</p></div>
              <div><strong>Lessons</strong><p>{{ item.lessons || '-' }}</p></div>
              <div><strong>Next Day</strong><p>{{ item.next_day_plan || '-' }}</p></div>
            </div>
            <div class="journal-inline-actions">
              <button class="secondary small-btn" @click="editReview(item)">Edit</button>
              <button class="secondary small-btn" @click="removeReview(item.id)">Delete</button>
              <router-link v-if="item.related_trade_group_display" class="inline-link" :to="`/trades/${item.related_trade_group_display.id}`">Open linked trade</router-link>
            </div>
            <div v-if="item.images?.length" class="image-grid compact-image-grid">
              <a v-for="img in item.images" :key="img.id" :href="img.image_url" target="_blank" class="image-link-card">
                <img :src="img.image_url" alt="review image" class="image-preview" />
              </a>
            </div>
          </div>
        </div>
        <div v-if="!reviews.length" class="empty-row">No journal entries yet.</div>
        <PaginationControls :count="totalCount" :current-page="page" :page-size="20" @change="loadReviews" />
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { createDailyReview, updateDailyReview, deleteDailyReview, fetchDailyReviews, fetchDailyReviewTradeOptions, uploadDailyReviewImages } from '../api/journal'
import PaginationControls from '../components/PaginationControls.vue'

const JOURNAL_EXPANDED_KEY = 'journal-expanded-v100'
const loading = ref(false)
const uploading = ref(false)
const reviews = ref([])
const tradeOptions = ref([])
const page = ref(1)
const totalCount = ref(0)
const listDateFilter = ref('')
const listStrategyFilter = ref('')
const expandedReviewIds = ref([])
const editingId = ref(null)
const journalTab = ref('entry')
const dateInputRef = ref(null)
const freshForm = () => ({
  review_date: new Date().toISOString().slice(0, 10),
  related_trade_group: null,
  image_urls: [],
  strategy: '',
  market_summary: '',
  emotions: '',
  thesis: '',
  entry_logic: '',
  exit_logic: '',
  lessons: '',
  next_day_plan: '',
})
const form = ref(freshForm())
const savingLabel = computed(() => {
  if (loading.value) return editingId.value ? 'Updating...' : 'Saving...'
  if (uploading.value) return 'Uploading...'
  return editingId.value ? 'Update Journal' : 'Save Journal'
})

function openDatePicker() {
  const dateInput = dateInputRef.value
  if (dateInput && typeof dateInput.showPicker === 'function') dateInput.showPicker()
}

function restoreExpandedState() {
  try { expandedReviewIds.value = JSON.parse(localStorage.getItem(JOURNAL_EXPANDED_KEY) || '[]') } catch { expandedReviewIds.value = [] }
}
function persistExpandedState() { localStorage.setItem(JOURNAL_EXPANDED_KEY, JSON.stringify(expandedReviewIds.value)) }

async function loadReviews(nextPage = 1) {
  page.value = nextPage
  const params = { page: page.value }
  if (listDateFilter.value) params.date = listDateFilter.value
  if (listStrategyFilter.value) params.strategy = listStrategyFilter.value
  const res = await fetchDailyReviews(params)
  reviews.value = res.data.results || []
  totalCount.value = res.data.count || reviews.value.length
}
async function loadTradeOptions() {
  if (!form.value.review_date) return
  const res = await fetchDailyReviewTradeOptions(form.value.review_date)
  tradeOptions.value = res.data || []
  const ids = new Set(tradeOptions.value.map(item => item.id))
  if (form.value.related_trade_group !== null && !ids.has(form.value.related_trade_group)) form.value.related_trade_group = null
}
async function handleFileUpload(event) {
  const files = event.target.files
  if (!files?.length) return
  uploading.value = true
  try {
    const res = await uploadDailyReviewImages(files)
    const urls = res.data.image_urls || (res.data.image_url ? [res.data.image_url] : [])
    form.value.image_urls = [...form.value.image_urls, ...urls]
  } finally {
    uploading.value = false
    event.target.value = ''
  }
}
function clearImages() { form.value.image_urls = [] }
function removeImage(idx) { form.value.image_urls.splice(idx, 1) }
function toggleReview(id) {
  const set = new Set(expandedReviewIds.value)
  if (set.has(id)) set.delete(id)
  else set.add(id)
  expandedReviewIds.value = Array.from(set)
  persistExpandedState()
}
function editReview(item) {
  editingId.value = item.id
  form.value = {
    review_date: item.review_date,
    related_trade_group: item.related_trade_group ?? null,
    image_urls: (item.images || []).map(img => img.image_url),
    market_summary: item.market_summary || '',
    emotions: item.emotions || '',
    strategy: item.strategy || '',
    thesis: item.thesis || '',
    entry_logic: item.entry_logic || '',
    exit_logic: item.exit_logic || '',
    lessons: item.lessons || '',
    next_day_plan: item.next_day_plan || '',
  }
  journalTab.value = 'entry'
  loadTradeOptions()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}
function cancelEdit() {
  editingId.value = null
  form.value = freshForm()
  loadTradeOptions()
}

async function removeReview(id) {
  if (!window.confirm('Delete this journal entry?')) return
  await deleteDailyReview(id)
  if (editingId.value === id) cancelEdit()
  await loadReviews(page.value)
}
async function submitReview() {
  loading.value = true
  try {
    if (editingId.value) await updateDailyReview(editingId.value, form.value)
    else await createDailyReview(form.value)
    const selectedDate = form.value.review_date
    cancelEdit()
    listDateFilter.value = selectedDate
    await loadReviews(1)
  } catch (err) {
    alert(err?.response?.data?.detail || 'Save failed')
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  restoreExpandedState()
  await loadTradeOptions()
  await loadReviews(1)
})
</script>
