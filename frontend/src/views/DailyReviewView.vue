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
        <button :class="['tv-subtab', { active: journalTab === 'pretrade' }]" @click="openPretradeTab">Pre-Trade Plan</button>
        <button :class="['tv-subtab', { active: journalTab === 'workspace' }]" @click="journalTab='workspace'">Review Workspace</button>
        <button :class="['tv-subtab', { active: journalTab === 'analytics' }]" @click="openAnalyticsTab">Analytics</button>
        <button :class="['tv-subtab', { active: journalTab === 'timeline' }]" @click="openTimelineTab">Journal Timeline</button>
      </div>
    </section>

    <template v-if="journalTab === 'workspace'">
    <section class="card">
      <div class="journal-form-grid workspace-summary-grid">
        <label :title="fieldHint('queue_date')"><span>Queue Date</span><input v-model="queueDate" type="date" @change="loadQueue" @click="openDatePicker" @focus="openDatePicker" /></label>
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
              <div class="muted-copy">
                Hold {{ card.hold_minutes || '-' }}m ·
                <span class="metric-with-tip">Exec {{ card.executions_count }}<span class="metric-tip">Exec = 该交易时间窗内的成交笔数（Raw Executions count）。</span></span> ·
                <span class="metric-with-tip">Shots {{ card.screenshots_count }}<span class="metric-tip">Shots = 该笔复盘上传的截图数量。</span></span>
              </div>
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
              <label :title="fieldHint('trade_strategy')"><span>Strategy</span><input v-model="tradeReviewForms[card.trade_group_id].strategy" /></label>
              <label :title="fieldHint('setup')"><span>Setup</span>
                <select v-model="tradeReviewForms[card.trade_group_id].setup">
                  <option :value="null">-</option>
                  <option v-for="item in setupTags" :key="item.id" :value="item.id">{{ item.name }}</option>
                </select>
              </label>
              <label :title="fieldHint('grade')"><span>Grade</span><select v-model="tradeReviewForms[card.trade_group_id].final_grade"><option value="">-</option><option>A</option><option>B</option><option>C</option><option>D</option></select></label>
              <label :title="fieldHint('would_take_again')"><span>Would take again</span><select v-model="tradeReviewForms[card.trade_group_id].would_take_again"><option value="">-</option><option value="yes">Yes</option><option value="no">No</option><option value="with_changes">With changes</option></select></label>
              <label :title="fieldHint('entry_q')"><span>Entry Q</span><input type="number" min="1" max="5" v-model.number="tradeReviewForms[card.trade_group_id].entry_quality" /></label>
              <label :title="fieldHint('exit_q')"><span>Exit Q</span><input type="number" min="1" max="5" v-model.number="tradeReviewForms[card.trade_group_id].exit_quality" /></label>
              <label :title="fieldHint('risk_q')"><span>Risk Q</span><input type="number" min="1" max="5" v-model.number="tradeReviewForms[card.trade_group_id].risk_management" /></label>
              <label :title="fieldHint('followed_plan')"><span>Followed plan</span><select v-model="tradeReviewForms[card.trade_group_id].followed_plan"><option :value="null">-</option><option :value="true">Yes</option><option :value="false">No</option></select></label>
              <label :title="fieldHint('primary_mistake_type')"><span>Primary mistake type</span><select v-model="tradeReviewForms[card.trade_group_id].primary_mistake_type"><option value="none">none</option><option value="discipline">discipline</option><option value="execution">execution</option><option value="risk">risk</option><option value="strategy">strategy</option><option value="psychology">psychology</option><option value="process">process</option></select></label>
              <label :title="fieldHint('mistake_severity')"><span>Mistake severity</span><select v-model="tradeReviewForms[card.trade_group_id].mistake_severity"><option value="low">low</option><option value="medium">medium</option><option value="high">high</option></select></label>
              <label :title="fieldHint('rule_violation_type')"><span>Rule violation type</span><select v-model="tradeReviewForms[card.trade_group_id].rule_violation_type"><option value="none">none</option><option value="entry_rule">entry_rule</option><option value="risk_rule">risk_rule</option><option value="exit_rule">exit_rule</option><option value="size_rule">size_rule</option></select></label>
            </div>
            <div class="trade-review-text-grid">
              <label :title="fieldHint('thesis')"><span>Thesis</span><textarea v-model="tradeReviewForms[card.trade_group_id].thesis" rows="2"></textarea></label>
              <label :title="fieldHint('what_to_improve')"><span>What to improve</span><textarea v-model="tradeReviewForms[card.trade_group_id].what_to_improve" rows="2"></textarea></label>
            </div>

            <div :title="fieldHint('mistake_tags')"><span>Mistake Tags</span><div class="chip-wrap">
              <button v-for="tag in mistakeTags" :key="tag.id" type="button" :class="['trade-option-chip', { active: (tradeReviewForms[card.trade_group_id].mistake_tags || []).includes(tag.id) }]" @click="toggleTradeMistakeTag(card.trade_group_id, tag.id)">{{ tag.name }}</button>
            </div></div>

            <label :title="fieldHint('screenshots')">
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
            <div v-if="tradeSaveErrors[card.trade_group_id]" class="save-error">
              {{ tradeSaveErrors[card.trade_group_id] }}
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
        <label :title="fieldHint('market_regime')"><span>Market Regime</span><input v-model="form.market_regime" /></label>
        <label :title="fieldHint('daily_bias')"><span>Daily Bias</span><input v-model="form.daily_bias" /></label>
        <label :title="fieldHint('session_focus')"><span>Session Focus</span><select v-model="form.session"><option value="">-</option><option>open</option><option>midday</option><option>close</option><option>overnight</option></select></label>
        <label :title="fieldHint('market_condition')"><span>Market condition</span><select v-model="form.market_condition"><option value="">-</option><option>trend</option><option>range</option><option>breakout</option><option>reversal</option><option>news</option></select></label>
      </div>

      <div v-if="dailyAccordion === 'execution'" class="journal-form-grid workspace-field-grid">
        <label :title="fieldHint('strategy_focus')"><span>Strategy focus</span><input v-model="form.strategy" /></label>
        <label :title="fieldHint('conviction')"><span>Conviction today (1-10)</span><input type="number" min="1" max="10" v-model.number="form.confidence_score" /></label>
        <label :title="fieldHint('discipline')"><span>Discipline (1-10)</span><input type="number" min="1" max="10" v-model.number="form.discipline_score" /></label>
        <label :title="fieldHint('emotional_control')"><span>Emotional control (1-10)</span><input type="number" min="1" max="10" v-model.number="form.emotional_control_score" /></label>
        <label :title="fieldHint('max_daily_loss')"><span>Max daily loss respected</span><select v-model="maxLossSelection"><option value="">Unknown</option><option value="true">Yes</option><option value="false">No</option></select></label>
      </div>

      <div v-if="dailyAccordion === 'lesson'" class="journal-text-grid">
        <label :title="fieldHint('market_summary')"><span>Market Summary</span><textarea v-model="form.market_summary" rows="3"></textarea></label>
        <label :title="fieldHint('biggest_mistake')"><span>Biggest Mistake</span><textarea v-model="form.biggest_mistake" rows="3"></textarea></label>
        <label :title="fieldHint('main_lesson')"><span>Main Lesson</span><textarea v-model="form.lessons" rows="3"></textarea></label>
        <label :title="fieldHint('tomorrow_plan')"><span>Tomorrow Plan</span><textarea v-model="form.next_day_plan" rows="3"></textarea></label>
      </div>

      <div v-if="dailyAccordion === 'tags'">
        <div :title="fieldHint('daily_mistake_tags')"><span>Daily Mistake Tags</span><div class="chip-wrap">
          <button v-for="tag in mistakeTags" :key="tag.id" type="button" :class="['trade-option-chip', { active: (form.mistake_tags || []).includes(tag.id) }]" @click="toggleDailyMistakeTag(tag.id)">{{ tag.name }}</button>
        </div></div>
        <label :title="fieldHint('daily_screenshots')">
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
            <label :title="fieldHint('thesis_status')"><span>Thesis status</span><select v-model="positionForms[item.trade_group_id].status"><option value="open">still valid</option><option value="reduced">weakened</option><option value="closed">invalid</option></select></label>
          </div>
          <label :title="fieldHint('hold_overnight')"><span>Why hold overnight</span><textarea v-model="positionForms[item.trade_group_id].carry_reason" rows="2"></textarea></label>
          <label :title="fieldHint('risk_tomorrow')"><span>Risk tomorrow</span><textarea v-model="positionForms[item.trade_group_id].gap_risk_note" rows="2"></textarea></label>
          <label :title="fieldHint('next_action')"><span>Next action</span><textarea v-model="positionForms[item.trade_group_id].next_session_plan" rows="2"></textarea></label>
          <div class="filter-action-row"><button @click="saveCheckpoint(item.trade_group_id)" :disabled="savingPosition === item.trade_group_id">{{ savingPosition === item.trade_group_id ? 'Saving...' : 'Save Checkpoint' }}</button></div>
        </div>
      </div>
    </section>
    </template>

    <section v-else-if="journalTab === 'pretrade'" class="card">
      <div class="section-title">Pre-Trade Plan / Setup Snapshot</div>
      <div class="journal-form-grid workspace-field-grid">
        <label :title="fieldHint('queue_date')"><span>Plan Date</span><input v-model="pretradeDate" type="date" @change="loadPretrade" @click="openDatePicker" @focus="openDatePicker" /></label>
        <label :title="fieldHint('session_focus')"><span>Session</span><select v-model="pretradeForm.session"><option value="premarket">premarket</option><option value="open">open</option><option value="midday">midday</option><option value="close">close</option></select></label>
        <label :title="fieldHint('market_regime')"><span>Market Regime</span><input v-model="pretradeForm.market_regime" /></label>
        <label :title="fieldHint('watchlist')"><span>Watchlist (comma-separated)</span><input v-model="watchlistText" placeholder="AAPL, NVDA, TSLA" /></label>
        <label><span>Risk Budget (R)</span><input type="number" step="0.1" v-model.number="pretradeForm.risk_budget_r" /></label>
      </div>
      <label :title="fieldHint('game_plan')"><span>Game Plan</span><textarea v-model="pretradeForm.game_plan" rows="3"></textarea></label>
      <label :title="fieldHint('catalysts')"><span>Catalysts</span><textarea v-model="pretradeForm.catalysts" rows="2"></textarea></label>
      <label><span>Checklist JSON</span><textarea v-model="checklistText" rows="2"></textarea></label>
      <div class="filter-action-row">
        <button @click="savePretrade" :disabled="savingPretrade">{{ savingPretrade ? 'Saving...' : 'Save Pre-Trade Plan' }}</button>
      </div>

      <div class="section-title" style="margin-top:14px;">Setup Snapshots</div>
      <div v-for="(row, idx) in snapshotForms" :key="`snap-${idx}`" class="journal-entry-card" style="margin-bottom:10px;">
        <div class="journal-form-grid trade-review-form-grid">
          <label><span>Symbol</span><input v-model="row.symbol" /></label>
          <label><span>Strategy</span><input v-model="row.strategy" /></label>
          <label><span>Setup</span><select v-model="row.setup"><option :value="null">-</option><option v-for="item in setupTags" :key="item.id" :value="item.id">{{ item.name }}</option></select></label>
          <label><span>Checklist passed</span><select v-model="row.checklist_passed"><option :value="true">Yes</option><option :value="false">No</option></select></label>
        </div>
        <div class="journal-form-grid workspace-field-grid">
          <label><span>Planned Entry</span><input type="number" step="0.0001" v-model.number="row.planned_entry" /></label>
          <label><span>Planned Stop</span><input type="number" step="0.0001" v-model.number="row.planned_stop" /></label>
          <label><span>Planned Target</span><input type="number" step="0.0001" v-model.number="row.planned_target" /></label>
        </div>
        <label><span>Trigger condition</span><textarea v-model="row.trigger_condition" rows="2"></textarea></label>
        <label><span>Invalidation</span><textarea v-model="row.invalidation" rows="2"></textarea></label>
        <div class="filter-action-row">
          <button @click="saveSnapshot(row)" :disabled="savingSnapshotId === row.local_id">{{ savingSnapshotId === row.local_id ? 'Saving...' : 'Save Snapshot' }}</button>
        </div>
      </div>
      <button class="secondary" @click="addSnapshotRow">Add Snapshot</button>
    </section>

    <section v-else-if="journalTab === 'analytics'" class="card">
      <div class="section-title">Trade Review Analytics</div>
      <div class="filter-action-row" style="margin-top:0;">
        <button @click="loadAnalytics" :disabled="loadingAnalytics">{{ loadingAnalytics ? 'Loading...' : 'Refresh Analytics' }}</button>
      </div>
      <div v-if="analyticsError" class="save-error">{{ analyticsError }}</div>
      <div v-if="!analytics.by_strategy.length && !analytics.by_session.length && !analytics.by_symbol.length" class="empty-row">
        No analytics data yet. Save Trade Reviews with `realized_r` / `session` / `strategy` first.
      </div>
      <div class="journal-text-grid" v-else>
        <div class="journal-entry-card">
          <div class="section-title minor">Portfolio Summary</div>
          <div class="muted-copy">Trades (N): {{ analytics.summary?.trades ?? 0 }} · Wins {{ analytics.summary?.wins ?? 0 }} · Losses {{ analytics.summary?.losses ?? 0 }}</div>
          <div class="muted-copy">Total PnL: {{ analytics.summary?.total_pnl ?? 0 }} · Expectancy: {{ analytics.summary?.expectancy ?? '-' }}</div>
          <div class="muted-copy">Profit Factor: {{ analytics.summary?.profit_factor ?? '-' }} · Max Drawdown: {{ analytics.summary?.max_drawdown ?? 0 }}</div>
        </div>
        <div class="journal-entry-card">
          <div class="section-title minor">Compare</div>
          <div class="journal-form-grid workspace-field-grid">
            <label><span>Dimension</span>
              <select v-model="compareDimension">
                <option v-for="item in analyticsDimensionOptions" :key="item.key" :value="item.key">{{ item.label }}</option>
              </select>
            </label>
            <label><span>Left</span>
              <select v-model="compareLeftKey"><option v-for="key in comparisonOptions" :key="`l-${key}`" :value="key">{{ key }}</option></select>
            </label>
            <label><span>Right</span>
              <select v-model="compareRightKey"><option v-for="key in comparisonOptions" :key="`r-${key}`" :value="key">{{ key }}</option></select>
            </label>
          </div>
          <div class="muted-copy" v-if="leftCompareRow">{{ compareLeftKey }} → N {{ leftCompareRow.trades }} · Win {{ leftCompareRow.win_rate }}% · PnL {{ leftCompareRow.total_pnl }} · Exp {{ leftCompareRow.expectancy }} · PF {{ leftCompareRow.profit_factor ?? '-' }}</div>
          <div class="muted-copy" v-if="rightCompareRow">{{ compareRightKey }} → N {{ rightCompareRow.trades }} · Win {{ rightCompareRow.win_rate }}% · PnL {{ rightCompareRow.total_pnl }} · Exp {{ rightCompareRow.expectancy }} · PF {{ rightCompareRow.profit_factor ?? '-' }}</div>
        </div>
        <div>
          <div class="section-title minor">By Strategy</div>
          <div v-for="row in analytics.by_strategy" :key="`s-${row.key}`" class="review-item">
            {{ row.key }} · N {{ row.trades }} · Win {{ row.win_rate }}% · PnL {{ row.total_pnl }} · Avg R {{ row.avg_r ?? '-' }} · Exp {{ row.expectancy ?? '-' }} · PF {{ row.profit_factor ?? '-' }} · Hold {{ row.avg_holding_minutes ?? '-' }}m
          </div>
        </div>
        <div>
          <div class="section-title minor">By Session</div>
          <div v-for="row in analytics.by_session" :key="`ss-${row.key}`" class="review-item">
            {{ row.key }} · N {{ row.trades }} · Win {{ row.win_rate }}% · PnL {{ row.total_pnl }} · Avg R {{ row.avg_r ?? '-' }} · Exp {{ row.expectancy ?? '-' }} · PF {{ row.profit_factor ?? '-' }} · Hold {{ row.avg_holding_minutes ?? '-' }}m
          </div>
        </div>
      </div>
      <div>
        <div class="section-title minor">By Symbol</div>
        <div v-for="row in analytics.by_symbol" :key="`sym-${row.key}`" class="review-item">
          {{ row.key }} · N {{ row.trades }} · Win {{ row.win_rate }}% · PnL {{ row.total_pnl }} · Avg R {{ row.avg_r ?? '-' }} · Exp {{ row.expectancy ?? '-' }} · PF {{ row.profit_factor ?? '-' }} · Hold {{ row.avg_holding_minutes ?? '-' }}m
        </div>
      </div>
      <div class="tv-dashboard-chart-grid tv-dashboard-chart-grid-triple" style="margin-top:12px;">
        <TradesVizChart title="Equity Curve" subtitle="Cumulative realized PnL" :categories="equityCategories" :series="equitySeries" default-type="line" :height="180" />
        <TradesVizChart title="R Distribution" subtitle="Per-trade R multiples" :categories="rDistributionCategories" :series="rDistributionSeries" default-type="bar" :height="180" />
        <TradesVizChart title="Holding Time vs PnL" subtitle="Pattern view (proxy chart)" :categories="holdingScatterCategories" :series="holdingScatterSeries" default-type="line" :height="180" />
      </div>
    </section>

    <section v-else class="card">
      <div class="section-title">Journal Timeline</div>
      <div class="journal-form-grid timeline-filter-grid">
        <label :title="fieldHint('date_from')"><span>Date From</span><input v-model="timelineDateFrom" type="date" @change="loadTimeline" @click="openDatePicker" @focus="openDatePicker" /></label>
        <label :title="fieldHint('date_to')"><span>Date To</span><input v-model="timelineDateTo" type="date" @change="loadTimeline" @click="openDatePicker" @focus="openDatePicker" /></label>
        <label><span>Strategy contains</span><input v-model="timelineStrategyQuery" placeholder="breakout / opening..." /></label>
        <label><span>Session</span><select v-model="timelineSessionFilter"><option value="">All</option><option value="open">open</option><option value="midday">midday</option><option value="close">close</option><option value="overnight">overnight</option></select></label>
        <label><span>Loss days only</span><select v-model="timelineLossOnly"><option :value="false">No</option><option :value="true">Yes</option></select></label>
        <label><span>Low emotion only (<=4)</span><select v-model="timelineLowEmotionOnly"><option :value="false">No</option><option :value="true">Yes</option></select></label>
        <button class="secondary" @click="loadTimeline">Refresh</button>
      </div>
      <div v-if="!filteredTimeline.length" class="empty-row">No daily reviews matched the filters.</div>
      <div v-for="item in filteredTimeline" :key="item.id" class="journal-entry-card" style="margin-bottom:10px;">
        <div class="journal-entry-head" style="justify-content:space-between;">
          <div>
            <strong>{{ item.review_date }}</strong>
            <span class="badge" style="margin-left:8px;">{{ item.review_status || 'draft' }}</span>
          </div>
          <div class="muted-copy">Updated {{ item.updated_at ? new Date(item.updated_at).toLocaleString() : '-' }}</div>
        </div>
        <div class="muted-copy">Regime/Bias: {{ item.market_regime || '-' }} / {{ item.daily_bias || '-' }} · Session {{ item.session || '-' }} · Condition {{ item.market_condition || '-' }}</div>
        <div class="muted-copy">Scores: conviction {{ item.confidence_score ?? '-' }} · discipline {{ item.discipline_score ?? '-' }} · emotion {{ item.emotional_control_score ?? '-' }}</div>
        <div class="muted-copy">Day PnL: {{ dailyPnl(item) }} · Trades: {{ (item.related_trade_groups_display || []).length }} · Images {{ item.images?.length || 0 }}</div>
        <div class="chip-wrap" style="margin-top:6px;">
          <span class="badge">Setup: {{ setupTagsFromDay(item).join(', ') || '-' }}</span>
          <span class="badge">Execution tags: {{ mistakeNames(item).join(', ') || '-' }}</span>
        </div>
        <div class="review-item" style="margin-top:8px;"><strong>✔ 做对了：</strong>{{ item.market_summary || '-' }}</div>
        <div class="review-item"><strong>❌ 错在哪：</strong>{{ item.biggest_mistake || '-' }}</div>
        <div class="review-item"><strong>→ 明天改什么：</strong>{{ item.next_day_plan || '-' }}</div>
        <div class="filter-action-row" style="margin-top:8px;">
          <button class="secondary small-btn" @click="toggleTimelineTrades(item.review_date)">{{ expandedTimelineDates.includes(item.review_date) ? 'Hide Trades' : 'Show Trades' }}</button>
          <span class="muted-copy" v-if="timelineLoadingDate === item.review_date">Loading trade details...</span>
        </div>
        <div v-if="expandedTimelineDates.includes(item.review_date)" class="accordion-body" style="padding-top:8px;">
          <div v-if="!(timelineTradeDetailsByDate[item.review_date] || []).length" class="empty-row">No closed trades for this date.</div>
          <div v-for="card in (timelineTradeDetailsByDate[item.review_date] || [])" :key="`tl-${item.review_date}-${card.trade_group_id}`" class="review-item">
            {{ card.symbol }} · PnL {{ card.realized_pnl }} · Exec {{ card.executions_count }} · Hold {{ card.hold_minutes ?? '-' }}m · EntryQ {{ card.trade_review?.entry_quality ?? '-' }} · ExitQ {{ card.trade_review?.exit_quality ?? '-' }} · RiskQ {{ card.trade_review?.risk_management ?? '-' }} · R {{ card.trade_review?.realized_r ?? '-' }}
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import TradesVizChart from '../components/TradesVizChart.vue'
import {
  createDailyReview,
  fetchDailyReviews,
  fetchMistakeTags,
  fetchPretradePlans,
  fetchReviewQueue,
  fetchSetupSnapshots,
  fetchSetupTags,
  fetchTradeReviewAnalyticsSummary,
  savePretradePlan,
  savePositionCheckpoint,
  updatePretradePlan,
  updateSetupSnapshot,
  saveSetupSnapshot,
  saveTradeReview,
  uploadDailyReviewImages,
} from '../api/journal'

