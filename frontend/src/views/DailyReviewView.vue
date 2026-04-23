<template>
  <div>
    <div class="dashboard-hero card compact-header-card">
      <div>
        <div class="dashboard-kicker">Trading Journal</div>
        <h1 class="dashboard-title">Journal</h1>
        <p class="dashboard-subtitle">升级为三层复盘：日内总复盘 + 多笔 Trade Reviews + 持仓 checkpoint。</p>
      </div>
    </div>

    <div class="journal-layout journal-layout-wide journal-shell">
      <section class="card journal-form-card journal-surface">
        <div class="section-title">{{ editingId ? 'Edit Daily Review' : 'New Daily Review' }}</div>
        <div class="journal-form-grid">
          <label class="journal-date-field"><span>Date</span><input ref="dateInputRef" v-model="form.review_date" type="date" @change="loadTradeOptions" /></label>
          <label><span>Market Regime</span><input v-model="form.market_regime" placeholder="trend / range / breakout" /></label>
          <label><span>Daily Bias</span><input v-model="form.daily_bias" placeholder="bullish / neutral / bearish" /></label>
        </div>

        <div class="journal-linked-trade-block">
          <div class="section-title minor">Linked Trade Groups (multi-select)</div>
          <div class="journal-linked-trade-options">
            <button v-for="option in tradeOptions" :key="option.id" type="button" :class="['trade-option-chip', { active: form.related_trade_groups.includes(option.id) }]" @click="toggleTradeGroup(option.id)">
              <strong>{{ option.symbol }}</strong><span>{{ option.status }}</span><span>PnL {{ option.realized_pnl }}</span>
            </button>
          </div>
        </div>

        <div class="journal-text-grid">
          <label class="journal-strategy-row"><span>Strategy</span><select v-model="form.strategy" class="compact-strategy-select"><option value="">Select strategy</option><option v-for="item in activeStrategyOptions" :key="item.id" :value="item.name">{{ item.name }}</option></select></label>
          <label><span>Key levels / catalyst</span><textarea v-model="form.key_levels_catalyst" rows="3"></textarea></label>
          <label><span>Watchlist</span><textarea v-model="form.watchlist" rows="3"></textarea></label>
          <label><span>Market Summary</span><textarea v-model="form.market_summary" rows="3"></textarea></label>
          <label><span>Biggest Mistake</span><textarea v-model="form.biggest_mistake" rows="3"></textarea></label>
          <label><span>Main Lesson</span><textarea v-model="form.lessons" rows="3"></textarea></label>
          <label><span>Tomorrow Plan</span><textarea v-model="form.next_day_plan" rows="3"></textarea></label>
        </div>

        <div class="journal-form-grid">
          <label><span>Discipline (1-10)</span><input v-model.number="form.discipline_score" type="number" min="1" max="10" /></label>
          <label><span>Emotional Control (1-10)</span><input v-model.number="form.emotional_control_score" type="number" min="1" max="10" /></label>
          <label><span>Max Daily Loss Respected?</span><select v-model="maxLossSelection"><option value="">Unknown</option><option value="true">Yes</option><option value="false">No</option></select></label>
        </div>

        <label><span>Review Images</span><div class="helper-row"><input type="file" accept="image/*" multiple @change="handleFileUpload" /><button type="button" class="secondary" @click="clearImages">Clear Images</button></div></label>
        <div v-if="form.image_urls.length" class="image-grid compact-image-grid">
          <div v-for="(url, idx) in form.image_urls" :key="url" class="image-tile"><img :src="url" alt="review preview" class="image-preview" /><button type="button" class="secondary small-btn" @click="removeImage(idx)">Remove</button></div>
        </div>
        <div class="filter-action-row"><button @click="submitReview" :disabled="loading || uploading">{{ savingLabel }}</button><button v-if="editingId" class="secondary" @click="cancelEdit">Cancel</button></div>
      </section>

      <section class="card journal-list-card journal-surface">
        <div class="section-title">Daily Review Timeline</div>
        <div v-for="item in reviews" :key="item.id" class="journal-entry-card accordion tv-journal-card">
          <button class="journal-entry-head accordion-trigger" @click="toggleReview(item.id)">
            <div><div class="review-date">{{ item.review_date }}</div><div class="review-linked-trade">{{ (item.related_trade_groups_display || []).map(t => t.symbol).join(', ') || 'No linked trades' }}</div></div>
            <span class="accordion-indicator">{{ expandedReviewIds.includes(item.id) ? '−' : '+' }}</span>
          </button>
          <div v-if="expandedReviewIds.includes(item.id)" class="accordion-body">
            <div class="journal-entry-grid">
              <div><strong>Regime/Bias</strong><div class="journal-entry-content">{{ item.market_regime || '-' }} / {{ item.daily_bias || '-' }}</div></div>
              <div><strong>Summary</strong><textarea class="journal-entry-content journal-entry-content-resizable" readonly :value="item.market_summary || '-'"></textarea></div>
            </div>
            <div class="journal-inline-actions"><button class="secondary small-btn" @click="editReview(item)">Edit</button><button class="secondary small-btn" @click="removeReview(item.id)">Delete</button></div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { createDailyReview, updateDailyReview, deleteDailyReview, fetchDailyReviews, fetchDailyReviewTradeOptions, uploadDailyReviewImages } from '../api/journal'
