<template>
  <div>
    <div class="dashboard-hero card compact-header-card">
      <div>
        <div class="dashboard-kicker">System</div>
        <h1 class="dashboard-title">Settings</h1>
        <p class="dashboard-subtitle">查看连接状态，并把默认 dashboard tab / 日期范围保存到后端数据库。</p>
      </div>
    </div>

    <div class="settings-grid">
      <div class="card settings-card">
        <div class="section-title">IBKR Flex Connection</div>
        <div class="settings-status-grid">
          <div class="settings-status-item">
            <div class="settings-status-label">Token</div>
            <div :class="['settings-status-value', config?.token_exists ? 'ok' : 'bad']">{{ config?.token_exists ? 'Configured' : 'Missing' }}</div>
          </div>
          <div class="settings-status-item">
            <div class="settings-status-label">Query ID</div>
            <div :class="['settings-status-value', config?.query_id_exists ? 'ok' : 'bad']">{{ config?.query_id_exists ? 'Configured' : 'Missing' }}</div>
          </div>
          <div class="settings-status-item">
            <div class="settings-status-label">Ready</div>
            <div :class="['settings-status-value', ready ? 'ok' : 'bad']">{{ ready ? 'Ready to sync' : 'Needs attention' }}</div>
          </div>
        </div>
        <div class="settings-copy">
          <div><strong>Token Preview:</strong> {{ config?.token_preview || '-' }}</div>
          <div><strong>Query ID:</strong> {{ config?.query_id || '-' }}</div>
        </div>
        <div class="settings-actions">
          <button @click="loadConfigStatus">Refresh Status</button>
        </div>
      </div>

      <div class="card settings-card">
        <div class="section-title">Dashboard Defaults</div>
        <div class="settings-form-grid">
          <label>
            <span>Default Dashboard Tab</span>
            <select v-model="form.default_dashboard_tab">
              <option :value="null">System default</option>
              <option v-for="tab in tabs" :key="tab.id" :value="tab.id">{{ tab.name }}</option>
            </select>
          </label>
          <label>
            <span>Default Date Range</span>
            <select v-model="form.default_date_range">
              <option value="all">All</option>
              <option value="7d">7D</option>
              <option value="30d">30D</option>
              <option value="mtd">MTD</option>
              <option value="ytd">YTD</option>
            </select>
          </label>
        </div>
        <div class="settings-copy muted-copy">
          这些默认值会存到后端数据库，Dashboard 首次打开时会优先使用这里的配置。
        </div>
        <div class="settings-actions">
          <button @click="saveDefaults" :disabled="saving">{{ saving ? 'Saving...' : 'Save Defaults' }}</button>
        </div>
      </div>

      <div class="card settings-card">
        <div class="section-title">Journal Strategies</div>
        <div class="settings-copy muted-copy">用于 Journal 的 Strategy 下拉配置。可调整排序、启用/停用、增删。</div>
        <div class="settings-form-grid strategy-settings-grid">
          <label>
            <span>New Strategy</span>
            <input v-model.trim="newStrategyName" type="text" placeholder="例如：Opening Breakout" @keyup.enter="addStrategy" />
          </label>
          <div class="settings-actions">
            <button @click="addStrategy" :disabled="!newStrategyName || strategySaving">{{ strategySaving ? 'Saving...' : 'Add Strategy' }}</button>
          </div>
        </div>

        <div class="strategy-list">
          <div v-for="item in strategyOptions" :key="item.id" class="strategy-row">
            <div class="strategy-main-group">
              <input v-model.trim="item.name" type="text" placeholder="Strategy name" />
              <label class="strategy-order-group">
                <span>Order</span>
                <input v-model.number="item.sort_order" type="number" min="0" />
              </label>
            </div>
            <label class="strategy-toggle">
              <input v-model="item.is_active" type="checkbox" />
              Active
            </label>
            <div class="strategy-actions-fixed">
              <button class="secondary small-btn" @click="saveStrategy(item)">Save</button>
              <button class="secondary small-btn" @click="removeStrategy(item.id)">Delete</button>
            </div>
          </div>
          <div v-if="!strategyOptions.length" class="muted-copy">No strategies configured yet.</div>
        </div>
      </div>

      <div class="card settings-card">
        <div class="section-title">Local Workspace</div>
        <div class="settings-copy">
          <p>下面这些仍然保存在浏览器本地：</p>
          <ul class="settings-list">
            <li>Widget visibility</li>
            <li>Chart panel widths</li>
            <li>Expanded filter state</li>
            <li>Journal accordion expanded state</li>
          </ul>
        </div>
        <div class="settings-actions">
          <button class="secondary" @click="clearLocalPrefs">Clear Local UI Prefs</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { fetchIBKRConfigStatus } from '../api/syncs'
import {
  fetchDashboardPreferences,
  fetchDashboardTabs,
  saveDashboardPreferences,
  fetchStrategyOptions,
  createStrategyOption,
  updateStrategyOption,
  deleteStrategyOption,
} from '../api/common'

const config = ref(null)
const tabs = ref([])
const saving = ref(false)
const form = reactive({ default_dashboard_tab: null, default_date_range: 'all' })
const ready = computed(() => Boolean(config.value?.token_exists && config.value?.query_id_exists))
const strategyOptions = ref([])
const strategySaving = ref(false)
const newStrategyName = ref('')

async function loadConfigStatus() {
  try {
    const res = await fetchIBKRConfigStatus()
    config.value = res.data
  } catch {
    config.value = { token_exists: false, query_id_exists: false, token_preview: '', query_id: '' }
  }
}
async function loadDashboardSettings() {
  const [tabRes, prefRes] = await Promise.all([fetchDashboardTabs(), fetchDashboardPreferences()])
  tabs.value = tabRes.data?.results || tabRes.data || []
  form.default_dashboard_tab = prefRes.data.default_dashboard_tab
  form.default_date_range = prefRes.data.default_date_range || 'all'
}
async function saveDefaults() {
  saving.value = true
  try {
    await saveDashboardPreferences({
      default_dashboard_tab: form.default_dashboard_tab,
      default_date_range: form.default_date_range,
    })
    alert('Dashboard defaults saved.')
  } finally {
    saving.value = false
  }
}

async function loadStrategyOptions() {
  const res = await fetchStrategyOptions()
  strategyOptions.value = (res.data?.results || res.data || []).sort((a, b) => (a.sort_order - b.sort_order) || a.name.localeCompare(b.name))
}

async function addStrategy() {
  if (!newStrategyName.value) return
  strategySaving.value = true
  try {
    await createStrategyOption({
      name: newStrategyName.value,
      is_active: true,
      sort_order: strategyOptions.value.length,
    })
    newStrategyName.value = ''
    await loadStrategyOptions()
  } finally {
    strategySaving.value = false
  }
}

async function saveStrategy(item) {
  await updateStrategyOption(item.id, {
    name: item.name,
    is_active: item.is_active,
    sort_order: item.sort_order,
  })
  await loadStrategyOptions()
}

async function removeStrategy(id) {
  if (!window.confirm('Delete this strategy option?')) return
  await deleteStrategyOption(id)
  await loadStrategyOptions()
}
function clearLocalPrefs() {
  Object.keys(localStorage)
    .filter((key) => key.startsWith('trade-dashboard-') || key.startsWith('tv-') || key.startsWith('journal-'))
    .forEach((key) => localStorage.removeItem(key))
  alert('Local UI preferences cleared.')
}

onMounted(async () => {
  await loadConfigStatus()
  await loadDashboardSettings()
  await loadStrategyOptions()
})
</script>
