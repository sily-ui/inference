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

    <!-- 主内容区 - 左右分栏布局 -->
    <div class="prediction-content" v-else-if="predictionData">
      <!-- 左侧栏 -->
      <div class="left-column">
        <!-- 情景概率分布 -->
        <div class="scenario-list-section">
          <h4 class="section-title">情景概率分布</h4>
          <div class="scenario-list">
            <div
              v-for="(scenario, idx) in predictionData.scenarios"
              :key="idx"
              class="scenario-list-item"
              :class="`risk-${scenario.risk_level}`"
            >
              <div class="scenario-header">
                <span class="scenario-name">{{ scenario.name }}</span>
                <span class="scenario-probability">{{ scenario.probability }}%</span>
              </div>
              <p class="scenario-description">{{ scenario.description || '暂无描述' }}</p>
              <div class="scenario-progress-bg">
                <div
                  class="scenario-progress-fill"
                  :class="scenario.risk_level"
                  :style="{ width: scenario.probability + '%' }"
                ></div>
              </div>
              <div class="scenario-meta">
                <div class="scenario-risk-tag" :class="scenario.risk_level">
                  {{ scenario.risk_level === 'high' ? '高风险' : scenario.risk_level === 'medium' ? '中风险' : '低风险' }}
                </div>
                <div class="scenario-timeline" v-if="scenario.timeline">
                  <span class="timeline-icon">⏱</span>
                  <span>{{ scenario.timeline }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 风险评估雷达图 -->
        <div class="radar-section">
          <h4 class="section-title">风险评估雷达</h4>
          <div class="radar-chart">
            <div class="radar-container">
              <svg viewBox="0 0 200 200" class="radar-svg">
                <!-- 背景网格 -->
                <polygon
                  v-for="n in 5"
                  :key="n"
                  :points="getRadarGridPoints(n)"
                  class="radar-grid"
                />
                <!-- 轴线 -->
                <line
                  v-for="(axis, idx) in radarAxes"
                  :key="idx"
                  :x1="100"
                  :y1="100"
                  :x2="axis.x"
                  :y2="axis.y"
                  class="radar-axis"
                />
                <!-- 数据区域 -->
                <polygon
                  :points="radarDataPoints"
                  class="radar-area"
                />
                <!-- 数据点 -->
                <circle
                  v-for="(point, idx) in radarData"
                  :key="idx"
                  :cx="point.x"
                  :cy="point.y"
                  r="4"
                  class="radar-point"
                />
              </svg>
              <!-- 标签 -->
              <div class="radar-labels">
                <span v-for="(label, idx) in radarLabels" :key="idx" :style="label.style">{{ label.text }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧栏 -->
      <div class="right-column">
        <!-- 轮次热度趋势 - 按5轮为单位折线图 -->
        <div class="heat-distribution-section">
          <div class="section-header-row">
            <h4 class="section-title">模拟轮次热度趋势</h4>
            <div class="risk-legend">
              <span class="legend-item high"><span class="dot"></span>高风险</span>
              <span class="legend-item medium"><span class="dot"></span>中风险</span>
              <span class="legend-item low"><span class="dot"></span>低风险</span>
            </div>
          </div>
          <div class="heat-line-chart-container">
            <div class="heat-line-chart">
              <svg viewBox="0 0 500 200" class="heat-line-svg">
                <!-- 背景网格 -->
                <line v-for="n in 5" :key="'h'+n" x1="50" :y1="n * 35" x2="480" :y2="n * 35" class="grid-line-light" />
                <line v-for="n in groupedRoundData.length" :key="'v'+n" :x1="50 + (n-1) * (430 / Math.max(groupedRoundData.length - 1, 1))" y1="10" :x2="50 + (n-1) * (430 / Math.max(groupedRoundData.length - 1, 1))" y2="175" class="grid-line-light" />
                
                <!-- Y轴标签 -->
                <text x="35" y="20" class="axis-label">100</text>
                <text x="40" y="90" class="axis-label">50</text>
                <text x="40" y="170" class="axis-label">0</text>
                
                <!-- 有数据部分的折线（实线） -->
                <polyline
                  v-for="(segment, idx) in groupedRoundLinePoints"
                  :key="'segment'+idx"
                  :points="segment"
                  class="heat-trend-line"
                  fill="none"
                />
                
                <!-- 预测趋势线（虚线） -->
                <polyline
                  v-if="trendLinePoints"
                  :points="trendLinePoints"
                  class="heat-trend-line-dashed"
                  fill="none"
                />
                
                <!-- 数据点 -->
                <circle
                  v-for="(point, idx) in groupedRoundPoints"
                  :key="idx"
                  :cx="point.x"
                  :cy="point.y"
                  r="6"
                  class="heat-data-point"
                  :class="[point.risk, { 'no-data': !point.hasData && point.heat === 0 }]"
                />
                
                <!-- X轴标签 -->
                <text
                  v-for="(group, idx) in groupedRoundData"
                  :key="'label'+idx"
                  :x="50 + idx * (430 / Math.max(groupedRoundData.length - 1, 1))"
                  y="195"
                  class="x-axis-label"
                  text-anchor="middle"
                >{{ group.label }}</text>
              </svg>
            </div>
            <div class="heat-chart-legend">
              <span class="legend-item">📊 每5轮聚合热度</span>
              <span class="legend-item">{{ simulationRunData?.all_actions?.length || 0 }} 条模拟数据</span>
              <span class="legend-item" style="color: #94a3b8;">--- 预测趋势</span>
            </div>
          </div>
          <!-- 统计信息 -->
          <div class="heat-stats-row" v-if="groupedRoundData.length > 0">
            <div class="heat-stat-item">
              <span class="stat-label">峰值轮次</span>
              <span class="stat-value">R{{ peakRoundRange }}</span>
            </div>
            <div class="heat-stat-item">
              <span class="stat-label">平均热度</span>
              <span class="stat-value">{{ avgGroupedHeat }}%</span>
            </div>
            <div class="heat-stat-item">
              <span class="stat-label">当前阶段</span>
              <span class="stat-value" :class="currentGroupRisk">{{ currentGroupRiskText }}</span>
            </div>
          </div>
        </div>

        <!-- 多维趋势分析 -->
        <div class="trend-analysis-section">
          <h4 class="section-title">多维趋势分析</h4>
          <div class="trend-chart-container">
            <div class="trend-chart">
              <svg viewBox="0 0 400 150" class="trend-svg">
                <!-- 网格线 -->
                <line v-for="n in 4" :key="n" x1="0" :y1="n * 30" x2="400" :y2="n * 30" class="grid-line" />
                <!-- 热度曲线 -->
                <polyline
                  :points="heatTrendPoints"
                  class="trend-line heat"
                  fill="none"
                />
                <!-- 情绪曲线 -->
                <polyline
                  :points="sentimentTrendPoints"
                  class="trend-line sentiment"
                  fill="none"
                />
                <!-- 风险点 -->
                <circle
                  v-for="(point, idx) in riskPoints"
                  :key="idx"
                  :cx="point.x"
                  :cy="point.y"
                  r="5"
                  class="risk-point"
                />
              </svg>
            </div>
            <div class="trend-legend">
              <span class="legend-item heat">— 热度指数</span>
              <span class="legend-item sentiment">— 情绪指数</span>
              <span class="legend-item risk">⚠ 风险趋势</span>
            </div>
          </div>
          <div class="trend-stats">
            <div class="stat-item">
              <span class="stat-value">{{ predictionData.stats?.avgHeat || 57 }}</span>
              <span class="stat-label">平均热度</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">{{ predictionData.stats?.maxHeat || 85 }}</span>
              <span class="stat-label">峰值热度</span>
            </div>
            <div class="stat-item">
              <span class="stat-value trend-arrow">→</span>
              <span class="stat-label">趋势方向</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">{{ predictionData.stats?.riskNodes || 2 }}</span>
              <span class="stat-label">风险节点</span>
            </div>
          </div>
        </div>

        <!-- 预测结论 -->
        <div class="conclusion-section">
          <h4 class="section-title">预测结论</h4>
          <div class="conclusion-content">
            <p>{{ predictionData.conclusion }}</p>
            <button class="btn-reanalyze" @click="resetPrediction">
              <span>🔄</span> 重新分析
            </button>
          </div>
        </div>

        <!-- 干预策略模拟 -->
        <div class="intervention-section">
          <h4 class="section-title">干预策略模拟</h4>
          <div class="intervention-input-area">
            <textarea
              v-model="interventionText"
              class="intervention-textarea"
              placeholder="输入干预策略，例如：发布官方声明澄清事实..."
              rows="2"
            ></textarea>
            <button
              class="btn-simulate"
              :disabled="isSimulating || !interventionText.trim()"
              @click="simulateIntervention"
            >
              <span v-if="isSimulating" class="spinner"></span>
              <span v-else>🚀 模拟效果</span>
            </button>
          </div>

          <!-- 干预结果 -->
          <div class="intervention-result" v-if="interventionResult">
            <div class="result-metrics">
              <div class="result-metric">
                <span class="metric-label">热度变化</span>
                <span class="metric-value" :class="interventionResult.heat_change > 0 ? 'up' : 'down'">
                  {{ interventionResult.heat_change > 0 ? '+' : '' }}{{ interventionResult.heat_change }}%
                </span>
              </div>
              <div class="result-metric">
                <span class="metric-label">情绪变化</span>
                <span class="metric-value" :class="interventionResult.sentiment_change > 0 ? 'up' : 'down'">
                  {{ interventionResult.sentiment_change > 0 ? '+' : '' }}{{ interventionResult.sentiment_change }}%
                </span>
              </div>
              <div class="result-metric">
                <span class="metric-label">推荐指数</span>
                <span class="metric-value stars">
                  {{ '★'.repeat(interventionResult.recommendation || 3) }}
                </span>
              </div>
            </div>
            <div class="result-analysis">
              <h5>策略分析</h5>
              <p>{{ interventionResult.analysis || interventionResult.expected_effect || '暂无分析' }}</p>
            </div>
          </div>
        </div>

        <!-- AI助手 -->
        <div class="ai-assistant-section">
          <h4 class="section-title">AI助手</h4>
          <div class="chat-container">
            <div class="chat-messages" ref="chatContainer">
              <!-- 推荐问题区域 -->
              <div v-if="chatHistory.length === 0 && recommendedQuestions.length > 0" class="recommended-questions">
                <div class="recommended-header">
                  <span class="recommended-icon">💡</span>
                  <span class="recommended-title">为您推荐的问题</span>
                </div>
                <div class="questions-list">
                  <button
                    v-for="(question, idx) in recommendedQuestions"
                    :key="idx"
                    class="question-btn"
                    @click="selectRecommendedQuestion(question)"
                    :disabled="isChatting"
                  >
                    <span class="question-number">{{ idx + 1 }}</span>
                    <span class="question-text">{{ question }}</span>
                  </button>
                </div>
              </div>
              <!-- 生成中状态 -->
              <div v-if="chatHistory.length === 0 && isGeneratingQuestions" class="generating-questions">
                <span class="generating-spinner"></span>
                <span class="generating-text">正在生成推荐问题...</span>
              </div>
              <!-- 聊天消息 -->
              <div
                v-for="(msg, idx) in chatHistory"
                :key="idx"
                class="chat-message"
                :class="msg.role"
              >
                <div class="message-content">{{ msg.content }}</div>
              </div>
            </div>
            <div class="chat-input-area">
              <input
                v-model="chatInput"
                type="text"
                class="chat-input"
                placeholder="向AI提问..."
                @keyup.enter="sendChatMessage"
              />
              <button
                class="btn-send"
                :disabled="isChatting || !chatInput.trim()"
                @click="sendChatMessage"
              >
                <span v-if="isChatting" class="spinner"></span>
                <span v-else>发送</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { predictPublicOpinion, simulateIntervention as apiSimulateIntervention, chatAboutPrediction, generateRecommendedQuestions, agentPredict } from '../api/prediction.js'
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

const emit = defineEmits(['add-log'])

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
const isAutoLoading = ref(true)
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
  if (!simulationRunData.value?.all_actions?.length) return []
  
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
  const maxDataRound = allRounds.length > 0 ? allRounds[allRounds.length - 1][0] : 1
  
  // 优先从后端存储的 run_state 中获取 total_rounds（最准确）
  // 这是 step2/3 启动模拟时计算并存储到数据库的
  const storedTotalRounds = simulationRunData.value?.total_rounds
  
  // 后备方案：从 step2/3 的 time_config 计算
  const timeConfig = props.simulationConfig?.time_config
  let calculatedRounds = 0
  if (timeConfig?.total_simulation_hours && timeConfig?.minutes_per_round) {
    calculatedRounds = Math.floor((timeConfig.total_simulation_hours * 60) / timeConfig.minutes_per_round)
  }
  
  // 使用存储的值优先，其次是计算值，最后是数据推断值
  const configMaxRounds = storedTotalRounds || calculatedRounds || maxDataRound
  
  // 确保至少显示到第15轮（3个区间），或配置的最大轮次
  const displayMaxRound = Math.max(configMaxRounds, 15, maxDataRound)
  
  // 计算最大动作数用于热度标准化
  const maxCount = Math.max(...allRounds.map(([, d]) => d.count), 1)
  
  // 按5轮分组，显示所有区间（包括无数据的）
  const groups = []
  for (let start = 1; start <= displayMaxRound; start += 5) {
    const end = Math.min(start + 4, displayMaxRound)
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
  const step = 400 / (timeline.length - 1 || 1)
  return timeline.map((t, i) => `${i * step},${150 - t.heat * 1.2}`).join(' ')
})

const sentimentTrendPoints = computed(() => {
  if (!predictionData.value?.timeline?.length) return ''
  const timeline = predictionData.value.timeline
  const step = 400 / (timeline.length - 1 || 1)
  return timeline.map((t, i) => `${i * step},${150 - (t.sentiment * 100) * 1.2}`).join(' ')
})

const riskPoints = computed(() => {
  if (!predictionData.value?.warnings?.length) return []
  const warnings = predictionData.value.warnings.filter(w => w.level === 'high')
  const step = 400 / (predictionData.value.timeline?.length - 1 || 1)
  return warnings.map((w, i) => ({
    x: (w.day / timeRange.value) * 400,
    y: 75
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

// 监听配置变化
watch(() => props.simulationConfig, async (newConfig) => {
  if (newConfig && !eventSummary.value) {
    await autoInitialize()
  }
}, { immediate: true })

// 自动初始化数据 - 基于前四步真实数据
const autoInitialize = async () => {
  isAutoLoading.value = true
  loadingProgress.value = 0

  try {
    // 步骤1: 获取项目详情
    loadingStep.value = '正在获取项目信息...'
    loadingProgress.value = 10

    if (props.projectData?.project_id) {
      try {
        const projectRes = await getProject(props.projectData.project_id)
        if (projectRes.success) {
          projectDetail.value = projectRes.data
          emit('add-log', '已获取项目详情')
        }
      } catch (e) {
        emit('add-log', `获取项目详情失败: ${e.message}`)
      }
    }

    // 步骤2: 获取模拟运行数据
    loadingStep.value = '正在获取模拟运行数据...'
    loadingProgress.value = 25

    if (props.simulationId) {
      try {
        const runRes = await getRunStatusDetail(props.simulationId)
        if (runRes.success && runRes.data) {
          simulationRunData.value = runRes.data
          calculateRoundHeatData(runRes.data.all_actions || [])
          emit('add-log', `已获取模拟运行数据: ${runRes.data.all_actions?.length || 0} 条动作记录`)
        }
      } catch (e) {
        emit('add-log', `获取模拟运行数据失败: ${e.message}`)
      }
    }

    loadingProgress.value = 40
    await delay(200)

    // 步骤3: 获取报告数据
    loadingStep.value = '正在获取报告数据...'
    loadingProgress.value = 55

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
          emit('add-log', '已获取报告数据')
        }
      } catch (e) {
        emit('add-log', `获取报告数据失败: ${e.message}`)
      }
    }

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

    loadingProgress.value = 70
    await delay(200)

    // 步骤4: Tavily搜索补充信息
    loadingStep.value = '正在搜索网络信息...'
    loadingProgress.value = 80

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
        emit('add-log', `Tavily搜索失败: ${e.message}`)
      }
    }

    loadingProgress.value = 90
    await delay(200)

    // 步骤5: 计算预测时间范围
    loadingStep.value = '正在计算预测周期...'

    // 优先从后端存储的 run_state 中获取 total_rounds（最准确）
    const storedTotalRounds = simulationRunData.value?.total_rounds

    // 后备方案：从 step2/3 的 time_config 计算
    const timeConfig = props.simulationConfig?.time_config
    let calculatedRounds = 0
    if (timeConfig?.total_simulation_hours && timeConfig?.minutes_per_round) {
      calculatedRounds = Math.floor((timeConfig.total_simulation_hours * 60) / timeConfig.minutes_per_round)
    }

    const maxRounds = storedTotalRounds || calculatedRounds || 48
    timeRange.value = Math.max(7, Math.min(30, Math.ceil(maxRounds / 4)))

    // 步骤6: 基于真实数据计算情绪分布
    await analyzeSentimentFromRealData()

    const maxSentiment = sentimentDistribution.value.reduce((prev, current) =>
      prev.percentage > current.percentage ? prev : current
    )
    currentSentiment.value = maxSentiment.label

    loadingProgress.value = 100
    loadingStep.value = '初始化完成，正在启动分析...'

    emit('add-log', `舆情预测初始化完成: 基于${simulationRunData.value?.all_actions?.length || 0}条真实模拟数据`)

    await delay(500)
    isAutoLoading.value = false
    await startAutoPrediction()

  } catch (error) {
    emit('add-log', `初始化失败: ${error.message}`)
    isAutoLoading.value = false
  }
}

// 计算轮次热度数据
const calculateRoundHeatData = (actions) => {
  if (!actions || actions.length === 0) {
    roundHeatData.value = Array.from({ length: 7 }, (_, i) => ({
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
      name: '平稳过渡与多元化认同成为主流',
      probability: baselineProb,
      description: '舆情按正常轨迹发展，公众理性讨论占主导',
      risk_level: 'low',
      timeline: '7-14天'
    },
    {
      name: '争议升级与身份政治化',
      probability: pessimisticProb,
      description: '舆情持续发酵，可能引发次生危机和群体对立',
      risk_level: 'high',
      timeline: '14-21天'
    },
    {
      name: '制度反思与规则调整',
      probability: Math.floor(optimisticProb * 0.6),
      description: '舆情推动制度完善和规则优化',
      risk_level: 'medium',
      timeline: '10-17天'
    },
    {
      name: '商业价值波动与品牌重塑',
      probability: Math.floor(neutralPct * 0.4),
      description: '商业层面受影响，需要品牌策略调整',
      risk_level: 'medium',
      timeline: '7-14天'
    },
    {
      name: '激发连锁反应与人才流动加速',
      probability: Math.max(5, Math.floor(pessimisticProb * 0.3)),
      description: '引发相关领域连锁反应，人才和资源配置变化',
      risk_level: 'low',
      timeline: '21-30天'
    }
  ].sort((a, b) => b.probability - a.probability)

  const timeline = []
  const days = timeRange.value
  const heatData = roundHeatData.value

  if (heatData.length > 0) {
    heatData.forEach((round, idx) => {
      const day = Math.ceil((idx + 1) * days / heatData.length)
      timeline.push({
        day,
        heat: round.heat,
        sentiment: (sentimentMap['positive'] || 30) / 100,
        event: `第${round.round}轮模拟节点`,
        risk: round.risk,
        actionCount: round.actionCount
      })
    })
  } else {
    for (let i = 0; i < Math.min(days, 7); i++) {
      const day = i + 1
      const heat = Math.floor(40 + Math.sin(i * 0.8) * 30 + Math.random() * 20)
      const risk = heat > 75 ? 'high' : heat > 50 ? 'medium' : 'low'
      timeline.push({
        day,
        heat,
        sentiment: positivePct / 100,
        event: `第${day}天舆情发展节点`,
        risk
      })
    }
  }

  const avgHeat = Math.round(timeline.reduce((sum, t) => sum + t.heat, 0) / timeline.length)
  const maxHeat = Math.max(...timeline.map(t => t.heat))
  const riskNodes = timeline.filter(t => t.risk === 'high').length

  const dominantScenario = scenarios[0]
  const conclusion = `基于${simulationRunData.value?.all_actions?.length || 0}条真实模拟数据分析，预测"${dominantScenario.name}"最可能发生（${dominantScenario.probability}%），当前情绪以${currentSentiment.value}为主，需关注${riskNodes}个关键风险节点。`

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
const simulateIntervention = async () => {
  isSimulating.value = true

  try {
    emit('add-log', `模拟干预策略: ${interventionText.value.slice(0, 30)}...`)

    const res = await apiSimulateIntervention({
      event_summary: predictionData.value.event_summary,
      intervention: interventionText.value,
      current_sentiment: predictionData.value.current_sentiment
    })

    if (res.success) {
      interventionResult.value = res.data
      emit('add-log', '干预策略模拟完成')
    } else {
      // 生成模拟结果
      interventionResult.value = {
        heat_change: Math.floor(Math.random() * 20) - 10,
        sentiment_change: (Math.random() * 0.4 - 0.2).toFixed(1),
        recommendation: Math.floor(Math.random() * 2) + 3,
        expected_effect: `该策略将${interventionText.value.slice(0, 20)}...，预计短期内可能${Math.random() > 0.5 ? '分散' : '集中'}舆论焦点，长期效果取决于执行力度和公众接受度。`,
        risk: '存在不确定性'
      }
    }
  } catch (error) {
    emit('add-log', `干预模拟异常: ${error.message}`)
    interventionResult.value = {
      heat_change: -15,
      sentiment_change: 0.3,
      recommendation: 4,
      expected_effect: '该策略有助于缓解当前舆情压力，建议配合其他措施综合使用。',
      risk: '低风险'
    }
  } finally {
    isSimulating.value = false
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
  
  if (scenarios.length > 0) {
    const topScenario = scenarios[0]
    questions.push(`针对"${topScenario.name}"这一最可能发生的情景，应该采取哪些预防措施？`)
  }
  
  const highRiskScenario = scenarios.find(s => s.risk_level === 'high')
  if (highRiskScenario) {
    questions.push(`如果"${highRiskScenario.name}"发生，最佳的应对策略是什么？`)
  }
  
  const sentimentData = sentimentDistribution.value
  const negativePct = sentimentData.find(s => s.type === 'negative')?.percentage || 0
  if (negativePct > 30) {
    questions.push(`当前负面情绪占比${negativePct}%，如何有效引导舆论走向中性或正面？`)
  } else {
    questions.push(`基于当前舆情态势，未来${timeRange.value}天内需要重点关注哪些方面？`)
  }
  
  return questions.slice(0, 3)
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
      chatHistory.value.push({ role: 'assistant', content: res.data.answer })
    } else if (res.success && res.data?.response) {
      chatHistory.value.push({ role: 'assistant', content: res.data.response })
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
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 20px;
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

/* 左侧栏 */
.left-column {
  display: flex;
  flex-direction: column;
  gap: 20px;
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

/* 轮次热度分布 */
.heat-distribution-section {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
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

.trend-chart-container {
  margin-bottom: 16px;
}

.trend-chart {
  height: 150px;
  background: #f8fafc;
  border-radius: 8px;
  padding: 10px;
}

.trend-svg {
  width: 100%;
  height: 100%;
}

.grid-line {
  stroke: #e2e8f0;
  stroke-width: 1;
  stroke-dasharray: 4;
}

.trend-line {
  stroke-width: 2;
  fill: none;
}

.trend-line.heat {
  stroke: #ef4444;
}

.trend-line.sentiment {
  stroke: #10b981;
}

.risk-point {
  fill: #f59e0b;
  stroke: white;
  stroke-width: 2;
}

.trend-legend {
  display: flex;
  justify-content: center;
  gap: 24px;
  margin-top: 12px;
}

.trend-legend .legend-item {
  font-size: 12px;
  color: #64748b;
}

.trend-legend .legend-item.heat { color: #ef4444; }
.trend-legend .legend-item.sentiment { color: #10b981; }
.trend-legend .legend-item.risk { color: #f59e0b; }

.trend-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  padding-top: 16px;
  border-top: 1px solid #f1f5f9;
}

.stat-item {
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 24px;
  font-weight: 700;
  color: #1e293b;
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

/* 干预策略模拟 */
.intervention-section {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.intervention-input-area {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.intervention-textarea {
  flex: 1;
  padding: 12px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 14px;
  resize: none;
  font-family: inherit;
}

.intervention-textarea:focus {
  outline: none;
  border-color: #3b82f6;
}

.btn-simulate {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 12px 20px;
  background: #6366f1;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.btn-simulate:hover:not(:disabled) {
  background: #4f46e5;
}

.btn-simulate:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.intervention-result {
  padding: 16px;
  background: #f8fafc;
  border-radius: 8px;
}

.result-metrics {
  display: flex;
  gap: 24px;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e2e8f0;
}

.result-metric {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.metric-label {
  font-size: 12px;
  color: #64748b;
}

.metric-value {
  font-size: 18px;
  font-weight: 600;
}

.metric-value.up { color: #ef4444; }
.metric-value.down { color: #10b981; }
.metric-value.stars { color: #f59e0b; }

.result-analysis h5 {
  font-size: 14px;
  color: #1e293b;
  margin: 0 0 8px 0;
}

.result-analysis p {
  font-size: 13px;
  color: #64748b;
  line-height: 1.5;
  margin: 0;
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
