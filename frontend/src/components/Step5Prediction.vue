<template>
  <div class="prediction-panel">
    <!-- 加载中状态 -->
    <div class="auto-loading-state" v-if="isAutoLoading">
      <div class="loading-animation">
        <div class="loading-ring"></div>
        <div class="loading-ring"></div>
        <div class="loading-ring"></div>
      </div>
      <h3>正在分析舆情数据...</h3>
      <p class="loading-step">{{ loadingStep }}</p>
      <div class="loading-progress">
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: loadingProgress + '%' }"></div>
        </div>
        <span class="progress-text">{{ loadingProgress }}%</span>
      </div>
    </div>

    <!-- Agent分析中状态 -->
    <div class="agent-analyzing-state" v-else-if="isPredicting && !predictionData">
      <div class="agent-header">
        <div class="agent-icon">🤖</div>
        <div class="agent-status">
          <h3>Prediction Agent 正在工作</h3>
          <p class="agent-stage">{{ getStageText(agentStage) }}</p>
        </div>
      </div>
      
      <div class="agent-progress-bar">
        <div class="agent-progress-fill" :style="{ width: agentProgress + '%' }"></div>
      </div>
      
      <div class="agent-message" v-if="agentMessage">
        <span class="message-icon">💭</span>
        <span>{{ agentMessage }}</span>
      </div>

      <div class="agent-logs-preview" v-if="agentLogs.length > 0">
        <div class="logs-header">
          <span>思考过程</span>
          <span class="logs-count">{{ agentLogs.length }} 条记录</span>
        </div>
        <div class="logs-list">
          <div 
            v-for="(log, idx) in agentLogs.slice(-5)" 
            :key="idx" 
            class="log-item"
            :class="log.action"
          >
            <span class="log-action">{{ getActionText(log.action) }}</span>
            <span class="log-message">{{ log.details?.message || log.details?.thought || '' }}</span>
          </div>
        </div>
      </div>

      <div class="agent-info">
        <span class="info-item">📊 事件: {{ eventSummary.slice(0, 30) }}...</span>
        <span class="info-item">🌡️ 情绪: {{ currentSentiment }}</span>
        <span class="info-item">📅 预测: {{ timeRange }}天</span>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="prediction-content" v-else-if="predictionData">
      <!-- 🦋 蝴蝶效应沙盒 -->
        <div class="sandbox-section">
          <h4 class="section-title">🦋 蝴蝶效应沙盒</h4>
          <p class="sandbox-subtitle">选择干预策略，观察蝴蝶效应如何改变舆情走向</p>

          <!-- 干预动作卡片池 -->
          <div class="card-pool" v-if="interventionCards.length > 0">
            <div
              v-for="card in interventionCards"
              :key="card.id"
              class="intervention-card"
              :class="{ selected: selectedCard?.id === card.id }"
              @click="selectInterventionCard(card)"
            >
              <div class="card-icon">{{ card.icon }}</div>
              <div class="card-body">
                <div class="card-name">{{ card.name }}</div>
                <div class="card-desc">{{ card.description }}</div>
                <div class="card-effect">{{ card.estimated_effect }}</div>
              </div>
            </div>
          </div>
          <div class="card-pool-loading" v-else-if="isLoadingCards">
            <span class="spinner-sm"></span>
            <span>正在生成干预策略卡片...</span>
          </div>
          <div class="card-pool-empty" v-else>
            <span class="empty-icon">📭</span>
            <span class="empty-text">干预卡片加载失败</span>
            <button class="btn-retry" @click="retryLoadCards">🔄 重新生成</button>
          </div>

          <!-- 分叉时间线控制区 -->
          <div class="branch-controls" v-if="selectedCard">
            <div class="control-row">
              <div class="control-group">
                <label>干预策略</label>
                <span class="control-value">{{ selectedCard.name }}</span>
              </div>
              <div class="control-group">
                <label>执行时间</label>
                <select v-model="interventionDay" class="day-select">
                  <option v-for="d in timeRange" :key="d" :value="d">第{{ d }}天</option>
                </select>
              </div>
              <button
                class="btn-branch"
                :disabled="isBranching"
                @click="generateBranchTimeline"
              >
                <span v-if="isBranching" class="spinner-sm"></span>
                <span v-else>🚀 生成分叉时间线</span>
              </button>
            </div>
          </div>

          <!-- 分叉时间线图表 -->
          <div class="branch-chart-container" v-if="branchTimeline.length > 0">
            <div class="branch-chart-header">
              <span class="branch-legend original">── 原始预测</span>
              <span class="branch-legend branch">- - 干预后预测</span>
            </div>
            <div class="branch-chart">
              <svg viewBox="0 0 700 220" class="branch-svg">
                <line v-for="n in 5" :key="'bh'+n" x1="50" :y1="n * 38" x2="670" :y2="n * 38" class="grid-line-light" />
                <text x="35" y="25" class="axis-label">100</text>
                <text x="40" y="110" class="axis-label">50</text>
                <text x="40" y="195" class="axis-label">0</text>

                <polygon :points="originalHeatAreaPoints" fill="url(#origGrad)" class="heat-area" />
                <polygon :points="branchHeatAreaPoints" fill="url(#branchGrad)" class="sentiment-area" />

                <polyline :points="originalHeatLinePoints" class="original-line" fill="none" />
                <polyline :points="branchHeatLinePoints" class="branch-line" fill="none" />

                <circle v-for="(pt, idx) in originalChartPoints" :key="'op'+idx" :cx="pt.x" :cy="pt.y" r="4" class="original-point" />
                <circle v-for="(pt, idx) in branchChartPoints" :key="'bp'+idx" :cx="pt.x" :cy="pt.y" r="4" class="branch-point" />

                <line v-if="interventionDay > 0"
                  :x1="getInterventionX" y1="10"
                  :x2="getInterventionX" y2="195"
                  class="intervention-line"
                />
                <text v-if="interventionDay > 0"
                  :x="getInterventionX" y="8"
                  class="intervention-label"
                  text-anchor="middle"
                >↓ 干预</text>

                <text v-for="(d, idx) in originalTimeline" :key="'bl'+idx"
                  :x="50 + idx * (620 / Math.max(originalTimeline.length - 1, 1))"
                  y="215" class="x-axis-label" text-anchor="middle"
                >D{{ d.day }}</text>

                <defs>
                  <linearGradient id="origGrad" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" style="stop-color:#3b82f6;stop-opacity:0.3" />
                    <stop offset="100%" style="stop-color:#3b82f6;stop-opacity:0.02" />
                  </linearGradient>
                  <linearGradient id="branchGrad" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" style="stop-color:#f59e0b;stop-opacity:0.3" />
                    <stop offset="100%" style="stop-color:#f59e0b;stop-opacity:0.02" />
                  </linearGradient>
                </defs>
              </svg>
            </div>

            <!-- 分叉对比指标 -->
            <div class="branch-comparison" v-if="branchComparison">
              <div class="comparison-item">
                <span class="comp-label">峰值热度变化</span>
                <span class="comp-value" :class="branchComparison.peak_heat_change > 0 ? 'up' : 'down'">
                  {{ branchComparison.peak_heat_change > 0 ? '+' : '' }}{{ branchComparison.peak_heat_change }}
                </span>
              </div>
              <div class="comparison-item">
                <span class="comp-label">情绪改善</span>
                <span class="comp-value" :class="branchComparison.avg_sentiment_change > 0 ? 'down' : 'up'">
                  {{ branchComparison.avg_sentiment_change > 0 ? '+' : '' }}{{ branchComparison.avg_sentiment_change }}
                </span>
              </div>
              <div class="comparison-item">
                <span class="comp-label">风险降级</span>
                <span class="comp-value">{{ branchComparison.risk_reduction }}</span>
              </div>
              <div class="comparison-item">
                <span class="comp-label">恢复加速</span>
                <span class="comp-value down">{{ branchComparison.recovery_speedup_days }}天</span>
              </div>
            </div>
            <div class="branch-analysis" v-if="branchAnalysis">
              <p>{{ branchAnalysis }}</p>
            </div>
          </div>

          <!-- 策略竞技场 + 时机热力图 -->
          <div class="sandbox-grid">
            <!-- 策略竞技场 -->
            <div class="arena-section">
              <h5 class="sub-title">🏟️ 策略竞技场</h5>
              <button
                class="btn-arena"
                :disabled="isComparing"
                @click="runStrategyCompare"
              >
                <span v-if="isComparing" class="spinner-sm"></span>
                <span v-else>⚔️ 启动策略对比</span>
              </button>
              <div class="arena-results" v-if="strategyComparisons.length > 0">
                <div
                  v-for="(comp, idx) in strategyComparisons"
                  :key="idx"
                  class="arena-card"
                  :class="{ best: comp.score === Math.max(...strategyComparisons.map(c => c.score)) }"
                >
                  <div class="arena-card-header">
                    <span class="arena-rank">#{{ idx + 1 }}</span>
                    <span class="arena-name">{{ comp.strategy_name }}</span>
                    <span class="arena-score">{{ comp.score }}分</span>
                  </div>
                  <div class="arena-metrics">
                    <div class="arena-metric">
                      <span class="am-label">热度</span>
                      <span class="am-value" :class="comp.heat_change > 0 ? 'up' : 'down'">{{ comp.heat_change > 0 ? '+' : '' }}{{ comp.heat_change }}%</span>
                    </div>
                    <div class="arena-metric">
                      <span class="am-label">情绪</span>
                      <span class="am-value" :class="comp.sentiment_change > 0 ? 'down' : 'up'">{{ comp.sentiment_change > 0 ? '+' : '' }}{{ comp.sentiment_change }}</span>
                    </div>
                    <div class="arena-metric">
                      <span class="am-label">风险</span>
                      <span class="am-value">{{ comp.risk_level === 'low' ? '低' : comp.risk_level === 'medium' ? '中' : '高' }}</span>
                    </div>
                  </div>
                  <p class="arena-analysis">{{ comp.analysis }}</p>
                </div>
              </div>
              <div class="arena-recommendation" v-if="strategyRecommendation">
                <span class="rec-icon">💡</span>
                <span>{{ strategyRecommendation }}</span>
              </div>
            </div>

            <!-- 时机热力图 -->
            <div class="heatmap-section">
              <h5 class="sub-title">🗺️ 干预时机热力图</h5>
              <button
                class="btn-heatmap"
                :disabled="isGeneratingHeatmap"
                @click="runHeatmapGeneration"
              >
                <span v-if="isGeneratingHeatmap" class="spinner-sm"></span>
                <span v-else>🗺️ 生成热力图</span>
              </button>
              <div class="heatmap-wrapper" v-if="heatmapData.length > 0">
                <div class="heatmap-canvas" ref="heatmapCanvas"></div>
                <div class="heatmap-explanation" v-if="heatmapExplanation">
                  <span class="explanation-icon">💡</span>
                  <span class="explanation-text">{{ heatmapExplanation }}</span>
                </div>
              </div>
              <div class="heatmap-loading" v-else-if="isGeneratingHeatmap">
                <div class="heatmap-loading-ring"></div>
                <span>正在计算干预时机矩阵...</span>
              </div>
            </div>
          </div>

          <!-- 反事实推演模块 -->
          <div class="counterfactual-section">
            <CounterfactualPanel
              :event-summary="eventSummary"
              :current-sentiment="currentSentiment"
              :time-range="timeRange"
              :simulation-run-data="simulationRunData"
              :prediction-data="predictionData"
              :intervention-cards="interventionCards"
              :original-timeline="originalTimeline"
              @add-log="(msg) => emit('add-log', msg)"
            />
          </div>
        </div>
      </div>
    </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { marked } from 'marked'
import * as d3 from 'd3'
import { predictPublicOpinion, simulateIntervention as apiSimulateIntervention, chatAboutPrediction, generateRecommendedQuestions, agentPredict, generateInterventionCards, generateInterventionTimeline, strategyCompare, generateInterventionHeatmap, generateCascadeEffect, generateCounterfactual, generateTimelineEvents, generateCounterfactualDAG } from '../api/prediction.js'
import CounterfactualPanel from './CounterfactualPanel.vue'
import { searchWithTavily } from '../api/tavily.js'
import { getRunStatusDetail } from '../api/simulation.js'
import { getReport } from '../api/report.js'
import { getProject } from '../api/graph.js'

const props = defineProps({
  reportId: String,
  simulationId: String,
  simulationConfig: Object,
  projectData: Object
})

const emit = defineEmits(['add-log', 'heatmapCellClick'])

// Agent模式状态
const useAgentMode = ref(true)
const agentLogs = ref([])
const agentStage = ref('')
const agentProgress = ref(0)
const agentMessage = ref('')
const currentThought = ref('')
const currentTool = ref('')
const expandedLogIndex = ref(null)

// 加载状态
const isAutoLoading = ref(false)
const isPredicting = ref(false)
const isSimulating = ref(false)
const isChatting = ref(false)
const loadingStep = ref('正在初始化...')
const loadingProgress = ref(0)

// 数据状态
const eventSummary = ref('')
const timeRange = ref(7)
const currentSentiment = ref('中性')
const predictionData = ref(null)
const interventionResult = ref(null)
const chatHistory = ref([])
const chatInput = ref('')
const interventionText = ref('')
const selectedIntervention = ref('')