const queueDate = ref(new Date().toISOString().slice(0, 10))
const journalTab = ref('pretrade')
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
const tradeSaveErrors = ref({})
const maxLossSelection = ref('')
const tradeSectionRef = ref(null)
const dailySectionRef = ref(null)
const positionSectionRef = ref(null)
const dailyTimeline = ref([])
const timelineDateFrom = ref('')
const timelineDateTo = ref('')
const timelineStrategyQuery = ref('')
const timelineSessionFilter = ref('')
const timelineLossOnly = ref(false)
const timelineLowEmotionOnly = ref(false)
const expandedTimelineDates = ref([])
const timelineTradeDetailsByDate = ref({})
const timelineLoadingDate = ref('')
const pretradeDate = ref(new Date().toISOString().slice(0, 10))
const pretradeForm = ref({ id: null, plan_date: pretradeDate.value, session: 'premarket', market_regime: '', watchlist: [], catalysts: '', game_plan: '', pre_trade_checklist: {}, risk_budget_r: null, notes: '' })
const watchlistText = ref('')
const checklistText = ref('{}')
const snapshotForms = ref([])
const savingPretrade = ref(false)
const savingSnapshotId = ref(null)
const analytics = ref({ by_strategy: [], by_session: [], by_symbol: [] })
const loadingAnalytics = ref(false)
const analyticsError = ref('')
const compareDimension = ref('by_strategy')
const compareLeftKey = ref('')
const compareRightKey = ref('')