import { fetchStrategyOptions } from '../api/common'

const loading = ref(false)
const uploading = ref(false)
const reviews = ref([])
const tradeOptions = ref([])
const strategyOptions = ref([])
const expandedReviewIds = ref([])
const editingId = ref(null)
const dateInputRef = ref(null)
const freshForm = () => ({ review_date: new Date().toISOString().slice(0, 10), related_trade_groups: [], image_urls: [], strategy: '', market_summary: '', lessons: '', next_day_plan: '', market_regime: '', key_levels_catalyst: '', watchlist: '', daily_bias: '', max_daily_loss_respected: null, discipline_score: null, emotional_control_score: null, biggest_mistake: '' })
const form = ref(freshForm())
const maxLossSelection = ref('')

watch(maxLossSelection, (value) => { form.value.max_daily_loss_respected = value === '' ? null : value === 'true' })
const savingLabel = computed(() => (loading.value ? (editingId.value ? 'Updating...' : 'Saving...') : uploading.value ? 'Uploading...' : editingId.value ? 'Update Review' : 'Save Review'))
const activeStrategyOptions = computed(() => strategyOptions.value.filter((item) => item.is_active))

function toggleTradeGroup(id) { const set = new Set(form.value.related_trade_groups); if (set.has(id)) set.delete(id); else set.add(id); form.value.related_trade_groups = Array.from(set) }
async function loadReviews() { const res = await fetchDailyReviews({ page_size: 100 }); reviews.value = res.data.results || [] }
async function loadStrategyOptions() { try { const res = await fetchStrategyOptions(); strategyOptions.value = (res.data?.results || res.data || []).sort((a, b) => (a.sort_order - b.sort_order) || a.name.localeCompare(b.name)) } catch { strategyOptions.value = [] } }
async function loadTradeOptions() { if (!form.value.review_date) return; const res = await fetchDailyReviewTradeOptions(form.value.review_date); tradeOptions.value = res.data || [] }
async function handleFileUpload(event) { const files = event.target.files; if (!files?.length) return; uploading.value = true; try { const res = await uploadDailyReviewImages(files); const urls = res.data.image_urls || (res.data.image_url ? [res.data.image_url] : []); form.value.image_urls = [...form.value.image_urls, ...urls] } finally { uploading.value = false; event.target.value = '' } }
function clearImages() { form.value.image_urls = [] }
function removeImage(idx) { form.value.image_urls.splice(idx, 1) }
function toggleReview(id) { expandedReviewIds.value = expandedReviewIds.value.includes(id) ? expandedReviewIds.value.filter(v => v !== id) : [...expandedReviewIds.value, id] }
function editReview(item) { editingId.value = item.id; form.value = { ...freshForm(), ...item, related_trade_groups: (item.related_trade_groups || []).slice(), image_urls: (item.images || []).map(img => img.image_url) }; maxLossSelection.value = item.max_daily_loss_respected == null ? '' : String(item.max_daily_loss_respected); loadTradeOptions() }
function cancelEdit() { editingId.value = null; form.value = freshForm(); maxLossSelection.value = ''; loadTradeOptions() }
async function removeReview(id) { if (!window.confirm('Delete this review?')) return; await deleteDailyReview(id); if (editingId.value === id) cancelEdit(); await loadReviews() }
async function submitReview() { loading.value = true; try { if (editingId.value) await updateDailyReview(editingId.value, form.value); else await createDailyReview(form.value); cancelEdit(); await loadReviews() } finally { loading.value = false } }

onMounted(async () => { await loadStrategyOptions(); await loadTradeOptions(); await loadReviews() })
</script>