// 🦋 蝴蝶效应沙盒状态
const interventionCards = ref([])
const selectedCard = ref(null)
const isLoadingCards = ref(false)
const interventionDay = ref(1)
const isBranching = ref(false)
const branchTimeline = ref([])
const branchComparison = ref(null)
const branchAnalysis = ref('')
const isComparing = ref(false)
const strategyComparisons = ref([])
const strategyRecommendation = ref('')
const isGeneratingHeatmap = ref(false)
const heatmapData = ref([])
const heatmapCanvas = ref(null)
const heatmapExplanation = ref('')
const heatmapSelectedCell = ref(null)
const isGeneratingCascade = ref(false)
const cascadeLayers = ref([])
const cascadeTotalReach = ref(0)
const cascadeSpeed = ref('')
const isGeneratingCF = ref(false)
const cfRemovedDay = ref('')
const cfResult = ref(null)

// 真实数据存储
const simulationRunData = ref(null)
const reportData = ref(null)
const projectDetail = ref(null)
const roundHeatData = ref([])

// Tavily搜索结果
const tavilyResults = ref(null)
const tavilySearchQuery = ref('')

// 推荐问题
const recommendedQuestions = ref([])
const isGeneratingQuestions = ref(false)

// 情绪分布数据（基于真实模拟数据计算）
const sentimentDistribution = ref([
  { type: 'positive', label: '正面', percentage: 25, count: 0 },
  { type: 'neutral', label: '中性', percentage: 35, count: 0 },
  { type: 'negative', label: '负面', percentage: 30, count: 0 },
  { type: 'complex', label: '复杂', percentage: 10, count: 0 }
])

// LLM生成的timeline事件
const llmTimelineEvents = ref([])
const isLoadingTimelineEvents = ref(false)

// 计算属性
const sentimentClass = computed(() => {
  const map = { '正面': 'positive', '中性': 'neutral', '负面': 'negative', '复杂': 'complex' }
  return map[currentSentiment.value] || 'neutral'
})

const overallRisk = computed(() => {
  const highRiskCount = roundHeatData.value.filter(r => r.risk === 'high').length
  if (highRiskCount >= 3) return '高'
  if (highRiskCount >= 1) return '中高'
  return '低'
})

const riskClass = computed(() => {
  const risk = overallRisk.value
  if (risk === '高') return 'high'
  if (risk === '中高') return 'medium'
  return 'low'
})

const currentRoundRisk = computed(() => {
  if (roundHeatData.value.length === 0) return 'medium'
  return roundHeatData.value[roundHeatData.value.length - 1]?.risk || 'medium'
})

const roundInsightText = computed(() => {
  const lastRound = roundHeatData.value[roundHeatData.value.length - 1]
  if (!lastRound) return '暂无数据'

  if (lastRound.risk === 'high') {
    return '话题进入高风险讨论阶段，需要密切关注舆情走向'
  } else if (lastRound.risk === 'medium') {
    return '话题保持活跃讨论，情绪趋于稳定'
  } else {
    return '话题进入长尾讨论阶段，公众关注度逐渐降低'
  }
})

// 按5轮为单位聚合数据
const groupedRoundData = computed(() => {
  // 优先从 step2 的 time_config 计算轮数（必须按照step2来）
  let totalRounds = 15 // 默认15轮
  const timeConfig = props.simulationConfig?.time_config
  if (timeConfig?.total_simulation_hours && timeConfig?.minutes_per_round) {
    totalRounds = Math.floor((timeConfig.total_simulation_hours * 60) / timeConfig.minutes_per_round)
  }
  // 确保至少15轮
  totalRounds = Math.max(15, totalRounds)
  
  if (simulationRunData.value?.all_actions?.length) {
    const actions = simulationRunData.value.all_actions
    const roundMap = new Map()
    
    // 统计每轮的动作数
    actions.forEach(action => {
      const round = action.round_num || 1
      if (!roundMap.has(round)) {
        roundMap.set(round, { count: 0, actions: [] })
      }
      roundMap.get(round).count++
      roundMap.get(round).actions.push(action)
    })
    
    // 获取所有轮次并排序
    const allRounds = Array.from(roundMap.entries()).sort((a, b) => a[0] - b[0])
    
    // 计算最大动作数用于热度标准化
    const maxCount = Math.max(...allRounds.map(([, d]) => d.count), 1)
    
    // 按5轮分组，显示所有区间（包括无数据的）
    const groups = []
    for (let start = 1; start <= totalRounds; start += 5) {
      const end = Math.min(start + 4, totalRounds)
      const roundsInGroup = allRounds.filter(([r]) => r >= start && r <= end)
      
      const totalActions = roundsInGroup.reduce((sum, [, data]) => sum + data.count, 0)
      
      // 计算热度：有数据则按数据计算，无数据则为0
      let heat = 0
      if (roundsInGroup.length > 0) {
        // 基于该组的动作密度计算热度
        const density = totalActions / (roundsInGroup.length * maxCount)
        heat = Math.min(100, Math.round(density * 100))
      }
      
      let risk = 'low'
      if (heat > 70) risk = 'high'
      else if (heat > 40) risk = 'medium'
      
      groups.push({
        startRound: start,
        endRound: end,
        label: `R${start}-${end}`,
        heat,
        risk,
        actionCount: totalActions,
        roundCount: roundsInGroup.length,
        hasData: roundsInGroup.length > 0
      })
    }
    
    return groups
  } else if (roundHeatData.value.length > 0) {
    // 使用 roundHeatData 作为备用数据
    const groups = []
    
    for (let start = 1; start <= totalRounds; start += 5) {
      const end = Math.min(start + 4, totalRounds)
      const roundsInGroup = roundHeatData.value.filter(r => r.round >= start && r.round <= end)
      
      if (roundsInGroup.length > 0) {
        const avgHeat = Math.round(roundsInGroup.reduce((sum, r) => sum + r.heat, 0) / roundsInGroup.length)
        let risk = 'low'
        if (avgHeat > 70) risk = 'high'
        else if (avgHeat > 40) risk = 'medium'
        
        groups.push({
          startRound: start,
          endRound: end,
          label: `R${start}-${end}`,
          heat: avgHeat,
          risk,
          actionCount: roundsInGroup.length,
          roundCount: roundsInGroup.length,
          hasData: true
        })
      } else {
        groups.push({
          startRound: start,
          endRound: end,
          label: `R${start}-${end}`,
          heat: 0,
          risk: 'low',
          actionCount: 0,
          roundCount: 0,
          hasData: false
        })
      }
    }
    
    return groups
  }
  
  return []
})

// 折线图的点坐标
const groupedRoundPoints = computed(() => {
  const data = groupedRoundData.value
  if (data.length === 0) return []

  const stepX = data.length > 1 ? 430 / (data.length - 1) : 0

  return data.map((group, idx) => ({
    x: 50 + idx * stepX,
    y: 175 - (group.heat / 100) * 165,
    heat: group.heat,
    risk: group.risk,
    label: group.label,
    hasData: group.hasData
  }))
})

// 有数据部分的折线
const groupedRoundLinePoints = computed(() => {
  const points = groupedRoundPoints.value
  if (points.length === 0) return ''

  // 只连接有数据或热度>0的点
  const segments = []
  let currentSegment = []

  points.forEach((p, idx) => {
    if (p.hasData || p.heat > 0) {
      currentSegment.push(`${p.x},${p.y}`)
    } else {
      if (currentSegment.length > 0) {
        segments.push(currentSegment.join(' '))
        currentSegment = []
      }
    }
  })

  if (currentSegment.length > 0) {
    segments.push(currentSegment.join(' '))
  }

  return segments
})

// 预测趋势线（虚线）- 连接最后一个数据点到未来
const trendLinePoints = computed(() => {
  const points = groupedRoundPoints.value
  if (points.length === 0) return ''

  // 找到最后一个有数据的点
  const lastDataIdx = points.reduce((last, p, idx) => p.hasData ? idx : last, -1)
  if (lastDataIdx < 0 || lastDataIdx === points.length - 1) return ''

  const lastPoint = points[lastDataIdx]
  const nextPoint = points[lastDataIdx + 1]

  return `${lastPoint.x},${lastPoint.y} ${nextPoint.x},${nextPoint.y}`
})

// 峰值轮次范围
const peakRoundRange = computed(() => {
  const data = groupedRoundData.value
  if (data.length === 0) return '1-5'
  
  const peak = data.reduce((max, g) => g.heat > max.heat ? g : max, data[0])
  return `${peak.startRound}-${peak.endRound}`
})

// 平均热度
const avgGroupedHeat = computed(() => {
  const data = groupedRoundData.value
  if (data.length === 0) return 0
  return Math.round(data.reduce((sum, g) => sum + g.heat, 0) / data.length)
})

// 当前阶段风险
const currentGroupRisk = computed(() => {
  const data = groupedRoundData.value
  if (data.length === 0) return 'low'
  return data[data.length - 1]?.risk || 'low'
})

const currentGroupRiskText = computed(() => {
  const risk = currentGroupRisk.value
  return risk === 'high' ? '高风险' : risk === 'medium' ? '中风险' : '低风险'
})

// ============================================
// 合并图表计算属性（轮次热度 + 多维趋势）
// ============================================

// 合并图表的X轴基于5轮分组数据
const mergedChartData = computed(() => {
  const groups = groupedRoundData.value
  if (groups.length === 0) return []
  
  // 为每个5轮分组创建情绪代理数据（基于风险等级）
  return groups.map((group, idx) => {
    let sentimentProxy = 50 // 默认中性
    if (group.risk === 'high') sentimentProxy = 30
    else if (group.risk === 'medium') sentimentProxy = 45
    else sentimentProxy = 65
    
    return {
      idx,
      label: group.label,
      heat: group.heat,
      sentiment: sentimentProxy,
      risk: group.risk,
      hasData: group.hasData,
      actionCount: group.actionCount
    }
  })
})

// 合并图表点坐标
const mergedChartPoints = computed(() => {
  const data = mergedChartData.value
  if (data.length === 0) return { heat: [], sentiment: [] }
  
  const width = 700
  const height = 200
  const paddingLeft = 50
  const paddingRight = 30
  const paddingTop = 20
  const paddingBottom = 30
  const chartWidth = width - paddingLeft - paddingRight
  const chartHeight = height - paddingTop - paddingBottom
  
  const stepX = data.length > 1 ? chartWidth / (data.length - 1) : 0
  
  const heatPoints = data.map((d, i) => ({
    x: paddingLeft + i * stepX,
    y: paddingTop + chartHeight - (d.heat / 100) * chartHeight,
    heat: d.heat,
    risk: d.risk,
    label: d.label,
    hasData: d.hasData
  }))
  
  const sentimentPoints = data.map((d, i) => ({
    x: paddingLeft + i * stepX,
    y: paddingTop + chartHeight - (d.sentiment / 100) * chartHeight,
    sentiment: d.sentiment,
    label: d.label
  }))
  
  return { heat: heatPoints, sentiment: sentimentPoints }
})

// 合并图表热度折线
const mergedHeatLinePoints = computed(() => {
  const points = mergedChartPoints.value.heat
  if (points.length === 0) return ''
  return points.map(p => `${p.x},${p.y}`).join(' ')
})

// 合并图表情绪折线
const mergedSentimentLinePoints = computed(() => {
  const points = mergedChartPoints.value.sentiment
  if (points.length === 0) return ''
  return points.map(p => `${p.x},${p.y}`).join(' ')
})

// 合并图表热度区域填充
const mergedHeatAreaPoints = computed(() => {
  const points = mergedChartPoints.value.heat
  if (points.length === 0) return ''
  
  const height = 200
  const paddingBottom = 30
  const baseline = height - paddingBottom
  
  const linePoints = points.map(p => `${p.x},${p.y}`).join(' ')
  return `${points[0].x},${baseline} ${linePoints} ${points[points.length - 1].x},${baseline}`
})

// 合并图表情绪区域填充
const mergedSentimentAreaPoints = computed(() => {
  const points = mergedChartPoints.value.sentiment
  if (points.length === 0) return ''
  
  const height = 200
  const paddingBottom = 30
  const baseline = height - paddingBottom
  
  const linePoints = points.map(p => `${p.x},${p.y}`).join(' ')
  return `${points[0].x},${baseline} ${linePoints} ${points[points.length - 1].x},${baseline}`
})

// 雷达图数据
const radarLabels = [
  { text: '传播力', style: { top: '0', left: '50%', transform: 'translateX(-50%)' } },
  { text: '影响力', style: { top: '25%', right: '0' } },
  { text: '持续度', style: { bottom: '25%', right: '0' } },
  { text: '可控性', style: { bottom: '0', left: '50%', transform: 'translateX(-50%)' } },
  { text: '敏感度', style: { bottom: '25%', left: '0' } }
]

const radarAxes = computed(() => {
  const angles = [0, 72, 144, 216, 288].map(a => (a - 90) * Math.PI / 180)
  return angles.map(angle => ({
    x: 100 + 80 * Math.cos(angle),
    y: 100 + 80 * Math.sin(angle)
  }))
})

const radarData = computed(() => {
  // 基于真实数据计算雷达图数值
  const avgHeat = predictionData.value?.stats?.avgHeat || 50
  const maxHeat = predictionData.value?.stats?.maxHeat || 70
  const riskNodes = predictionData.value?.stats?.riskNodes || 2
  const sentimentScore = sentimentDistribution.value.find(s => s.type === 'positive')?.percentage || 30

  const values = [
    Math.min(100, avgHeat + 20), // 传播力
    Math.min(100, maxHeat), // 影响力
    Math.min(100, timeRange.value * 3), // 持续度
    Math.max(20, 100 - riskNodes * 20), // 可控性
    Math.min(100, 100 - sentimentScore + 30) // 敏感度
  ]

  const angles = [0, 72, 144, 216, 288].map(a => (a - 90) * Math.PI / 180)
  return values.map((val, idx) => ({
    x: 100 + (val / 100) * 80 * Math.cos(angles[idx]),
    y: 100 + (val / 100) * 80 * Math.sin(angles[idx]),
    value: val
  }))
})