const form = ref({ review_date: queueDate.value, review_status: 'draft', strategy: '', market_regime: '', daily_bias: '', market_summary: '', biggest_mistake: '', lessons: '', next_day_plan: '', related_trade_groups: [], session: '', market_condition: '', confidence_score: null, discipline_score: null, emotional_control_score: null, max_daily_loss_respected: null, mistake_tags: [], image_urls: [] })

const completionRate = computed(() => {
  const total = (queue.value.summary.closed_trade_count || 0) + (queue.value.summary.open_position_count || 0) + 1
  const doneTrades = (queue.value.closed_trades || []).filter((t) => (t.review_completeness || 0) >= 80).length
  const donePositions = (queue.value.open_positions || []).filter((p) => p.latest_checkpoint_id).length
  const doneDaily = queue.value.summary.daily_review_completed ? 1 : 0
  return total ? Math.round(((doneTrades + donePositions + doneDaily) / total) * 100) : 0
})

const FIELD_HINTS = {
  queue_date: '选择要处理复盘队列的交易日期。',
  trade_strategy: '本笔交易使用的策略名称/方向。',
  setup: '交易形态/模式（如 Breakout、Pullback）。',
  grade: '本笔交易综合评级（A最好）。',
  would_take_again: '如果再来一次，你是否还会做这笔交易。',
  entry_q: '1-5分：入场质量，5=非常理想。',
  exit_q: '1-5分：出场执行质量，5=非常理想。',
  risk_q: '1-5分：风险控制质量（仓位/止损执行）。',
  followed_plan: '是否按原计划执行。',
  thesis: '这笔交易的核心逻辑与依据。',
  what_to_improve: '这笔交易后续可改进点。',
  mistake_tags: '本笔交易出现的问题标签（可多选）。',
  screenshots: '上传该笔交易相关截图，用于复盘留档。',
  market_regime: '当天主要市场环境（趋势/震荡等）。',
  daily_bias: '当日主观偏向（看多/看空/中性）。',
  session_focus: '复盘重点所在时段（开盘/中段/尾盘等）。',
  market_condition: '当天更细的行情状态标签。',
  strategy_focus: '当天重点执行的策略主题。',
  conviction: '1-10分：当日交易信念强度。',
  discipline: '1-10分：纪律执行程度。',
  emotional_control: '1-10分：情绪控制程度。',
  max_daily_loss: '是否遵守了日亏损上限。',
  market_summary: '对市场表现的简要总结。',
  biggest_mistake: '当天最关键的错误。',
  main_lesson: '当天最重要的经验教训。',
  tomorrow_plan: '次日执行计划。',
  daily_mistake_tags: '当天层面的错误标签（可多选）。',
  daily_screenshots: '上传当日复盘截图。',
  thesis_status: '隔夜持仓原始逻辑当前是否仍成立。',
  hold_overnight: '继续持仓到次日的原因。',
  risk_tomorrow: '次日可能面临的主要风险。',
  next_action: '次日计划动作（持有/减仓/平仓条件）。',
  date_from: '时间线起始日期。',
  date_to: '时间线结束日期。',
  primary_mistake_type: '错误主类型硬分类，用于后续成本归因。',
  mistake_severity: '错误严重度硬分类。',
  rule_violation_type: '违规规则类型硬分类。',
  watchlist: '盘前重点观察标的列表。',
  game_plan: '盘前执行剧本与优先级。',
  catalysts: '盘前重要事件/催化剂。',
}