const radarDataPoints = computed(() => {
  return radarData.value.map(p => `${p.x},${p.y}`).join(' ')
})

// ============================================
// 🦋 蝴蝶效应沙盒计算属性
// ============================================

const originalTimeline = computed(() => {
  return predictionData.value?.timeline || []
})

const originalChartPoints = computed(() => {
  const tl = originalTimeline.value
  if (tl.length === 0) return []
  const step = 620 / Math.max(tl.length - 1, 1)
  return tl.map((t, i) => ({
    x: 50 + i * step,
    y: 190 - (t.heat / 100) * 180
  }))
})

const originalHeatLinePoints = computed(() => {
  return originalChartPoints.value.map(p => `${p.x},${p.y}`).join(' ')
})

const originalHeatAreaPoints = computed(() => {
  const pts = originalChartPoints.value
  if (pts.length === 0) return ''
  const first = pts[0]
  const last = pts[pts.length - 1]
  return `${first.x},190 ` + pts.map(p => `${p.x},${p.y}`).join(' ') + ` ${last.x},190`
})

const branchChartPoints = computed(() => {
  const tl = branchTimeline.value
  if (tl.length === 0) return []
  const step = 620 / Math.max(tl.length - 1, 1)
  return tl.map((t, i) => ({
    x: 50 + i * step,
    y: 190 - (t.heat / 100) * 180
  }))
})

const branchHeatLinePoints = computed(() => {
  return branchChartPoints.value.map(p => `${p.x},${p.y}`).join(' ')
})

const branchHeatAreaPoints = computed(() => {
  const pts = branchChartPoints.value
  if (pts.length === 0) return ''
  const first = pts[0]
  const last = pts[pts.length - 1]
  return `${first.x},190 ` + pts.map(p => `${p.x},${p.y}`).join(' ') + ` ${last.x},190`
})

const getInterventionX = computed(() => {
  const tl = originalTimeline.value
  if (tl.length === 0 || interventionDay.value <= 0) return 50
  const step = 620 / Math.max(tl.length - 1, 1)
  const idx = tl.findIndex(t => t.day >= interventionDay.value)
  if (idx < 0) return 50 + (tl.length - 1) * step
  return 50 + idx * step
})

const heatmapDays = computed(() => {
  if (heatmapData.value.length === 0 || heatmapData.value[0]?.scores?.length === 0) return []
  return heatmapData.value[0].scores.map(s => s.day)
})

const removableEvents = computed(() => {
  const tl = originalTimeline.value
  if (!tl || tl.length === 0) return []
  return tl.map(t => ({
    ...t,
    event: t.event || `第${t.day}天舆情节点`
  }))
})

const getHeatmapColor = (score) => {
  if (score >= 80) return '#22c55e'
  if (score >= 60) return '#84cc16'
  if (score >= 40) return '#eab308'
  if (score >= 20) return '#f97316'
  return '#ef4444'
}

const getHeatmapClass = (score) => {
  if (score >= 80) return 'excellent'
  if (score >= 60) return 'good'
  if (score >= 40) return 'average'
  if (score >= 20) return 'poor'
  return 'danger'
}

const getRadarGridPoints = (level) => {
  const radius = (level / 5) * 80
  const angles = [0, 72, 144, 216, 288].map(a => (a - 90) * Math.PI / 180)
  return angles.map(angle => {
    const x = 100 + radius * Math.cos(angle)
    const y = 100 + radius * Math.sin(angle)
    return `${x},${y}`
  }).join(' ')
}

// 趋势图数据点
const heatTrendPoints = computed(() => {
  if (!predictionData.value?.timeline?.length) return ''
  const timeline = predictionData.value.timeline
  const step = 340 / (timeline.length - 1 || 1)
  const offsetX = 40
  return timeline.map((t, i) => `${offsetX + i * step},${160 - t.heat * 1.4}`).join(' ')
})

const sentimentTrendPoints = computed(() => {
  if (!predictionData.value?.timeline?.length) return ''
  const timeline = predictionData.value.timeline
  const step = 340 / (timeline.length - 1 || 1)
  const offsetX = 40
  return timeline.map((t, i) => `${offsetX + i * step},${160 - (t.sentiment * 100) * 1.4}`).join(' ')
})

// 区域填充点（用于渐变填充）
const heatAreaPoints = computed(() => {
  if (!predictionData.value?.timeline?.length) return ''
  const timeline = predictionData.value.timeline
  const step = 340 / (timeline.length - 1 || 1)
  const offsetX = 40
  const points = timeline.map((t, i) => `${offsetX + i * step},${160 - t.heat * 1.4}`)
  return `${offsetX},160 ` + points.join(' ') + ` ${offsetX + (timeline.length - 1) * step},160`
})

const sentimentAreaPoints = computed(() => {
  if (!predictionData.value?.timeline?.length) return ''
  const timeline = predictionData.value.timeline
  const step = 340 / (timeline.length - 1 || 1)
  const offsetX = 40
  const points = timeline.map((t, i) => `${offsetX + i * step},${160 - (t.sentiment * 100) * 1.4}`)
  return `${offsetX},160 ` + points.join(' ') + ` ${offsetX + (timeline.length - 1) * step},160`
})

// 数据点坐标
const heatDataPoints = computed(() => {
  if (!predictionData.value?.timeline?.length) return []
  const timeline = predictionData.value.timeline
  const step = 340 / (timeline.length - 1 || 1)
  const offsetX = 40
  return timeline.map((t, i) => ({
    x: offsetX + i * step,
    y: 160 - t.heat * 1.4
  }))
})

const sentimentDataPoints = computed(() => {
  if (!predictionData.value?.timeline?.length) return []
  const timeline = predictionData.value.timeline
  const step = 340 / (timeline.length - 1 || 1)
  const offsetX = 40
  return timeline.map((t, i) => ({
    x: offsetX + i * step,
    y: 160 - (t.sentiment * 100) * 1.4
  }))
})

// 风险标记线
const riskLines = computed(() => {
  if (!predictionData.value?.warnings?.length) return []
  const warnings = predictionData.value.warnings.filter(w => w.level === 'high')
  const timeline = predictionData.value.timeline
  if (!timeline?.length) return []
  const step = 340 / (timeline.length - 1 || 1)
  const offsetX = 40
  return warnings.map((w, i) => ({
    x: offsetX + ((w.day - 1) / (timeRange.value - 1 || 1)) * (timeline.length - 1) * step
  }))
})

// 工具函数
const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms))

// Agent辅助函数
const getStageText = (stage) => {
  const stageMap = {
    'pending': '⏳ 等待开始',
    'planning': '📋 规划预测策略',
    'analyzing': '🔍 深度分析中',
    'predicting': '📊 生成预测结果',
    'reflecting': '🤔 反思与总结',
    'completed': '✅ 预测完成'
  }
  return stageMap[stage] || stage
}

const getActionText = (action) => {
  const actionMap = {
    'prediction_start': '🚀 启动',
    'planning_start': '📋 开始规划',
    'planning_thought': '💭 规划思考',
    'planning_complete': '✅ 规划完成',
    'module_start': '🔧 开始模块分析',
    'react_thought': '🧠 ReACT思考',
    'tool_call': '⚡ 调用工具',
    'tool_result': '📥 工具返回',
    'llm_response': '🤖 LLM响应',
    'module_complete': '✅ 模块完成',
    'reflection_start': '🤔 开始反思',
    'reflection_result': '📝 反思结果',
    'prediction_complete': '🎉 预测完成',
    'error': '❌ 错误'
  }
  return actionMap[action] || action
}

// 组件挂载时初始化数据
onMounted(async () => {
  console.log('Step5 mounted, predictionData:', predictionData.value)
  // 强制初始化，确保页面有数据展示
  await autoInitialize()
})

// 监听配置变化
watch(() => props.simulationConfig, async (newConfig) => {
  if (newConfig && !eventSummary.value) {
    await autoInitialize()
  }
}, { immediate: true })

// 监听 simulationId 变化，重新获取模拟数据
watch(
  () => props.simulationId,
  async (newSimulationId) => {
    if (newSimulationId) {
      try {
        const runRes = await getRunStatusDetail(newSimulationId)
        if (runRes.success && runRes.data) {
          simulationRunData.value = runRes.data
          calculateRoundHeatData(runRes.data.all_actions || [])
          emit('add-log', `已加载模拟运行数据: ${runRes.data.all_actions?.length || 0}条动作`)
          // 重新分析情绪分布
          await analyzeSentimentFromRealData()
        }
      } catch (e) {
        console.log('获取模拟运行数据失败:', e.message)
        emit('add-log', `获取模拟运行数据失败: ${e.message}`)
      }
    }
  },
  { immediate: false }
)

// 自动初始化数据 - 基于前四步真实数据（直接生成预测结果，不显示加载状态）
const autoInitialize = async () => {
  console.log('autoInitialize started')
  try {
    // 步骤1: 获取项目详情
    if (props.projectData?.project_id) {
      try {
        const projectRes = await getProject(props.projectData.project_id)
        if (projectRes.success) {
          projectDetail.value = projectRes.data
        }
      } catch (e) {
        console.log('获取项目详情失败:', e.message)
      }
    }

    // 步骤2: 获取模拟运行数据
    if (props.simulationId) {
      try {
        const runRes = await getRunStatusDetail(props.simulationId)
        if (runRes.success && runRes.data) {
          simulationRunData.value = runRes.data
          calculateRoundHeatData(runRes.data.all_actions || [])
        }
      } catch (e) {
        console.log('获取模拟运行数据失败:', e.message)
      }
    }

    // 步骤3: 获取报告数据
    if (props.reportId) {
      try {
        const reportRes = await getReport(props.reportId)
        if (reportRes.success && reportRes.data) {
          reportData.value = reportRes.data
          if (reportRes.data.outline?.summary) {
            eventSummary.value = reportRes.data.outline.summary
          } else if (reportRes.data.outline?.title) {
            eventSummary.value = reportRes.data.outline.title
          }
        }
      } catch (e) {
        console.log('获取报告数据失败:', e.message)
      }
    }

    // 设置默认事件摘要
    if (!eventSummary.value) {
      let searchQuery = ''
      if (props.simulationConfig?.simulation_requirement) {
        searchQuery = props.simulationConfig.simulation_requirement
      } else if (props.projectData?.simulation_requirement) {
        searchQuery = props.projectData.simulation_requirement
      } else if (props.projectData?.analysis_summary) {
        searchQuery = props.projectData.analysis_summary
      } else if (props.projectData?.project_name) {
        searchQuery = props.projectData.project_name
      }
      eventSummary.value = searchQuery || '基于当前模拟环境的舆情预测分析'
    }

    // 步骤4: Tavily搜索补充信息
    if (eventSummary.value && eventSummary.value.length > 5) {
      try {
        const tavilyRes = await searchWithTavily({
          query: eventSummary.value.slice(0, 100),
          search_depth: 'basic',
          topic: 'news',
          max_results: 5
        })
        if (tavilyRes.success && tavilyRes.data) {
          tavilyResults.value = tavilyRes.data
        }
      } catch (e) {
        console.log('Tavily搜索失败:', e.message)
      }
    }

    // 步骤5: 计算预测时间范围
    const storedTotalRounds = simulationRunData.value?.total_rounds
    const timeConfig = props.simulationConfig?.time_config
    let calculatedRounds = 0
    if (timeConfig?.total_simulation_hours && timeConfig?.minutes_per_round) {
      calculatedRounds = Math.floor((timeConfig.total_simulation_hours * 60) / timeConfig.minutes_per_round)
    }

    const maxRounds = storedTotalRounds || calculatedRounds || 48
    timeRange.value = Math.max(7, Math.min(30, Math.ceil(maxRounds / 4)))

    // 步骤6: 基于真实数据计算情绪分布
    await analyzeSentimentFromRealData()

    // 设置当前情绪
    if (sentimentDistribution.value.length > 0) {
      const maxSentiment = sentimentDistribution.value.reduce((prev, current) =>
        prev.percentage > current.percentage ? prev : current
      )
      currentSentiment.value = maxSentiment.label
    } else {
      currentSentiment.value = '中性'
    }

    // 直接生成预测数据，不显示加载状态
    console.log('Generating prediction data...')

    // 🦋 先加载LLM生成的时间线事件
    await loadTimelineEvents()

    predictionData.value = generateMockPredictionData()
    recommendedQuestions.value = generateDefaultQuestions()
    console.log('Prediction data generated:', predictionData.value)

    // 🦋 加载干预策略卡片（需要等待完成）
    await loadInterventionCards()

  } catch (error) {
    console.error('初始化失败:', error)
    // 出错时也直接生成模拟数据，确保页面能显示
    eventSummary.value = eventSummary.value || '舆情预测分析'
    currentSentiment.value = '中性'
    predictionData.value = generateMockPredictionData()
    recommendedQuestions.value = generateDefaultQuestions()
    console.log('Fallback prediction data generated')
  }
}

// 计算轮次热度数据
const calculateRoundHeatData = (actions) => {
  // 优先从 step2 的 time_config 计算轮数（必须按照step2来）
  let roundCount = 15 // 默认15轮
  const timeConfig = props.simulationConfig?.time_config
  if (timeConfig?.total_simulation_hours && timeConfig?.minutes_per_round) {
    roundCount = Math.floor((timeConfig.total_simulation_hours * 60) / timeConfig.minutes_per_round)
  }
  // 确保至少15轮
  roundCount = Math.max(15, roundCount)
  
  if (!actions || actions.length === 0) {
    roundHeatData.value = Array.from({ length: roundCount }, (_, i) => ({
      round: i + 1,
      heat: 50 + Math.floor(Math.random() * 30),
      risk: 'medium'
    }))
    return
  }

  const roundMap = new Map()
  actions.forEach(action => {
    const round = action.round_num || 1
    if (!roundMap.has(round)) {
      roundMap.set(round, { count: 0, actions: [] })
    }
    roundMap.get(round).count++
    roundMap.get(round).actions.push(action)
  })

  const rounds = Array.from(roundMap.entries())
    .sort((a, b) => a[0] - b[0])
    .slice(0, 12)

  const maxCount = Math.max(...rounds.map(r => r[1].count), 1)

  roundHeatData.value = rounds.map(([round, data]) => {
    const heat = Math.min(100, Math.round((data.count / maxCount) * 100))
    let risk = 'low'
    if (heat > 75) risk = 'high'
    else if (heat > 50) risk = 'medium'

    return {
      round,
      heat,
      risk,
      actionCount: data.count
    }
  })
}

// 基于真实模拟数据计算情绪分布
const analyzeSentimentFromRealData = async () => {
  const actions = simulationRunData.value?.all_actions || []

  if (actions.length === 0) {
    sentimentDistribution.value = [
      { type: 'positive', label: '正面', percentage: 25, count: 0 },
      { type: 'neutral', label: '中性', percentage: 35, count: 0 },
      { type: 'negative', label: '负面', percentage: 30, count: 0 },
      { type: 'complex', label: '复杂', percentage: 10, count: 0 }
    ]
    return
  }

  let positive = 0, neutral = 0, negative = 0, complex = 0

  actions.forEach(action => {
    const content = (action.content || '').toLowerCase()
    const actionType = (action.action_type || '').toLowerCase()

    const positiveWords = ['good', 'great', 'excellent', '支持', '赞同', '喜欢', '优秀', '棒', '好']
    const negativeWords = ['bad', 'terrible', '反对', '批评', '不满', '糟糕', '差', '坏', '愤怒']
    const complexWords = ['but', 'however', '虽然', '但是', '不过', '复杂', '矛盾']

    let hasPositive = positiveWords.some(w => content.includes(w))
    let hasNegative = negativeWords.some(w => content.includes(w))
    let hasComplex = complexWords.some(w => content.includes(w))

    if (actionType.includes('like') || actionType.includes('follow') || actionType.includes('share')) {
      hasPositive = true
    } else if (actionType.includes('unfollow') || actionType.includes('block') || actionType.includes('report')) {
      hasNegative = true
    }

    if (hasComplex || (hasPositive && hasNegative)) {
      complex++
    } else if (hasPositive) {
      positive++
    } else if (hasNegative) {
      negative++
    } else {
      neutral++
    }
  })

  const total = actions.length
  sentimentDistribution.value = [
    { type: 'positive', label: '正面', percentage: Math.round((positive / total) * 100), count: positive },
    { type: 'neutral', label: '中性', percentage: Math.round((neutral / total) * 100), count: neutral },
    { type: 'negative', label: '负面', percentage: Math.round((negative / total) * 100), count: negative },
    { type: 'complex', label: '复杂', percentage: Math.round((complex / total) * 100), count: complex }
  ]
}

// 生成基于真实数据的预测数据
const generateMockPredictionData = () => {
  const sentimentMap = {}
  sentimentDistribution.value.forEach(s => {
    sentimentMap[s.type] = s.percentage
  })

  const positivePct = sentimentMap['positive'] || 25
  const negativePct = sentimentMap['negative'] || 30
  const neutralPct = sentimentMap['neutral'] || 35

  const optimisticProb = Math.min(40, Math.max(15, positivePct + 5))
  const pessimisticProb = Math.min(40, Math.max(15, negativePct + 5))
  const baselineProb = 100 - optimisticProb - pessimisticProb

  const scenarios = [
    {
      name: '平稳过渡',
      probability: baselineProb,
      description: '公众注意力逐步转移，讨论趋于理性，舆情平稳着陆',
      risk_level: 'low',
      timeline: '3-5天热度维持'
    },
    {
      name: '品牌修复',
      probability: pessimisticProb,
      description: '品牌形象受损后进入修复期，需主动沟通重建信任',
      risk_level: 'low',
      timeline: '3-5天影响窗口'
    },
    {
      name: '口碑恶化',
      probability: Math.floor(optimisticProb * 0.6),
      description: '负面评价持续扩散，用户信任度下降，需紧急应对',
      risk_level: 'high',
      timeline: '1周内影响窗口'
    },
    {
      name: '竞品借势',
      probability: Math.floor(neutralPct * 0.4),
      description: '竞争对手借机营销，分流用户关注，市场竞争加剧',
      risk_level: 'medium',
      timeline: '1周内关键期'
    }
  ].sort((a, b) => b.probability - a.probability)

  const timeline = []
  const days = timeRange.value
  const heatData = roundHeatData.value

  const timelineEvents = llmTimelineEvents.value.length > 0 
    ? llmTimelineEvents.value 
    : [
        '事件初始发酵，社交媒体开始传播',
        '话题热度上升，KOL参与讨论',
        '主流媒体介入报道，舆论扩大',
        '官方首次回应，公众情绪分化',
        '讨论进入深水区，多方观点碰撞',
        '舆情达到峰值，关注度高',
        '话题开始降温，讨论趋于理性',
        '舆论逐渐平息，进入长尾阶段'
      ]

  if (heatData.length > 0) {
    heatData.forEach((round, idx) => {
      const day = Math.ceil((idx + 1) * days / heatData.length)
      const eventIdx = Math.min(idx, timelineEvents.length - 1)
      const eventText = timelineEvents[eventIdx]?.event || timelineEvents[eventIdx] || `第${round.round}轮模拟节点`
      const riskHint = timelineEvents[eventIdx]?.risk_hint || ''
      const riskText = round.risk === 'high' ? '【高风险】' : round.risk === 'medium' ? '【中风险】' : ''
      timeline.push({
        day,
        heat: round.heat,
        sentiment: (sentimentMap['positive'] || 30) / 100,
        event: riskHint ? `${riskHint} ${eventText}` : `${riskText}${eventText}`,
        risk: round.risk,
        actionCount: round.actionCount
      })
    })
  } else {
    for (let i = 0; i < Math.min(days, 7); i++) {
      const day = i + 1
      const heat = Math.floor(40 + Math.sin(i * 0.8) * 30 + Math.random() * 20)
      const risk = heat > 75 ? 'high' : heat > 50 ? 'medium' : 'low'
      const eventIdx = Math.min(i, timelineEvents.length - 1)
      const eventText = timelineEvents[eventIdx]?.event || timelineEvents[eventIdx] || `第${day}天舆情发展节点`
      const riskHint = timelineEvents[eventIdx]?.risk_hint || ''
      const riskText = risk === 'high' ? '【高风险】' : risk === 'medium' ? '【中风险】' : ''
      timeline.push({
        day,
        heat,
        sentiment: positivePct / 100,
        event: riskHint ? `${riskHint} ${eventText}` : `${riskText}${eventText}`,
        risk
      })
    }
  }

  const avgHeat = Math.round(timeline.reduce((sum, t) => sum + t.heat, 0) / timeline.length)
  const maxHeat = Math.max(...timeline.map(t => t.heat))
  const riskNodes = timeline.filter(t => t.risk === 'high').length

  const dominantScenario = scenarios[0]
  const actionCount = simulationRunData.value?.all_actions?.length || 0
  
  let conclusion
  if (actionCount > 0) {
    conclusion = `基于${actionCount}条真实模拟数据分析，预测"${dominantScenario.name}"最可能发生（${dominantScenario.probability}%），当前情绪以${currentSentiment.value}为主，需关注${riskNodes}个关键风险节点。`
  } else {
    // 当没有真实模拟数据时，使用LLM生成更自然的结论
    conclusion = `综合分析预测，"${dominantScenario.name}"情景最可能发生（${dominantScenario.probability}%），当前情绪以${currentSentiment.value}为主，存在${riskNodes}个关键风险节点需要重点关注。`
  }

  const warnings = []
  const highRiskRounds = heatData.filter(r => r.risk === 'high')
  if (highRiskRounds.length > 0) {
    highRiskRounds.slice(0, 2).forEach((round, idx) => {
      warnings.push({
        day: Math.ceil(round.round * days / (heatData.length || 7)),
        type: idx === 0 ? '热度峰值' : '情绪拐点',
        level: round.risk,
        description: `第${round.round}轮出现高热度活动（${round.heat}）`,
        suggestion: idx === 0 ? '提前准备应对预案，监控舆情走向' : '加强正面引导，及时澄清误解'
      })
    })
  }

  return {
    event_summary: eventSummary.value,
    current_sentiment: currentSentiment.value,
    engine_mode: 'hybrid',
    generated_at: new Date().toISOString(),
    conclusion,
    scenario_summary: `综合分析显示，"${dominantScenario.name}"发生概率最高，但需防范负面情景的触发因素`,
    scenarios,
    timeline,
    warnings,
    stats: {
      avgHeat,
      maxHeat,
      trend: avgHeat > 60 ? '上升' : avgHeat < 40 ? '下降' : '平稳',
      riskNodes
    }
  }
}

// 开始自动预测
const startAutoPrediction = async () => {
  isPredicting.value = true
  agentLogs.value = []
  agentStage.value = 'planning'
  agentProgress.value = 0
  agentMessage.value = '正在初始化预测Agent...'

  try {
    emit('add-log', `开始舆情预测: ${eventSummary.value.slice(0, 50)}...`)

    if (useAgentMode.value) {
      const res = await agentPredict({
        simulation_id: props.simulationId || 'manual',
        event_summary: eventSummary.value,
        current_sentiment: currentSentiment.value,
        time_range: timeRange.value,
        simulation_data: {
          all_actions: simulationRunData.value?.all_actions || [],
          agent_count: simulationRunData.value?.agent_count || 0
        }
      })

      if (res.success) {
        predictionData.value = res.data
        agentStage.value = 'completed'
        agentMessage.value = '预测完成'
        emit('add-log', `舆情预测完成 (置信度: ${Math.round((res.data.confidence || 0.8) * 100)}%)`)
        
        if (res.data.key_insights && res.data.key_insights.length > 0) {
          emit('add-log', `核心洞察: ${res.data.key_insights[0]}`)
        }
        
        await generateQuestions()
      } else {
        emit('add-log', `Agent预测失败，使用传统模式: ${res.error}`)
        await fallbackPrediction()
      }
    } else {
      await fallbackPrediction()
    }
  } catch (error) {
    emit('add-log', `预测异常，使用模拟数据: ${error.message}`)
    predictionData.value = generateMockPredictionData()
    recommendedQuestions.value = generateDefaultQuestions()
  } finally {
    isPredicting.value = false
  }
}

// 传统预测模式（降级方案）
const fallbackPrediction = async () => {
  const res = await predictPublicOpinion({
    simulation_id: props.simulationId || 'manual',
    report_id: props.reportId || '',
    event_summary: eventSummary.value,
    current_sentiment: currentSentiment.value,
    time_range: timeRange.value
  })

  if (res.success) {
    predictionData.value = res.data
    emit('add-log', '舆情预测完成')
    await generateQuestions()
  } else {
    emit('add-log', `预测API失败，使用模拟数据: ${res.error}`)
    predictionData.value = generateMockPredictionData()
    recommendedQuestions.value = generateDefaultQuestions()
  }
}

// 重置预测
const resetPrediction = () => {
  predictionData.value = null
  interventionResult.value = null
  chatHistory.value = []
  interventionText.value = ''
  startAutoPrediction()
}

// 模拟干预
// 🦋 蝴蝶效应沙盒方法

const loadTimelineEvents = async () => {
  if (!eventSummary.value) return
  isLoadingTimelineEvents.value = true
  try {
    const res = await generateTimelineEvents({
      event_summary: eventSummary.value,
      current_sentiment: currentSentiment.value,
      time_range: timeRange.value,
      scenarios: predictionData.value?.scenarios || []
    })
    if (res.success && res.data?.events?.length > 0) {
      llmTimelineEvents.value = res.data.events
      emit('add-log', `已生成${res.data.events.length}个时间线事件节点`)
    }
  } catch (error) {
    emit('add-log', `生成时间线事件失败: ${error.message}`)
  } finally {
    isLoadingTimelineEvents.value = false
  }
}

const loadInterventionCards = async () => {
  if (!predictionData.value) return
  isLoadingCards.value = true
  interventionCards.value = []
  try {
    const res = await generateInterventionCards({
      event_summary: predictionData.value.event_summary || eventSummary.value,
      scenarios: predictionData.value.scenarios || [],
      current_sentiment: predictionData.value.current_sentiment || currentSentiment.value,
      warnings: predictionData.value.warnings || []
    })
    if (res.success && res.data?.cards?.length > 0) {
      interventionCards.value = res.data.cards
      emit('add-log', `已生成${res.data.cards.length}张干预策略卡片`)
    } else {
      interventionCards.value = generateFallbackCards()
      emit('add-log', '干预卡片API返回空，使用降级数据')
    }
  } catch (error) {
    interventionCards.value = generateFallbackCards()
    emit('add-log', `干预卡片加载失败，使用降级数据`)
  } finally {
    isLoadingCards.value = false
  }
}