function fieldHint(key) {
  return FIELD_HINTS[key] || ''
}

const analyticsDimensionOptions = computed(() => ([
  { key: 'by_strategy', label: 'Strategy' },
  { key: 'by_session', label: 'Session' },
  { key: 'by_symbol', label: 'Symbol' },
]))

const analyticsRowsForDimension = computed(() => analytics.value?.[compareDimension.value] || [])
const comparisonOptions = computed(() => analyticsRowsForDimension.value.map((row) => row.key))
const leftCompareRow = computed(() => analyticsRowsForDimension.value.find((row) => row.key === compareLeftKey.value) || null)
const rightCompareRow = computed(() => analyticsRowsForDimension.value.find((row) => row.key === compareRightKey.value) || null)
const equityCategories = computed(() => (analytics.value.equity_curve || []).map((p) => p.date))
const equitySeries = computed(() => [{ name: 'Equity', data: (analytics.value.equity_curve || []).map((p) => p.equity) }])
const rDistributionCategories = computed(() => (analytics.value.r_distribution || []).map((_, idx) => `T${idx + 1}`))
const rDistributionSeries = computed(() => [{ name: 'R Multiple', data: analytics.value.r_distribution || [] }])
const holdingScatterCategories = computed(() => (analytics.value.holding_vs_pnl || []).map((_, idx) => `P${idx + 1}`))
const holdingScatterSeries = computed(() => [
  { name: 'Holding Minutes', data: (analytics.value.holding_vs_pnl || []).map((p) => p.holding_minutes) },
  { name: 'PnL', data: (analytics.value.holding_vs_pnl || []).map((p) => p.pnl) },
])