const generateFallbackCards = () => {
  return [
    { id: 'fc1', icon: '📢', name: '官方声明', description: '通过官方渠道发布正式声明，澄清事实', estimated_effect: '快速止血，降低传播速度' },
    { id: 'fc2', icon: '🤝', name: 'KOL引导', description: '邀请意见领袖参与讨论，正向引导舆论', estimated_effect: '稀释负面声音' },
    { id: 'fc3', icon: '📊', name: '数据披露', description: '公开关键数据和事实依据，增强透明度', estimated_effect: '提升公众信任' },
    { id: 'fc4', icon: '🎯', name: '精准回应', description: '针对核心质疑点进行一对一回应', estimated_effect: '解决关键矛盾' },
  ]
}

const retryLoadCards = () => {
  loadInterventionCards()
}

const selectInterventionCard = (card) => {
  selectedCard.value = selectedCard.value?.id === card.id ? null : card
  branchTimeline.value = []
  branchComparison.value = null
  branchAnalysis.value = ''
}

const generateBranchTimeline = async () => {
  if (!selectedCard.value) return
  isBranching.value = true
  try {
    const res = await generateInterventionTimeline({
      event_summary: predictionData.value.event_summary || eventSummary.value,
      current_sentiment: predictionData.value.current_sentiment || currentSentiment.value,
      time_range: timeRange.value,
      intervention_type: selectedCard.value.type,
      intervention_description: selectedCard.value.description,
      intervention_day: interventionDay.value,
      original_timeline: originalTimeline.value
    })
    if (res.success && res.data) {
      branchTimeline.value = res.data.branch_timeline || []
      branchComparison.value = res.data.comparison || null
      branchAnalysis.value = res.data.analysis || ''
      emit('add-log', `分叉时间线生成完成: ${selectedCard.value.name} @ 第${interventionDay.value}天`)
    }
  } catch (error) {
    emit('add-log', `分叉时间线生成失败: ${error.message}`)
    branchTimeline.value = []
    branchComparison.value = null
    branchAnalysis.value = ''
  } finally {
    isBranching.value = false
  }
}

const runStrategyCompare = async () => {
  if (!predictionData.value) return
  if (interventionCards.value.length === 0) {
    emit('add-log', '请先生成干预策略卡片')
    return
  }
  isComparing.value = true
  try {
    const strategies = interventionCards.value.slice(0, 4).map(c => ({
      type: c.type,
      description: c.description,
      timing: Math.ceil(timeRange.value / 3)
    }))
    const res = await strategyCompare({
      event_summary: predictionData.value.event_summary || eventSummary.value,
      current_sentiment: predictionData.value.current_sentiment || currentSentiment.value,
      strategies,
      original_timeline: originalTimeline.value
    })
    if (res.success && res.data) {
      strategyComparisons.value = res.data.comparisons || []
      strategyRecommendation.value = res.data.recommendation || ''
      emit('add-log', '策略竞技场对比完成')
    }
  } catch (error) {
    emit('add-log', `策略对比失败: ${error.message}`)
    strategyComparisons.value = []
    strategyRecommendation.value = ''
  } finally {
    isComparing.value = false
  }
}

const runHeatmapGeneration = async () => {
  if (!predictionData.value) return
  if (interventionCards.value.length === 0) {
    emit('add-log', '请先生成干预策略卡片')
    return
  }
  isGeneratingHeatmap.value = true
  try {
    const interventionTypes = interventionCards.value.slice(0, 4).map(c => c.type)
    const res = await generateInterventionHeatmap({
      event_summary: predictionData.value.event_summary || eventSummary.value,
      current_sentiment: predictionData.value.current_sentiment || currentSentiment.value,
      time_range: timeRange.value,
      intervention_types: interventionTypes,
      original_timeline: originalTimeline.value
    })
    if (res.success && res.data?.heatmap) {
      heatmapData.value = res.data.heatmap
      heatmapExplanation.value = res.data.explanation || '颜色越深代表干预效果越好，深蓝色区域是黄金干预期！'
      emit('add-log', '干预时机热力图生成完成')
      await nextTick()
      renderHeatmapD3()
    } else {
      heatmapData.value = generateFallbackHeatmap()
      heatmapExplanation.value = '这是基于当前舆情态势推算的参考数据，实际干预效果还需结合具体情况。'
      await nextTick()
      renderHeatmapD3()
    }
  } catch (error) {
    heatmapData.value = generateFallbackHeatmap()
    heatmapExplanation.value = '热力图生成遇到问题，显示的是模拟数据仅供参考。'
    emit('add-log', `热力图生成失败，使用降级数据: ${error.message}`)
    await nextTick()
    renderHeatmapD3()
  } finally {
    isGeneratingHeatmap.value = false
  }
}

const generateFallbackHeatmap = () => {
  const types = ['官方声明', 'KOL引导', '数据披露', '精准回应']
  const days = Math.min(timeRange.value, 7)
  return types.map((name, i) => ({
    type: `type_${i}`,
    type_name: name,
    scores: Array.from({ length: days }, (_, d) => ({
      day: d + 1,
      score: Math.round(40 + Math.random() * 40 + (i === 0 ? 15 : 0) - d * 3),
      effectiveness: d < 2 ? '极佳' : d < 4 ? '良好' : '一般',
      risk_note: '仅供参考'
    }))
  }))
}

const renderHeatmapD3 = () => {
  if (!heatmapCanvas.value || heatmapData.value.length === 0) return

  const container = heatmapCanvas.value
  container.innerHTML = ''

  const margin = { top: 30, right: 20, bottom: 50, left: 80 }
  const cellGap = 3
  const cellRadius = 4

  const types = heatmapData.value.map(r => r.type_name)
  const days = heatmapData.value[0]?.scores.map(s => s.day) || []
  const daysCount = days.length
  const rowsCount = types.length

  const cellW = Math.max(40, Math.min(60, (container.clientWidth - margin.left - margin.right - (daysCount - 1) * cellGap) / daysCount))
  const cellH = 44
  const width = margin.left + (daysCount * cellW) + ((daysCount - 1) * cellGap) + margin.right
  const height = margin.top + (rowsCount * cellH) + ((rowsCount - 1) * cellGap) + margin.bottom

  const svg = d3.select(container).append('svg')
    .attr('width', width)
    .attr('height', height)

  const defs = svg.append('defs')

  const colorScale = d3.scaleLinear()
    .domain([20, 50, 80])
    .range(['#1e40af', '#7dd3fc', '#fef9c3'])
    .interpolate(d3.interpolateHcl)

  const warningScale = d3.scaleLinear()
    .domain([20, 50, 80])
    .range(['#dc2626', '#f97316', '#22c55e'])
    .interpolate(d3.interpolateHcl)

  // 定义呼吸动画（使用 CSS filter: drop-shadow）
  defs.append('style')
    .text(`
      @keyframes breathGlow {
        0%, 100% { 
          filter: drop-shadow(0 0 8px #FFD700);
        }
        50% { 
          filter: drop-shadow(0 0 12px #FFD700) brightness(1.2);
        }
      }
      .gold-point {
        animation: breathGlow 2s ease-in-out infinite;
      }
    `)

  // 收集所有单元格，找出评分最低的Top3作为黄金干预期
  const allCells = []
  heatmapData.value.forEach((row, rowIdx) => {
    row.scores.forEach((score, colIdx) => {
      allCells.push({
        score: score.score,
        rowIdx,
        colIdx,
        row: row,
        day: score.day
      })
    })
  })
  // 按评分升序，取最低3个
  const topGoldCells = allCells.sort((a, b) => a.score - b.score).slice(0, 3)
  const goldCellKeys = new Set(topGoldCells.map(c => `${c.rowIdx}-${c.colIdx}`))

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  g.append('rect')
    .attr('width', width - margin.left - margin.right)
    .attr('height', height - margin.top - margin.bottom)
    .attr('fill', '#1e293b')
    .attr('rx', 8)

  g.selectAll('.col-header')
    .data(days)
    .join('text')
    .attr('class', 'col-header')
    .attr('x', (d, i) => i * (cellW + cellGap) + cellW / 2)
    .attr('y', -10)
    .attr('text-anchor', 'middle')
    .attr('fill', '#94a3b8')
    .attr('font-size', 11)
    .attr('font-weight', 600)
    .text(d => `Day ${d}`)

  g.selectAll('.row-label')
    .data(types)
    .join('text')
    .attr('class', 'row-label')
    .attr('x', -10)
    .attr('y', (d, i) => i * (cellH + cellGap) + cellH / 2)
    .attr('text-anchor', 'end')
    .attr('dominant-baseline', 'middle')
    .attr('fill', '#e2e8f0')
    .attr('font-size', 12)
    .attr('font-weight', 500)
    .text(d => d)

  const tooltip = d3.select(container).append('div')
    .attr('class', 'heatmap-tooltip')
    .style('opacity', 0)
    .style('position', 'absolute')
    .style('background', 'rgba(15,23,42,0.95)')
    .style('border', '1px solid #475569')
    .style('border-radius', '8px')
    .style('padding', '10px 14px')
    .style('color', '#f1f5f9')
    .style('font-size', '12px')
    .style('pointer-events', 'none')
    .style('z-index', 100)
    .style('box-shadow', '0 4px 12px rgba(0,0,0,0.3)')
    .style('max-width', '200px')

  let animDelay = 0

  heatmapData.value.forEach((row, rowIdx) => {
    row.scores.forEach((score, colIdx) => {
      const x = colIdx * (cellW + cellGap)
      const y = rowIdx * (cellH + cellGap)
      const isGoldCell = goldCellKeys.has(`${rowIdx}-${colIdx}`)

      const cell = g.append('g')
        .attr('class', 'heatmap-cell-group')
        .style('cursor', 'pointer')
        .on('click', () => {
          heatmapSelectedCell.value = { row: row.type_name, col: `Day ${score.day}`, score }
          // 派发给父组件
          emit('heatmapCellClick', {
            intervention: row.type_name.replace(/\s+/g, '_'),
            day: score.day,
            score: score.score
          })
          tooltip.transition().duration(200).style('opacity', 0)
        })

      cell.append('rect')
        .attr('x', x)
        .attr('y', y)
        .attr('width', cellW)
        .attr('height', cellH)
        .attr('rx', cellRadius)
        .attr('fill', colorScale(score.score))
        .attr('stroke', score.score > 70 ? warningScale(score.score) : (isGoldCell ? '#fbbf24' : 'none'))
        .attr('stroke-width', score.score > 70 || isGoldCell ? 2 : 0)
        .attr('class', isGoldCell ? 'gold-point' : '')
        .attr('opacity', 0)
        .transition()
        .duration(400)
        .delay(animDelay)
        .attr('opacity', 1)

      // 隐藏评分数字，仅保留风险文字，调小字号
      cell.append('text')
        .attr('x', x + cellW / 2)
        .attr('y', y + cellH / 2 + 2)
        .attr('text-anchor', 'middle')
        .attr('dominant-baseline', 'middle')
        .attr('fill', score.score > 60 ? '#1e293b' : '#cbd5e1')
        .attr('font-size', 8)
        .attr('opacity', 0.7)
        .text(score.score > 70 ? '高危' : score.score > 50 ? '中危' : '低危')
        .transition().duration(400).delay(animDelay).attr('opacity', 0.7)

      cell.on('mouseenter', function (event) {
        const rectElement = d3.select(this).select('rect')
        
        rectElement
          .transition().duration(200)
          .style('transform', `translateY(-4px) scale(1.05)`)
          .style('box-shadow', '0 10px 20px rgba(0,0,0,0.3)')
          .style('transform-origin', 'center center')

        d3.select(this.parentNode).selectAll('.heatmap-cell-group rect')
          .filter((d, i, els) => {
            const parent = d3.select(els[i].parentNode)
            return parent.node() !== d3.select(this).node()
          })
          .transition().duration(150).attr('opacity', 0.3)

        const rect = container.getBoundingClientRect()
        const tooltipX = event.clientX - rect.left + 10
        const tooltipY = event.clientY - rect.top - 10

        let icon = score.score < 40 ? '🌟' : (score.score > 70 ? '⚠️' : '')
        tooltip.html(`
          <div style="font-weight:600;margin-bottom:6px;color:#a5b4fc">${row.type_name} × Day ${score.day}</div>
          <div style="margin-bottom:4px">效果评分: ${icon} <span style="font-weight:700;color:${score.score > 70 ? '#ef4444' : score.score > 50 ? '#f59e0b' : '#22c55e'}">${score.score}分</span></div>
          <div style="color:#94a3b8;font-size:11px">${score.effectiveness || '效果一般'}</div>
          ${score.risk_note ? `<div style="color:#64748b;font-size:10px;margin-top:4px">${score.risk_note}</div>` : ''}
        `)
          .transition().duration(150)
          .style('opacity', 1)
          .style('left', `${Math.min(tooltipX, container.clientWidth - 220)}px`)
          .style('top', `${Math.max(0, tooltipY)}px`)
      })
      .on('mouseleave', function () {
        const rectElement = d3.select(this).select('rect')
        
        rectElement
          .transition().duration(200)
          .style('transform', 'translateY(0) scale(1)')
          .style('box-shadow', 'none')

        d3.select(this.parentNode).selectAll('.heatmap-cell-group rect')
          .transition().duration(150).attr('opacity', 1)

        tooltip.transition().duration(200).style('opacity', 0)
      })

      animDelay += 15
    })
  })

  const legendW = 120
  const legendH = 10
  const legendX = width - margin.right - legendW
  const legendY = height - 30

  const legendScale = d3.scaleLinear().domain([20, 100]).range([0, legendW])

  const legendGrad = defs.append('linearGradient')
    .attr('id', 'heatmapLegendGrad')
    .attr('x1', '0%').attr('y1', '0%').attr('x2', '100%').attr('y2', '0%')

  legendGrad.append('stop').attr('offset', '0%').attr('stop-color', '#1e40af')
  legendGrad.append('stop').attr('offset', '50%').attr('stop-color', '#7dd3fc')
  legendGrad.append('stop').attr('offset', '100%').attr('stop-color', '#fef9c3')

  g.append('rect')
    .attr('x', legendX)
    .attr('y', legendY)
    .attr('width', legendW)
    .attr('height', legendH)
    .attr('fill', 'url(#heatmapLegendGrad)')
    .attr('rx', 3)

  g.append('text').attr('x', legendX).attr('y', legendY - 4).attr('fill', '#94a3b8').attr('font-size', 9).text('效果差')
  g.append('text').attr('x', legendX + legendW).attr('y', legendY - 4).attr('fill', '#94a3b8').attr('font-size', 9).attr('text-anchor', 'end').text('效果佳')
}

const runCascadeEffect = async () => {
  if (!selectedCard.value) return
  isGeneratingCascade.value = true
  try {
    const res = await generateCascadeEffect({
      event_summary: predictionData.value.event_summary || eventSummary.value,
      intervention_type: selectedCard.value.type,
      intervention_description: selectedCard.value.description,
      simulation_data: {
        current_sentiment: predictionData.value.current_sentiment || currentSentiment.value,
        time_range: timeRange.value,
        agent_count: simulationRunData.value?.agent_count || 0,
        all_actions: simulationRunData.value?.all_actions || []
      }
    })
    if (res.success && res.data) {
      cascadeLayers.value = res.data.layers || []
      cascadeTotalReach.value = res.data.total_reach || 0
      cascadeSpeed.value = res.data.speed || ''
      emit('add-log', '链式反应推演完成')
    }
  } catch (error) {
    emit('add-log', `链式反应推演失败: ${error.message}`)
    cascadeLayers.value = []
    cascadeTotalReach.value = 0
    cascadeSpeed.value = ''
  } finally {
    isGeneratingCascade.value = false
  }
}

const runCounterfactual = async () => {
  if (!cfRemovedDay.value) return
  isGeneratingCF.value = true
  try {
    const removedNode = removableEvents.value.find(n => n.day === parseInt(cfRemovedDay.value))
    const removedEventDesc = removedNode?.event || `第${cfRemovedDay.value}天事件`
    const res = await generateCounterfactual({
      event_summary: predictionData.value.event_summary || eventSummary.value,
      current_sentiment: predictionData.value.current_sentiment || currentSentiment.value,
      original_timeline: originalTimeline.value,
      removed_event_day: parseInt(cfRemovedDay.value),
      removed_event_desc: removedEventDesc
    })
    if (res.success && res.data) {
      cfResult.value = res.data
      emit('add-log', `反事实推演完成: 移除D${cfRemovedDay.value}事件`)
    }
  } catch (error) {
    emit('add-log', `反事实推演失败: ${error.message}`)
    cfResult.value = null
  } finally {
    isGeneratingCF.value = false
  }
}

// 生成推荐问题
const generateQuestions = async () => {
  if (!predictionData.value?.scenarios?.length) return
  
  isGeneratingQuestions.value = true
  try {
    const res = await generateRecommendedQuestions({
      event_summary: eventSummary.value,
      scenarios: predictionData.value.scenarios,
      sentiment_distribution: sentimentDistribution.value
    })
    
    if (res.success && res.data?.questions?.length > 0) {
      recommendedQuestions.value = res.data.questions.slice(0, 3)
      emit('add-log', '已生成3个推荐问题')
    } else {
      // 使用默认推荐问题
      recommendedQuestions.value = generateDefaultQuestions()
    }
  } catch (error) {
    emit('add-log', `生成推荐问题失败: ${error.message}`)
    recommendedQuestions.value = generateDefaultQuestions()
  } finally {
    isGeneratingQuestions.value = false
  }
}

// 生成默认推荐问题（基于情景）
const generateDefaultQuestions = () => {
  const scenarios = predictionData.value?.scenarios || []
  const questions = []
  const eventName = eventSummary.value?.slice(0, 20) || '该事件'
  
  // 问题1: 基于最可能的情景，动态生成
  if (scenarios.length > 0) {
    const topScenario = scenarios[0]
    const prob = topScenario.probability || 25
    const risk = topScenario.risk_level || 'medium'
    
    if (risk === 'high') {
      questions.push(`"${eventName}..."演变为"${topScenario.name}"的概率较高，应如何提前做好应对准备？`)
    } else if (prob > 40) {
      questions.push(`面对"${topScenario.name}"这一主要情景，建议采取哪些关键措施确保舆情平稳？`)
    } else {
      questions.push(`针对"${topScenario.name}"情景，"${eventName}..."后续最需要关注什么？`)
    }
  }
  
  // 问题2: 基于情绪分布和风险等级
  const sentimentData = sentimentDistribution.value
  const negativePct = sentimentData.find(s => s.type === 'negative')?.percentage || 0
  const positivePct = sentimentData.find(s => s.type === 'positive')?.percentage || 0
  const dominantSentiment = negativePct > positivePct ? '负面' : (positivePct > negativePct ? '正面' : '中性')
  
  if (negativePct > 35) {
    questions.push(`当前${dominantSentiment}情绪占主导（${negativePct}%），如何遏制负面情绪扩散并转向建设性讨论？`)
  } else if (negativePct > 20) {
    questions.push(`当前存在一定负面情绪（${negativePct}%），如何及时干预避免舆情危机升级？`)
  } else {
    questions.push(`当前舆情情绪相对均衡，如何维持这种良好的讨论氛围？`)
  }
  
  // 问题3: 基于时间范围和预警信息
  const warnings = predictionData.value?.warnings || []
  const timeRangeDays = timeRange.value || 7
  
  if (warnings.length > 0) {
    const topWarning = warnings[0]
    const warningText = typeof topWarning === 'string' ? topWarning : (topWarning.description || topWarning.text || '')
    questions.push(`专家预警"${warningText.slice(0, 25)}..."，在${timeRangeDays}天内应如何重点防控？`)
  } else if (scenarios.length > 1) {
    const secondScenario = scenarios[1]
    questions.push(`如果"${secondScenario.name}"成为次要情景，对整体舆情走向会产生什么影响？`)
  } else {
    questions.push(`综合当前分析，未来${timeRangeDays}天内的舆情发展会经历哪些关键阶段？`)
  }
  
  return questions.slice(0, 3).length >= 3 ? questions.slice(0, 3) : [
    `${eventName}的后续发展趋势如何？有什么关键应对建议？`,
    `当前的舆情风险点主要集中在哪些方面？如何有效干预？`,
    `针对${timeRangeDays}天内的舆情发展，应重点做好哪些准备工作？`
  ]
}

// 选择推荐问题
const selectRecommendedQuestion = (question) => {
  chatInput.value = question
  sendChatMessage()
}

// 发送聊天消息
const sendChatMessage = async () => {
  if (!chatInput.value.trim()) return

  const userMessage = chatInput.value.trim()
  chatHistory.value.push({ role: 'user', content: userMessage })
  chatInput.value = ''
  isChatting.value = true

  try {
    const res = await chatAboutPrediction({
      question: userMessage,
      prediction_data: {
        event_summary: predictionData.value.event_summary || eventSummary.value,
        scenarios: predictionData.value.scenarios || [],
        warnings: predictionData.value.warnings || [],
        timeline: predictionData.value.timeline || [],
        conclusion: predictionData.value.conclusion || '',
        current_sentiment: predictionData.value.current_sentiment || currentSentiment.value,
        time_range: predictionData.value.time_range || timeRange.value
      }
    })

    if (res.success && res.data?.answer) {
      chatHistory.value.push({ role: 'assistant', content: marked.parse(res.data.answer) })
    } else if (res.success && res.data?.response) {
      chatHistory.value.push({ role: 'assistant', content: marked.parse(res.data.response) })
    } else {
      chatHistory.value.push({ role: 'assistant', content: '抱歉，我暂时无法回答这个问题。' })
    }
  } catch (error) {
    chatHistory.value.push({ role: 'assistant', content: '抱歉，服务暂时不可用。' })
  } finally {
    isChatting.value = false
    await nextTick()
    const container = document.querySelector('.chat-messages')
    if (container) container.scrollTop = container.scrollHeight
  }
}
</script>

<style scoped>
.prediction-panel {
  width: 100%;
  height: 100%;
  background: #f8fafc;
  overflow-y: auto;
}

/* 加载状态 */
.auto-loading-state,
.analyzing-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  padding: 40px;
}

.loading-animation {
  position: relative;
  width: 80px;
  height: 80px;
}

.loading-ring {
  position: absolute;
  border: 3px solid transparent;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.loading-ring:nth-child(1) { width: 80px; height: 80px; top: 0; left: 0; }
.loading-ring:nth-child(2) { width: 60px; height: 60px; top: 10px; left: 10px; animation-delay: -0.2s; }
.loading-ring:nth-child(3) { width: 40px; height: 40px; top: 20px; left: 20px; animation-delay: -0.4s; }

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-step {
  color: #64748b;
  margin-top: 16px;
}

.loading-progress {
  width: 300px;
  margin-top: 24px;
}

.progress-bar {
  height: 8px;
  background: #e2e8f0;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #3b82f6, #8b5cf6);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.progress-text {
  display: block;
  text-align: center;
  margin-top: 8px;
  font-size: 14px;
  color: #64748b;
}

/* 分析中状态 */
.analyzing-animation {
  position: relative;
  width: 100px;
  height: 100px;
}

.brain-icon {
  font-size: 48px;
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 2;
}

.pulse-ring {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  border: 2px solid #3b82f6;
  border-radius: 50%;
  opacity: 0;
  animation: pulse 2s ease-out infinite;
}

.pulse-ring:nth-child(2) { animation-delay: 0s; }
.pulse-ring:nth-child(3) { animation-delay: 0.6s; }

@keyframes pulse {
  0% { width: 60px; height: 60px; opacity: 0.8; }
  100% { width: 120px; height: 120px; opacity: 0; }
}

.analyzing-desc {
  color: #64748b;
  margin-top: 8px;
}

/* Agent分析中状态 */
.agent-analyzing-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  padding: 40px;
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
}

.agent-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}

.agent-icon {
  font-size: 48px;
  animation: bounce 2s ease-in-out infinite;
}

@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

.agent-status h3 {
  font-size: 20px;
  color: #1e293b;
  margin: 0;
}

.agent-stage {
  font-size: 14px;
  color: #6366f1;
  margin: 4px 0 0 0;
}

.agent-progress-bar {
  width: 400px;
  max-width: 100%;
  height: 8px;
  background: #e2e8f0;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 20px;
}

.agent-progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #6366f1, #8b5cf6);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.agent-message {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  margin-bottom: 20px;
  max-width: 500px;
}

.agent-message .message-icon {
  font-size: 18px;
}

.agent-message span:last-child {
  color: #475569;
  font-size: 14px;
}

.agent-logs-preview {
  width: 100%;
  max-width: 500px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  margin-bottom: 20px;
}

.logs-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
  font-size: 13px;
  color: #64748b;
}

.logs-count {
  background: #e2e8f0;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 12px;
}

.logs-list {
  max-height: 200px;
  overflow-y: auto;
  padding: 8px;
}

.log-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 8px 12px;
  border-radius: 6px;
  margin-bottom: 4px;
  background: #f8fafc;
  font-size: 13px;
}

.log-item:hover {
  background: #f1f5f9;
}

.log-item.tool_call {
  background: #eff6ff;
  border-left: 3px solid #3b82f6;
}

.log-item.tool_result {
  background: #f0fdf4;
  border-left: 3px solid #10b981;
}

.log-item.llm_response {
  background: #fef3c7;
  border-left: 3px solid #f59e0b;
}

.log-item.error {
  background: #fef2f2;
  border-left: 3px solid #ef4444;
}

.log-action {
  font-size: 12px;
  color: #64748b;
  white-space: nowrap;
  min-width: 80px;
}

.log-message {
  color: #475569;
  line-height: 1.4;
  word-break: break-word;
}

.agent-info {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
  justify-content: center;
}