const filteredTimeline = computed(() => {
  return (dailyTimeline.value || []).filter((item) => {
    const strategyOk = !timelineStrategyQuery.value || (item.strategy || '').toLowerCase().includes(timelineStrategyQuery.value.toLowerCase())
    const sessionOk = !timelineSessionFilter.value || (item.session || '') === timelineSessionFilter.value
    const pnl = dailyPnl(item)
    const lossOk = !timelineLossOnly.value || pnl < 0
    const emotionOk = !timelineLowEmotionOnly.value || ((item.emotional_control_score ?? 999) <= 4)
    return strategyOk && sessionOk && lossOk && emotionOk
  })
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
      primary_mistake_type: review.primary_mistake_type || 'none',
      mistake_severity: review.mistake_severity || 'low',
      rule_violation_type: review.rule_violation_type || 'none',
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

function dailyPnl(item) {
  return (item.related_trade_groups_display || []).reduce((sum, t) => sum + Number(t.realized_pnl || 0), 0)
}

function mistakeNames(item) {
  const ids = item.mistake_tags || []
  return ids.map((id) => (mistakeTags.value || []).find((t) => t.id === id)?.name).filter(Boolean)
}

function setupTagsFromDay(item) {
  const cards = timelineTradeDetailsByDate.value[item.review_date] || []
  return Array.from(new Set(cards.map((card) => card.setup_name).filter(Boolean)))
}

async function toggleTimelineTrades(reviewDate) {
  if (expandedTimelineDates.value.includes(reviewDate)) {
    expandedTimelineDates.value = expandedTimelineDates.value.filter((d) => d !== reviewDate)
    return
  }
  expandedTimelineDates.value = [...expandedTimelineDates.value, reviewDate]
  if (timelineTradeDetailsByDate.value[reviewDate]) return
  timelineLoadingDate.value = reviewDate
  try {
    const res = await fetchReviewQueue(reviewDate)
    timelineTradeDetailsByDate.value[reviewDate] = res.data?.closed_trades || []
  } finally {
    timelineLoadingDate.value = ''
  }
}

async function openTimelineTab() {
  journalTab.value = 'timeline'
  if (!dailyTimeline.value.length) await loadTimeline()
}

async function openPretradeTab() {
  journalTab.value = 'pretrade'
  await loadPretrade()
}

async function openAnalyticsTab() {
  journalTab.value = 'analytics'
  await loadAnalytics()
}

async function saveCardReview(tradeGroupId) {
  savingTrade.value = tradeGroupId
  try {
    const payload = { ...tradeReviewForms.value[tradeGroupId] }
    payload.entry_quality = normalizeScore(payload.entry_quality)
    payload.exit_quality = normalizeScore(payload.exit_quality)
    payload.risk_management = normalizeScore(payload.risk_management)
    await saveTradeReview(payload)
    tradeSaveErrors.value[tradeGroupId] = ''
    await loadQueue()
  } catch (error) {
    const data = error?.response?.data || {}
    tradeSaveErrors.value[tradeGroupId] = Object.entries(data)
      .map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(', ') : value}`)
      .join(' | ') || 'Save failed. Please check required fields.'
  } finally {
    savingTrade.value = null
  }
}

function normalizeScore(value) {
  if (value === '' || value == null) return null
  const n = Number(value)
  if (!Number.isFinite(n)) return null
  return Math.min(5, Math.max(1, Math.round(n)))
}

function buildLocalSnapshot(item = {}) {
  return {
    local_id: item.id || `${Date.now()}-${Math.random()}`,
    id: item.id || null,
    pretrade_plan: item.pretrade_plan || pretradeForm.value.id,
    trade_group: item.trade_group || null,
    symbol: item.symbol || '',
    strategy: item.strategy || '',
    setup: item.setup || null,
    trigger_condition: item.trigger_condition || '',
    invalidation: item.invalidation || '',
    planned_entry: item.planned_entry,
    planned_stop: item.planned_stop,
    planned_target: item.planned_target,
    checklist_passed: item.checklist_passed ?? false,
    snapshot_notes: item.snapshot_notes || '',
  }
}

async function loadPretrade() {
  const res = await fetchPretradePlans({ date: pretradeDate.value, page_size: 1 })
  const existing = (res.data?.results || res.data || [])[0]
  if (existing) {
    pretradeForm.value = { ...existing }
    watchlistText.value = (existing.watchlist || []).join(', ')
    checklistText.value = JSON.stringify(existing.pre_trade_checklist || {}, null, 2)
    const snaps = await fetchSetupSnapshots({ pretrade_plan: existing.id, page_size: 50 })
    snapshotForms.value = (snaps.data?.results || snaps.data || []).map((item) => buildLocalSnapshot(item))
  } else {
    pretradeForm.value = { id: null, plan_date: pretradeDate.value, session: 'premarket', market_regime: '', watchlist: [], catalysts: '', game_plan: '', pre_trade_checklist: {}, risk_budget_r: null, notes: '' }
    watchlistText.value = ''
    checklistText.value = '{}'
    snapshotForms.value = [buildLocalSnapshot()]
  }
}

async function savePretrade() {
  savingPretrade.value = true
  try {
    let parsedChecklist = {}
    try { parsedChecklist = JSON.parse(checklistText.value || '{}') } catch { parsedChecklist = {} }
    const payload = {
      ...pretradeForm.value,
      plan_date: pretradeDate.value,
      watchlist: watchlistText.value.split(',').map((v) => v.trim()).filter(Boolean),
      pre_trade_checklist: parsedChecklist,
    }
    const res = pretradeForm.value.id ? await updatePretradePlan(pretradeForm.value.id, payload) : await savePretradePlan(payload)
    pretradeForm.value = res.data
    if (!snapshotForms.value.length) snapshotForms.value = [buildLocalSnapshot()]
  } finally {
    savingPretrade.value = false
  }
}

function addSnapshotRow() {
  snapshotForms.value.push(buildLocalSnapshot())
}

async function saveSnapshot(row) {
  if (!pretradeForm.value.id) await savePretrade()
  savingSnapshotId.value = row.local_id
  try {
    const payload = { ...row, pretrade_plan: pretradeForm.value.id }
    delete payload.local_id
    const res = row.id ? await updateSetupSnapshot(row.id, payload) : await saveSetupSnapshot(payload)
    Object.assign(row, buildLocalSnapshot(res.data))
  } finally {
    savingSnapshotId.value = null
  }
}

async function loadAnalytics() {
  loadingAnalytics.value = true
  try {
    analyticsError.value = ''
    const res = await fetchTradeReviewAnalyticsSummary()
    analytics.value = res.data || { by_strategy: [], by_session: [], by_symbol: [] }
    const keys = (analytics.value[compareDimension.value] || []).map((row) => row.key)
    compareLeftKey.value = keys[0] || ''
    compareRightKey.value = keys[1] || keys[0] || ''
  } catch (error) {
    analyticsError.value = error?.response?.data?.detail || 'Failed to load analytics.'
  } finally {
    loadingAnalytics.value = false
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
  await loadPretrade()
  await loadAnalytics()
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

.metric-with-tip {
  position: relative;
  display: inline-flex;
  align-items: center;
}
.metric-tip {
  position: absolute;
  left: 0;
  top: calc(100% + 6px);
  z-index: 20;
  min-width: 200px;
  max-width: 280px;
  padding: 8px 10px;
  border-radius: 8px;
  background: #0f172a;
  color: #f8fafc;
  font-size: 12px;
  line-height: 1.35;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.25);
  opacity: 0;
  pointer-events: none;
  transform: translateY(-2px);
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.metric-with-tip:hover .metric-tip {
  opacity: 1;
  transform: translateY(0);
}

.save-error {
  margin-top: 8px;
  color: #b91c1c;
  font-size: 12px;
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