.agent-info .info-item {
  font-size: 13px;
  color: #64748b;
  background: white;
  padding: 6px 12px;
  border-radius: 6px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.analyzing-progress {
  width: 300px;
  margin-top: 24px;
}

.progress-bar-indeterminate {
  height: 4px;
  background: linear-gradient(90deg, #3b82f6, #8b5cf6, #3b82f6);
  background-size: 200% 100%;
  border-radius: 2px;
  animation: indeterminate 1.5s linear infinite;
}

@keyframes indeterminate {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* 主内容区 - 左右分栏 */
.prediction-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.left-column {
  display: none;
}

/* 实时情报卡片 */
.intelligence-card {
  background: #1e293b;
  border-radius: 12px;
  padding: 20px;
  color: white;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}

.status-dot {
  width: 8px;
  height: 8px;
  background: #10b981;
  border-radius: 50%;
  animation: blink 2s infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.card-title {
  font-size: 14px;
  color: #94a3b8;
}

.intelligence-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.intel-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.intel-label {
  font-size: 12px;
  color: #94a3b8;
  margin-bottom: 4px;
}

.intel-value {
  font-size: 18px;
  font-weight: 600;
}

.intel-value.positive { color: #10b981; }
.intel-value.negative { color: #ef4444; }
.intel-value.neutral { color: #f59e0b; }
.intel-value.complex { color: #8b5cf6; }
.intel-value.high { color: #ef4444; }
.intel-value.medium { color: #f59e0b; }
.intel-value.low { color: #10b981; }
.intel-value.highlight { color: #60a5fa; }

/* 情景概率分布 */
.scenario-list-section {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 16px;
}

.scenario-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.scenario-list-item {
  padding-bottom: 12px;
  border-bottom: 1px solid #f1f5f9;
}

.scenario-list-item:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.scenario-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.scenario-name {
  font-size: 14px;
  color: #334155;
  flex: 1;
  padding-right: 8px;
}

.scenario-probability {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
}

.scenario-progress-bg {
  height: 6px;
  background: #f1f5f9;
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 8px;
}

.scenario-progress-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.5s ease;
}

.scenario-progress-fill.high { background: #ef4444; }
.scenario-progress-fill.medium { background: #f59e0b; }
.scenario-progress-fill.low { background: #10b981; }

.scenario-risk-tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
}

.scenario-risk-tag.high {
  background: #fef2f2;
  color: #ef4444;
}

.scenario-risk-tag.medium {
  background: #fffbeb;
  color: #f59e0b;
}

.scenario-risk-tag.low {
  background: #f0fdf4;
  color: #10b981;
}

.scenario-description {
  font-size: 12px;
  color: #64748b;
  line-height: 1.5;
  margin: 8px 0;
  padding: 8px 12px;
  background: #f8fafc;
  border-radius: 6px;
  border-left: 3px solid #3b82f6;
}

.scenario-keywords {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin: 8px 0;
}

.keyword-tag {
  display: inline-block;
  padding: 2px 8px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: white;
  font-size: 10px;
  border-radius: 10px;
  font-weight: 500;
}

.scenario-insight {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  margin: 8px 0;
  padding: 6px 10px;
  background: #fffbeb;
  border-radius: 6px;
  border-left: 3px solid #f59e0b;
}

.insight-label {
  font-size: 12px;
  flex-shrink: 0;
}

.insight-text {
  font-size: 11px;
  color: #92400e;
  line-height: 1.4;
  font-style: italic;
}

.scenario-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.scenario-timeline {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: #64748b;
}

.timeline-icon {
  font-size: 12px;
}

/* 风险评估雷达图 */
.radar-section {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.radar-chart {
  display: flex;
  justify-content: center;
  padding: 20px 0;
}

.radar-container {
  position: relative;
  width: 200px;
  height: 200px;
}

.radar-svg {
  width: 100%;
  height: 100%;
}

.radar-grid {
  fill: none;
  stroke: #e2e8f0;
  stroke-width: 1;
}

.radar-axis {
  stroke: #e2e8f0;
  stroke-width: 1;
}

.radar-area {
  fill: rgba(59, 130, 246, 0.2);
  stroke: #3b82f6;
  stroke-width: 2;
}

.radar-point {
  fill: #3b82f6;
}

.radar-labels {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.radar-labels span {
  position: absolute;
  font-size: 11px;
  color: #64748b;
  white-space: nowrap;
}

/* 右侧栏 */
.right-column {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* 合并图表样式 */
.merged-trend-section {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.merged-stats-row {
  display: flex;
  gap: 20px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #e2e8f0;
}

.merged-stats-row .heat-stat-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.sentiment-trend-line {
  stroke: #10b981;
  stroke-width: 2;
}

.sentiment-data-point {
  fill: #10b981;
  stroke: white;
  stroke-width: 1.5;
}

.heat-area, .sentiment-area {
  opacity: 0.6;
}

.section-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.risk-legend {
  display: flex;
  gap: 16px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #64748b;
}

.legend-item .dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.legend-item.high .dot { background: #ef4444; }
.legend-item.medium .dot { background: #f59e0b; }
.legend-item.low .dot { background: #10b981; }

.heat-bars-container {
  display: flex;
  gap: 20px;
}

.heat-bars {
  flex: 1;
  display: flex;
  align-items: flex-end;
  justify-content: space-around;
  height: 180px;
  padding: 0 10px;
}

.heat-bar-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.heat-value {
  font-size: 12px;
  font-weight: 600;
  color: #1e293b;
}

.heat-bar-bg {
  width: 32px;
  height: 120px;
  background: #f1f5f9;
  border-radius: 4px;
  overflow: hidden;
  position: relative;
}

.heat-bar-fill {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  border-radius: 4px;
  transition: height 0.5s ease;
}

.heat-bar-fill.high { background: linear-gradient(180deg, #ef4444, #dc2626); }
.heat-bar-fill.medium { background: linear-gradient(180deg, #f59e0b, #d97706); }
.heat-bar-fill.low { background: linear-gradient(180deg, #10b981, #059669); }

.heat-label {
  font-size: 11px;
  color: #64748b;
}

.heat-insight {
  width: 200px;
  padding: 16px;
  background: #f8fafc;
  border-radius: 8px;
}

.insight-risk {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  margin-bottom: 8px;
}

.insight-risk.high {
  background: #fef2f2;
  color: #ef4444;
}

.insight-risk.medium {
  background: #fffbeb;
  color: #f59e0b;
}

.insight-risk.low {
  background: #f0fdf4;
  color: #10b981;
}

.insight-round {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 8px;
}

.insight-desc {
  font-size: 13px;
  color: #64748b;
  line-height: 1.5;
  margin-bottom: 12px;
}

.insight-metrics {
  display: flex;
  gap: 16px;
}

.insight-metrics .metric {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #64748b;
}

.insight-metrics .metric-value {
  font-weight: 600;
  color: #1e293b;
}

/* 轮次热度折线图 */
.heat-line-chart-container {
  padding: 10px 0;
}

.heat-line-chart {
  height: 220px;
  background: #f8fafc;
  border-radius: 8px;
  padding: 10px;
}

.heat-line-svg {
  width: 100%;
  height: 100%;
}

.grid-line-light {
  stroke: #e2e8f0;
  stroke-width: 1;
  stroke-dasharray: 4, 4;
}

.axis-label {
  font-size: 11px;
  fill: #94a3b8;
  text-anchor: end;
}

.x-axis-label {
  font-size: 11px;
  fill: #64748b;
}

.heat-trend-line {
  stroke: #3b82f6;
  stroke-width: 3;
  fill: none;
  stroke-linecap: round;
  stroke-linejoin: round;
  filter: drop-shadow(0 2px 4px rgba(59, 130, 246, 0.3));
}

.heat-trend-line-dashed {
  stroke: #94a3b8;
  stroke-width: 2;
  fill: none;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-dasharray: 8, 4;
  opacity: 0.6;
}

.heat-data-point {
  fill: white;
  stroke-width: 3;
  cursor: pointer;
  transition: all 0.2s ease;
}

.heat-data-point.high {
  stroke: #ef4444;
}

.heat-data-point.medium {
  stroke: #f59e0b;
}

.heat-data-point.low {
  stroke: #10b981;
}

.heat-data-point.no-data {
  stroke: #cbd5e1;
  fill: #f1f5f9;
  r: 4;
}

.heat-data-point:hover {
  r: 8;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2));
}

.heat-data-point.no-data:hover {
  r: 5;
}

.heat-chart-legend {
  display: flex;
  justify-content: center;
  gap: 24px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #f1f5f9;
}

.heat-chart-legend .legend-item {
  font-size: 12px;
  color: #64748b;
}

.heat-stats-row {
  display: flex;
  justify-content: space-around;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #f1f5f9;
}

.heat-stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.heat-stat-item .stat-label {
  font-size: 12px;
  color: #94a3b8;
}

.heat-stat-item .stat-value {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
}

.heat-stat-item .stat-value.high {
  color: #ef4444;
}

.heat-stat-item .stat-value.medium {
  color: #f59e0b;
}

.heat-stat-item .stat-value.low {
  color: #10b981;
}

/* 多维趋势分析 */
.trend-analysis-section {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.trend-chart-wrapper {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.y-axis-labels {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 10px 0;
  font-size: 11px;
  color: #94a3b8;
  text-align: right;
  height: 180px;
}

.trend-chart-container {
  flex: 1;
  position: relative;
}

.trend-chart-container svg {
  width: 100%;
  height: 180px;
}

.grid-line {
  stroke: #f1f5f9;
  stroke-width: 1;
}

.trend-line {
  stroke-width: 3;
  fill: none;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.trend-line.heat {
  stroke: #ef4444;
}

.trend-line.sentiment {
  stroke: #10b981;
}

.data-point {
  stroke: white;
  stroke-width: 2;
}

.data-point.heat {
  fill: #ef4444;
}

.data-point.sentiment {
  fill: #10b981;
}

.risk-line {
  stroke: #f59e0b;
  stroke-width: 2;
  stroke-dasharray: 5, 5;
  opacity: 0.6;
}

.risk-labels {
  position: relative;
  height: 20px;
  margin-top: 4px;
}

.risk-label {
  position: absolute;
  transform: translateX(-50%);
  font-size: 10px;
  color: #f59e0b;
  background: #fffbeb;
  padding: 2px 6px;
  border-radius: 4px;
  border: 1px solid #fcd34d;
}

/* 图例卡片 */
.trend-legend {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-bottom: 20px;
}

.legend-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  background: #f8fafc;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
}

.legend-card .legend-color {
  width: 12px;
  height: 12px;
  border-radius: 3px;
}

.legend-card.heat .legend-color {
  background: #ef4444;
}

.legend-card.sentiment .legend-color {
  background: #10b981;
}

.legend-card.risk .legend-color {
  background: #f59e0b;
}

.legend-card .legend-info {
  display: flex;
  flex-direction: column;
}

.legend-card .legend-name {
  font-size: 11px;
  color: #64748b;
}

.legend-card .legend-value {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
}

/* 统计卡片 */
.trend-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 10px;
  border: 1px solid #e2e8f0;
}

.stat-card .stat-icon {
  font-size: 20px;
}

.stat-card .stat-info {
  display: flex;
  flex-direction: column;
}

.stat-card .stat-value {
  font-size: 18px;
  font-weight: 700;
  color: #1e293b;
}

.stat-card .stat-value.up {
  color: #ef4444;
}

.stat-card .stat-value.down {
  color: #10b981;
}

.stat-card .stat-value.stable {
  color: #64748b;
}

.stat-card .stat-value.warning {
  color: #f59e0b;
}

.stat-card .stat-label {
  font-size: 11px;
  color: #64748b;
  margin-top: 2px;
}

.stat-value.trend-arrow {
  color: #3b82f6;
}

.stat-label {
  display: block;
  font-size: 12px;
  color: #64748b;
  margin-top: 4px;
}

/* 预测结论 */
.conclusion-section {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.conclusion-content {
  display: flex;
  gap: 20px;
  align-items: flex-start;
}

.conclusion-content p {
  flex: 1;
  font-size: 14px;
  color: #475569;
  line-height: 1.6;
  margin: 0;
}

.btn-reanalyze {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: #f1f5f9;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.btn-reanalyze:hover {
  background: #e2e8f0;
  color: #475569;
}

/* 🦋 蝴蝶效应沙盒 */
.sandbox-section {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.sandbox-subtitle {
  font-size: 13px;
  color: #64748b;
  margin: 0 0 20px 0;
}

.card-pool {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 20px;
}

.card-pool-loading {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 20px;
  color: #64748b;
  font-size: 13px;
  justify-content: center;
}

.card-pool-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 30px 20px;
  color: #64748b;
  background: #f8fafc;
  border-radius: 10px;
  border: 1px dashed #d1d5db;
}

.empty-icon {
  font-size: 32px;
}

.empty-text {
  font-size: 14px;
  color: #94a3b8;
}

.btn-retry {
  padding: 8px 16px;
  background: #7c3aed;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-retry:hover {
  background: #6d28d9;
}

.intervention-card {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px;
  background: #f8fafc;
  border: 2px solid #e2e8f0;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.intervention-card:hover {
  border-color: #8b5cf6;
  background: #faf5ff;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.15);
}

.intervention-card.selected {
  border-color: #7c3aed;
  background: linear-gradient(135deg, #f5f3ff, #ede9fe);
  box-shadow: 0 4px 16px rgba(139, 92, 246, 0.25);
}

.card-icon {
  font-size: 24px;
  flex-shrink: 0;
}

.card-body {
  flex: 1;
  min-width: 0;
}

.card-name {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 4px;
}

.card-desc {
  font-size: 12px;
  color: #64748b;
  line-height: 1.4;
  margin-bottom: 4px;
}

.card-effect {
  font-size: 11px;
  color: #7c3aed;
  font-weight: 500;
}

.branch-controls {
  background: #f8fafc;
  border-radius: 10px;
  padding: 16px;
  margin-bottom: 20px;
}

.control-row {
  display: flex;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
}

.control-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.control-group label {
  font-size: 12px;
  color: #64748b;
}

.control-value {
  font-size: 14px;
  font-weight: 600;
  color: #7c3aed;
}

.day-select {
  padding: 6px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 13px;
  background: white;
  cursor: pointer;
}

.day-select:focus {
  outline: none;
  border-color: #7c3aed;
}

.btn-branch,
.btn-arena,
.btn-heatmap,
.btn-cascade,
.btn-cf {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px 16px;
  background: #7c3aed;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.btn-branch:hover:not(:disabled),
.btn-arena:hover:not(:disabled),
.btn-heatmap:hover:not(:disabled),
.btn-cascade:hover:not(:disabled),
.btn-cf:hover:not(:disabled) {
  background: #6d28d9;
}

.btn-branch:disabled,
.btn-arena:disabled,
.btn-heatmap:disabled,
.btn-cascade:disabled,
.btn-cf:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.spinner-sm {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.branch-chart-container {
  margin-bottom: 20px;
}

.branch-chart-header {
  display: flex;
  gap: 24px;
  margin-bottom: 8px;
  padding: 0 10px;
}

.branch-legend {
  font-size: 12px;
  color: #64748b;
  display: flex;
  align-items: center;
  gap: 6px;
}

.branch-legend.original { color: #3b82f6; }
.branch-legend.branch { color: #f59e0b; }

.branch-chart {
  background: #f8fafc;
  border-radius: 8px;
  padding: 10px;
}

.branch-svg {
  width: 100%;
}

.original-line {
  stroke: #3b82f6;
  stroke-width: 2.5;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.branch-line {
  stroke: #f59e0b;
  stroke-width: 2.5;
  stroke-dasharray: 8, 4;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.original-point {
  fill: #3b82f6;
  stroke: white;
  stroke-width: 1.5;
}

.branch-point {
  fill: #f59e0b;
  stroke: white;
  stroke-width: 1.5;
}

.intervention-line {
  stroke: #ef4444;
  stroke-width: 2;
  stroke-dasharray: 6, 3;
  opacity: 0.7;
}

.intervention-label {
  font-size: 11px;
  fill: #ef4444;
  font-weight: 600;
}

.branch-comparison {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-top: 16px;
  padding: 16px;
  background: #f8fafc;
  border-radius: 8px;
}

.comparison-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.comp-label {
  font-size: 11px;
  color: #64748b;
}

.comp-value {
  font-size: 16px;
  font-weight: 700;
}

.comp-value.up { color: #ef4444; }
.comp-value.down { color: #10b981; }

.branch-analysis {
  margin-top: 12px;
  padding: 12px 16px;
  background: linear-gradient(135deg, #fffbeb, #fef3c7);
  border-radius: 8px;
  border-left: 3px solid #f59e0b;
}

.branch-analysis p {
  font-size: 13px;
  color: #92400e;
  line-height: 1.6;
  margin: 0;
}

.sandbox-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-top: 20px;
}

.arena-section,
.heatmap-section,
.cascade-section,
.counterfactual-section {
  background: #f8fafc;
  border-radius: 10px;
  padding: 16px;
}

.sub-title {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 12px 0;
}

.arena-results {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 12px;
}

.arena-card {
  padding: 12px;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  transition: all 0.2s;
}

.arena-card.best {
  border-color: #10b981;
  background: linear-gradient(135deg, #f0fdf4, #dcfce7);
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.15);
}

.arena-card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.arena-rank {
  font-size: 12px;
  font-weight: 700;
  color: #64748b;
  min-width: 24px;
}

.arena-card.best .arena-rank {
  color: #10b981;
}

.arena-name {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
  flex: 1;
}

.arena-score {
  font-size: 16px;
  font-weight: 700;
  color: #7c3aed;
}

.arena-card.best .arena-score {
  color: #10b981;
}

.arena-metrics {
  display: flex;
  gap: 16px;
  margin-bottom: 8px;
}

.arena-metric {
  display: flex;
  align-items: center;
  gap: 4px;
}

.am-label {
  font-size: 11px;
  color: #94a3b8;
}

.am-value {
  font-size: 13px;
  font-weight: 600;
}

.am-value.up { color: #ef4444; }
.am-value.down { color: #10b981; }

.arena-analysis {
  font-size: 12px;
  color: #64748b;
  line-height: 1.5;
  margin: 0;
}

.arena-recommendation {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-top: 12px;
  padding: 10px 14px;
  background: linear-gradient(135deg, #f0fdf4, #dcfce7);
  border-radius: 8px;
  border-left: 3px solid #10b981;
  font-size: 13px;
  color: #166534;
  line-height: 1.5;
}

.rec-icon {
  flex-shrink: 0;
}

.heatmap-wrapper {
  position: relative;
  margin-top: 16px;
}

.heatmap-canvas {
  position: relative;
  width: 100%;
  min-height: 220px;
  background: #0f172a;
  border-radius: 12px;
  padding: 12px;
  overflow: hidden;
}

.heatmap-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 220px;
  background: #0f172a;
  border-radius: 12px;
  color: #94a3b8;
  gap: 16px;
}

.heatmap-loading-ring {
  width: 48px;
  height: 48px;
  border: 3px solid #1e293b;
  border-top-color: #6366f1;
  border-radius: 50%;
  animation: heatmap-spin 1s linear infinite;
}

@keyframes heatmap-spin {
  to { transform: rotate(360deg); }
}

.heatmap-explanation {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-top: 12px;
  padding: 10px 14px;
  background: linear-gradient(135deg, #1e293b, #0f172a);
  border-radius: 8px;
  border-left: 3px solid #6366f1;
}

.explanation-icon {
  flex-shrink: 0;
  font-size: 14px;
}

.explanation-text {
  font-size: 12px;
  color: #cbd5e1;
  line-height: 1.5;
}

.btn-heatmap {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: white;
  border: none;
  border-radius: 8px;
  padding: 8px 16px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 12px;
}

.btn-heatmap:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.35);
}

.btn-heatmap:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.spinner-sm {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-right: 6px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 链式反应 */
.cascade-container {
  margin-top: 20px;
}

.cascade-flow {
  position: relative;
  padding-left: 20px;
}

.cascade-layer {
  position: relative;
  margin-bottom: 25px;
  padding-left: 30px;
}

.layer-content {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 10px;
  padding: 16px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}

.layer-content:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.layer-header {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

.layer-level {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 12px;
  margin-right: 10px;
  flex-shrink: 0;
}

.layer-title {
  font-weight: 600;
  font-size: 14px;
  color: #333;
  flex: 1;
}

.layer-stats {
  display: flex;
  gap: 15px;
  margin-bottom: 10px;
  font-size: 12px;
  color: #666;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.sentiment-shift.positive {
  color: #28a745;
}

.sentiment-shift.negative {
  color: #dc3545;
}

.layer-agents {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}

.agent-tag {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 10px;
  font-weight: 500;
}

.agent-tag.high {
  background: #ffebee;
  color: #c62828;
  border: 1px solid #ffcdd2;
}

.agent-tag.medium {
  background: #fff8e1;
  color: #ef6c00;
  border: 1px solid #ffecb3;
}

.agent-tag.low {
  background: #e8f5e8;
  color: #2e7d32;
  border: 1px solid #c8e6c9;
}

.layer-connector {
  position: absolute;
  left: 14px;
  top: 100%;
  width: 2px;
  height: 25px;
  background: linear-gradient(to bottom, #667eea, #764ba2);
}

.cascade-summary {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 12px 16px;
  margin-top: 20px;
  font-size: 14px;
  font-weight: 500;
}

.summary-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.summary-label {
  color: #666;
}

.summary-value {
  color: #333;
  font-weight: 600;
}

.btn-cascade {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  padding: 8px 16px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-bottom: 15px;
}

.btn-cascade:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(102, 126, 234, 0.3);
}

.btn-cascade:disabled {
  background: #e0e0e0;
  color: #9e9e9e;
  cursor: not-allowed;
}

.cf-hint {
  font-size: 12px;
  color: #64748b;
  font-style: italic;
  margin: 0 0 12px 0;
}

.cf-controls {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.cf-select {
  flex: 1;
  padding: 6px 10px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 12px;
  background: white;
}

.cf-select:focus {
  outline: none;
  border-color: #7c3aed;
}

.cf-result {
  padding: 12px;
  background: white;
  border-radius: 8px;
  border-left: 3px solid #8b5cf6;
}

.cf-impact {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.cf-impact-label {
  font-size: 12px;
  color: #64748b;
}

.cf-impact-value {
  font-size: 20px;
  font-weight: 700;
  color: #7c3aed;
}

.cf-desc,
.cf-diff,
.cf-analysis {
  font-size: 12px;
  color: #475569;
  line-height: 1.5;
  margin: 0 0 6px 0;
}

.cf-diff {
  color: #92400e;
  font-weight: 500;
}

.cf-analysis {
  color: #64748b;
  font-style: italic;
  margin-bottom: 0;
}

/* AI助手 */
.ai-assistant-section {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.chat-container {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  overflow: hidden;
}

.chat-messages {
  height: 150px;
  overflow-y: auto;
  padding: 12px;
  background: #f8fafc;
}

.chat-placeholder {
  text-align: center;
  color: #94a3b8;
  padding: 40px 0;
  font-size: 14px;
}

.chat-message {
  margin-bottom: 12px;
}

.chat-message.user {
  text-align: right;
}

.chat-message.assistant {
  text-align: left;
}

.message-content {
  display: inline-block;
  max-width: 80%;
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 13px;
  line-height: 1.5;
}

.chat-message.user .message-content {
  background: #3b82f6;
  color: white;
  border-bottom-right-radius: 4px;
}

.chat-message.assistant .message-content {
  background: white;
  color: #334155;
  border: 1px solid #e2e8f0;
  border-bottom-left-radius: 4px;
  max-width: 100%;
}

.chat-message.assistant .message-content :deep(h1),
.chat-message.assistant .message-content :deep(h2),
.chat-message.assistant .message-content :deep(h3),
.chat-message.assistant .message-content :deep(h4) {
  margin: 0 0 10px 0;
  color: #1e293b;
  font-weight: 600;
}

.chat-message.assistant .message-content :deep(h1) { font-size: 18px; }
.chat-message.assistant .message-content :deep(h2) { font-size: 16px; }
.chat-message.assistant .message-content :deep(h3) { font-size: 15px; }
.chat-message.assistant .message-content :deep(h4) { font-size: 14px; }

.chat-message.assistant .message-content :deep(p) {
  margin: 0 0 10px 0;
  line-height: 1.6;
}

.chat-message.assistant .message-content :deep(p:last-child) {
  margin-bottom: 0;
}

.chat-message.assistant .message-content :deep(ul),
.chat-message.assistant .message-content :deep(ol) {
  margin: 0 0 10px 0;
  padding-left: 20px;
}

.chat-message.assistant .message-content :deep(li) {
  margin-bottom: 4px;
  line-height: 1.5;
}

.chat-message.assistant .message-content :deep(code) {
  background: #f1f5f9;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Fira Code', monospace;
  font-size: 12px;
  color: #6366f1;
}

.chat-message.assistant .message-content :deep(pre) {
  background: #1e293b;
  color: #e2e8f0;
  padding: 12px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 0 0 10px 0;
}

.chat-message.assistant .message-content :deep(pre code) {
  background: transparent;
  color: inherit;
  padding: 0;
}

.chat-message.assistant .message-content :deep(blockquote) {
  margin: 0 0 10px 0;
  padding: 8px 12px;
  border-left: 3px solid #6366f1;
  background: #f8fafc;
  color: #64748b;
  font-style: italic;
}

.chat-message.assistant .message-content :deep(strong) {
  color: #1e293b;
  font-weight: 600;
}

.chat-message.assistant .message-content :deep(em) {
  color: #475569;
}

.chat-message.assistant .message-content :deep(a) {
  color: #6366f1;
  text-decoration: none;
}

.chat-message.assistant .message-content :deep(a:hover) {
  text-decoration: underline;
}

.chat-message.assistant .message-content :deep(hr) {
  border: none;
  border-top: 1px solid #e2e8f0;
  margin: 12px 0;
}

.chat-message.assistant .message-content :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 0 0 10px 0;
  font-size: 13px;
}

.chat-message.assistant .message-content :deep(th),
.chat-message.assistant .message-content :deep(td) {
  border: 1px solid #e2e8f0;
  padding: 6px 10px;
  text-align: left;
}

.chat-message.assistant .message-content :deep(th) {
  background: #f8fafc;
  font-weight: 600;
}

.chat-input-area {
  display: flex;
  gap: 8px;
  padding: 12px;
  background: white;
  border-top: 1px solid #e2e8f0;
}

.chat-input {
  flex: 1;
  padding: 10px 14px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 14px;
}

.chat-input:focus {
  outline: none;
  border-color: #3b82f6;
}

.btn-send {
  padding: 10px 20px;
  background: #6366f1;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-send:hover:not(:disabled) {
  background: #4f46e5;
}

.btn-send:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

/* 推荐问题样式 */
.recommended-questions {
  padding: 16px;
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  border-radius: 12px;
  margin-bottom: 12px;
}

.recommended-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.recommended-icon {
  font-size: 1.2rem;
}

.recommended-title {
  font-size: 0.85rem;
  font-weight: 600;
  color: #0369a1;
}

.questions-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.question-btn {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px 14px;
  background: #ffffff;
  border: 1px solid #bae6fd;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: left;
  width: 100%;
}

.question-btn:hover:not(:disabled) {
  background: #f0f9ff;
  border-color: #7dd3fc;
  transform: translateX(4px);
  box-shadow: 0 2px 8px rgba(14, 165, 233, 0.15);
}

.question-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.question-number {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 22px;
  height: 22px;
  background: #0ea5e9;
  color: white;
  font-size: 0.75rem;
  font-weight: 600;
  border-radius: 50%;
  flex-shrink: 0;
}

.question-text {
  font-size: 0.85rem;
  color: #334155;
  line-height: 1.5;
  flex: 1;
}

.generating-questions {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  gap: 12px;
}

.generating-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #e2e8f0;
  border-top-color: #0ea5e9;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.generating-text {
  font-size: 0.85rem;
  color: #64748b;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 响应式 */
@media (max-width: 1024px) {
  .prediction-content {
    grid-template-columns: 1fr;
  }

  .heat-bars-container {
    flex-direction: column;
  }

  .heat-insight {
    width: auto;
  }
}
</style>
