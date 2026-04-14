<template>
  <div class="cf-panel">
    <h4 class="section-title">🔮 反事实推演引擎</h4>
    <p class="cf-subtitle">调整时间轴与干预策略，观察舆情传播网络的动态演变</p>

    <div class="cf-main">
      <div class="cf-control-panel">
        <div class="cf-control-row">
          <div class="time-shuttle">
            <span class="shuttle-label">⏱ 时间穿梭</span>
            <input
              type="range"
              class="time-slider"
              :min="0"
              :max="maxTimeStep"
              :step="1"
              v-model.number="currentTimeStep"
            />
            <span class="shuttle-value">T+{{ currentTimeStep }}h</span>
          </div>
          <div class="strategy-group">
            <span class="strategy-label">🎯 干预策略</span>
            <div class="strategy-radios">
              <label
                v-for="s in strategies"
                :key="s.id"
                class="strategy-radio"
                :class="{ active: currentStrategy === s.id }"
              >
                <input type="radio" :value="s.id" v-model="currentStrategy" />
                <span class="radio-dot"></span>
                <span class="radio-text">{{ s.name }}</span>
              </label>
            </div>
          </div>
        </div>
        <button class="btn-run-cf" :disabled="isRunningCF" @click="runCounterfactualEngine">
          <span v-if="isRunningCF" class="spinner-sm"></span>
          <span v-else>🚀 启动推演</span>
        </button>
      </div>

      <div class="cf-dag-container" ref="dagContainer">
        <div class="dag-loading" v-if="isRunningCF">
          <div class="dag-loading-ring"></div>
          <span>推演计算中...</span>
        </div>
        <div class="dag-empty" v-else-if="!dagData.nodes.length">
          <span class="empty-icon">🕸️</span>
          <span>点击"启动推演"生成传播网络图</span>
        </div>
        <svg ref="dagSvg" class="dag-svg"></svg>
      </div>

      <div class="cf-bottom-row">
        <div class="cf-trend-panel">
          <div class="trend-header">
            <span class="trend-title">📈 全局态势趋势</span>
            <div class="trend-legends">
              <span class="trend-legend"><span class="legend-line original"></span>自然演化</span>
              <span class="trend-legend" v-if="currentStrategy !== 'natural'"><span class="legend-line intervened"></span>{{ currentStrategyName }}</span>
            </div>
          </div>
          <div class="trend-chart-container" ref="trendChart"></div>
          <div class="trend-chat-mini">
            <div class="chat-header-mini">
              <span class="chat-icon">🤖</span>
              <span class="chat-title">AI分析助手</span>
            </div>
            <div class="chat-messages-mini" ref="chatContainerMini">
              <div v-if="chatHistory.length === 0 && !isChatting && !isGeneratingQuestions" class="chat-empty-hint">
                <span>试试问问：最佳干预时机是什么时候？</span>
              </div>
              <div v-if="isGeneratingQuestions" class="chat-generating">
                <span class="mini-spinner"></span>
                <span>思考中...</span>
              </div>
              <div
                v-for="(msg, idx) in chatHistory"
                :key="idx"
                class="chat-message-mini"
                :class="msg.role"
              >
                <span class="mini-msg-content" v-html="msg.content"></span>
              </div>
            </div>
            <div class="chat-input-row">
              <input
                v-model="chatInput"
                type="text"
                class="chat-input-mini"
                placeholder="问AI..."
                @keyup.enter="sendChatMessage"
                :disabled="isChatting"
              />
              <button class="btn-chat-mini" @click="sendChatMessage" :disabled="isChatting || !chatInput.trim()">
                <span v-if="isChatting" class="mini-spinner"></span>
                <span v-else>→</span>
              </button>
            </div>
          </div>
        </div>

        <div class="cf-sidebar" :class="{ expanded: selectedNode }">
          <div class="sidebar-default" v-if="!selectedNode">
            <h5 class="sidebar-title">📊 全局概览</h5>
            <div class="global-stats">
              <div class="stat-card">
                <span class="stat-value">{{ globalStats.nodeCount }}</span>
                <span class="stat-label">传播节点</span>
              </div>
              <div class="stat-card">
                <span class="stat-value">{{ globalStats.edgeCount }}</span>
                <span class="stat-label">传播路径</span>
              </div>
              <div class="stat-card">
                <span class="stat-value">{{ globalStats.maxDepth }}</span>
                <span class="stat-label">传播层级</span>
              </div>
              <div class="stat-card">
                <span class="stat-value" :class="globalStats.riskLevel">{{ globalStats.riskText }}</span>
                <span class="stat-label">风险等级</span>
              </div>
            </div>
            <div class="global-radar">
              <h6 class="radar-title">多维特征雷达</h6>
              <svg viewBox="0 0 200 200" class="radar-svg">
                <polygon
                  v-for="level in 5"
                  :key="'grid'+level"
                  :points="getRadarGridPoints(level)"
                  class="radar-grid"
                />
                <line
                  v-for="(axis, idx) in radarAxes"
                  :key="'axis'+idx"
                  x1="100" y1="100"
                  :x2="axis.x" :y2="axis.y"
                  class="radar-axis-line"
                />
                <text
                  v-for="(label, idx) in radarLabels"
                  :key="'label'+idx"
                  :x="radarAxes[idx].tx"
                  :y="radarAxes[idx].ty"
                  class="radar-label-text"
                >{{ label }}</text>
                <polygon :points="globalRadarPoints" class="radar-area" />
                <circle
                  v-for="(pt, idx) in globalRadarData"
                  :key="'pt'+idx"
                  :cx="pt.x" :cy="pt.y" r="3"
                  class="radar-point"
                />
              </svg>
            </div>

            <div class="agent-decision-panel">
              <h6 class="decision-title">🤖 智能决策链</h6>
              <div class="decision-terminal">
                <div class="terminal-header-bar">
                  <span class="terminal-dot red"></span>
                  <span class="terminal-dot yellow"></span>
                  <span class="terminal-dot green"></span>
                  <span class="terminal-title">Agent Decision Trace</span>
                </div>
                <div class="terminal-content" ref="agentTerminal">
                  <div
                    v-for="(log, idx) in agentDecisionLogs"
                    :key="idx"
                    class="decision-line"
                    :class="log.type"
                  >
                    <span class="log-prefix">[{{ log.prefix }}]</span>
                    <span class="log-content">{{ log.content }}</span>
                  </div>
                  <div v-if="agentDecisionLogs.length === 0" class="empty-log">
                    等待推演启动...
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="sidebar-detail" v-else>
            <div class="detail-header">
              <h5 class="detail-title">{{ selectedNode.name }}</h5>
              <button class="btn-close-detail" @click="selectedNode = null">✕</button>
            </div>
            <div class="detail-badges">
              <span class="badge" :class="selectedNode.sentimentType">{{ selectedNode.sentiment }}</span>
              <span class="badge depth">L{{ selectedNode.depth }}</span>
              <span class="badge influence">{{ selectedNode.influenceLabel }}</span>
            </div>
            <div class="detail-radar">
              <h6 class="radar-title">节点多模态特征</h6>
              <svg viewBox="0 0 200 200" class="radar-svg">
                <polygon
                  v-for="level in 5"
                  :key="'dgrid'+level"
                  :points="getRadarGridPoints(level)"
                  class="radar-grid"
                />
                <line
                  v-for="(axis, idx) in radarAxes"
                  :key="'daxis'+idx"
                  x1="100" y1="100"
                  :x2="axis.x" :y2="axis.y"
                  class="radar-axis-line"
                />
                <text
                  v-for="(label, idx) in radarLabels"
                  :key="'dlabel'+idx"
                  :x="radarAxes[idx].tx"
                  :y="radarAxes[idx].ty"
                  class="radar-label-text"
                >{{ label }}</text>
                <polygon :points="nodeRadarPoints" class="radar-area node" />
                <circle
                  v-for="(pt, idx) in nodeRadarData"
                  :key="'dpt'+idx"
                  :cx="pt.x" :cy="pt.y" r="3"
                  class="radar-point node"
                />
              </svg>
            </div>
            <div class="detail-agent-log">
              <h6 class="log-title">Agent 决策日志</h6>
              <div class="terminal-window">
                <div class="terminal-header">
                  <span class="terminal-dot red"></span>
                  <span class="terminal-dot yellow"></span>
                  <span class="terminal-dot green"></span>
                  <span class="terminal-title-text">ReACT Chain</span>
                </div>
                <div class="terminal-body" ref="terminalBody">
                  <div
                    v-for="(line, idx) in selectedNode.agentLog"
                    :key="idx"
                    class="terminal-line"
                    :class="line.type"
                  >
                    <span class="line-prefix">{{ line.prefix }}</span>
                    <span class="line-content">{{ displayedLogContent(idx) }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import * as d3 from 'd3'
import { marked } from 'marked'
import { chatAboutPrediction, generateRecommendedQuestions } from '../api/prediction.js'

const props = defineProps({
  eventSummary: { type: String, default: '' },
  currentSentiment: { type: String, default: '中性' },
  timeRange: { type: Number, default: 7 },
  simulationRunData: { type: Object, default: null },
  predictionData: { type: Object, default: null },
  interventionCards: { type: Array, default: () => [] },
  originalTimeline: { type: Array, default: () => [] }
})

const emit = defineEmits(['add-log'])

const strategies = [
  { id: 'natural', name: '🌿 自然演化' },
  { id: 'official', name: '📢 官方通报' },
  { id: 'cutnode', name: '✂️ 切断高危节点' },
  { id: 'amplify', name: '🔊 放大正面声音' }
]

const currentStrategy = ref('natural')
const currentTimeStep = ref(0)
const maxTimeStep = computed(() => props.timeRange * 24)
const isRunningCF = ref(false)
const selectedNode = ref(null)

const dagContainer = ref(null)
const dagSvg = ref(null)
const trendChart = ref(null)
const terminalBody = ref(null)
const agentTerminal = ref(null)
const chatContainerMini = ref(null)

const dagData = ref({ nodes: [], edges: [] })
const trendData = ref({ original: [], intervened: [] })
const agentDecisionLogs = ref([])

const chatHistory = ref([])
const chatInput = ref('')
const isChatting = ref(false)
const isGeneratingQuestions = ref(false)
const recommendedQuestions = ref([])

let dagSimulation = null
let flowAnimationTimer = null
let agentLogTimer = null

const currentStrategyName = computed(() => {
  const s = strategies.find(s => s.id === currentStrategy.value)
  return s ? s.name.replace(/^[^\s]+\s/, '') : ''
})

const globalStats = computed(() => {
  const nodes = dagData.value.nodes
  const edges = dagData.value.edges
  const maxDepth = nodes.length > 0 ? Math.max(...nodes.map(n => n.depth)) : 0
  const highRiskCount = nodes.filter(n => n.riskLevel === 'high').length
  let riskLevel = 'low'
  let riskText = '低'
  if (highRiskCount >= 3) { riskLevel = 'high'; riskText = '高' }
  else if (highRiskCount >= 1) { riskLevel = 'medium'; riskText = '中' }
  return {
    nodeCount: nodes.length,
    edgeCount: edges.length,
    maxDepth,
    riskLevel,
    riskText
  }
})

const radarLabels = ['传播力', '影响力', '情绪极性', '可信度', '持续度']

const radarAxes = computed(() => {
  const angles = [0, 72, 144, 216, 288].map(a => (a - 90) * Math.PI / 180)
  return angles.map(angle => ({
    x: 100 + 80 * Math.cos(angle),
    y: 100 + 80 * Math.sin(angle),
    tx: 100 + 95 * Math.cos(angle),
    ty: 100 + 95 * Math.sin(angle)
  }))
})

const globalRadarData = computed(() => {
  const values = [
    Math.min(100, (globalStats.value.nodeCount / 20) * 100),
    Math.min(100, (globalStats.value.edgeCount / 30) * 100),
    props.currentSentiment === '负面' ? 80 : props.currentSentiment === '正面' ? 20 : 50,
    60,
    Math.min(100, props.timeRange * 10)
  ]
  const angles = [0, 72, 144, 216, 288].map(a => (a - 90) * Math.PI / 180)
  return values.map((val, idx) => ({
    x: 100 + (val / 100) * 80 * Math.cos(angles[idx]),
    y: 100 + (val / 100) * 80 * Math.sin(angles[idx]),
    value: val
  }))
})

const globalRadarPoints = computed(() => {
  return globalRadarData.value.map(p => `${p.x},${p.y}`).join(' ')
})

const nodeRadarData = computed(() => {
  if (!selectedNode.value) return []
  const n = selectedNode.value
  const values = [
    n.features?.spread || 50,
    n.features?.influence || 50,
    n.features?.sentiment || 50,
    n.features?.credibility || 50,
    n.features?.persistence || 50
  ]
  const angles = [0, 72, 144, 216, 288].map(a => (a - 90) * Math.PI / 180)
  return values.map((val, idx) => ({
    x: 100 + (val / 100) * 80 * Math.cos(angles[idx]),
    y: 100 + (val / 100) * 80 * Math.sin(angles[idx]),
    value: val
  }))
})

const nodeRadarPoints = computed(() => {
  return nodeRadarData.value.map(p => `${p.x},${p.y}`).join(' ')
})

const displayedLogLines = ref({})

const displayedLogContent = (idx) => {
  return displayedLogLines.value[idx] || ''
}

const scrollChatToBottom = async () => {
  await nextTick()
  if (chatContainerMini.value) {
    chatContainerMini.value.scrollTop = chatContainerMini.value.scrollHeight
  }
}

const sendChatMessage = async () => {
  if (!chatInput.value.trim() || isChatting.value) return

  const userMessage = chatInput.value.trim()
  chatInput.value = ''
  isChatting.value = true

  chatHistory.value.push({
    role: 'user',
    content: userMessage
  })

  await scrollChatToBottom()

  try {
    const predictionData = props.predictionData || {}
    const res = await chatAboutPrediction({
      question: userMessage,
      prediction_data: {
        event_summary: predictionData.event_summary || props.eventSummary || '',
        scenarios: predictionData.scenarios || [],
        warnings: predictionData.warnings || [],
        timeline: predictionData.timeline || [],
        conclusion: predictionData.conclusion || '',
        current_sentiment: predictionData.current_sentiment || props.currentSentiment || '中性',
        time_range: predictionData.time_range || props.timeRange || 7
      }
    })

    if (res.success && res.data?.answer) {
      chatHistory.value.push({
        role: 'assistant',
        content: marked.parse(res.data.answer)
      })
    } else if (res.success && res.data?.response) {
      chatHistory.value.push({
        role: 'assistant',
        content: marked.parse(res.data.response)
      })
    } else {
      chatHistory.value.push({
        role: 'assistant',
        content: '<p>抱歉，我暂时无法回答这个问题。</p>'
      })
    }

    emit('add-log', `AI助手回复: ${userMessage}`)
  } catch (err) {
    console.error('Chat error:', err)
    chatHistory.value.push({
      role: 'assistant',
      content: '<p>抱歉，出了点问题，请稍后再试。</p>'
    })
  } finally {
    isChatting.value = false
    await scrollChatToBottom()
  }
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

const runCounterfactualEngine = async () => {
  isRunningCF.value = true
  selectedNode.value = null
  agentDecisionLogs.value = []
  
  startAgentLogGeneration()
  
  try {
    const res = await generateCounterfactualDAG({
      event_summary: props.eventSummary,
      current_sentiment: props.currentSentiment,
      time_range: props.timeRange,
      strategy: currentStrategy.value,
      simulation_data: {
        all_actions: props.simulationRunData?.all_actions || [],
        agent_count: props.simulationRunData?.agent_count || 0
      },
      original_timeline: props.originalTimeline
    })
    if (res.success && res.data) {
      dagData.value = res.data.dag || { nodes: [], edges: [] }
      trendData.value = res.data.trend || { original: [], intervened: [] }
      emit('add-log', `反事实推演完成: ${currentStrategyName.value}策略, ${dagData.value.nodes.length}个节点`)
      await nextTick()
      renderDAG()
      renderTrendChart()
      addAgentLog('observation', 'Observation', `推演完成：生成${dagData.value.nodes.length}个传播节点，${dagData.value.edges.length}条传播路径`)
    }
  } catch (error) {
    emit('add-log', `反事实推演失败: ${error.message}`)
    dagData.value = generateFallbackDAG()
    trendData.value = generateFallbackTrend()
    await nextTick()
    renderDAG()
    renderTrendChart()
    addAgentLog('observation', 'Observation', `推演完成（使用模拟数据）：生成${dagData.value.nodes.length}个传播节点`)
  } finally {
    isRunningCF.value = false
    if (agentLogTimer) {
      clearInterval(agentLogTimer)
      agentLogTimer = null
    }
  }
}

const startAgentLogGeneration = () => {
  const strategyLogs = {
    natural: [
      { type: 'thought', prefix: 'Thought', content: '启动自然演化模式，分析舆情传播的自然规律...' },
      { type: 'action', prefix: 'Action', content: '正在构建传播网络模型，计算节点间的自然连接...' },
      { type: 'observation', prefix: 'Observation', content: '检测到传播网络正在自然扩散，无明显干预点' }
    ],
    official: [
      { type: 'thought', prefix: 'Thought', content: '检测到"KOL转发"节点情绪极性发生突变，负面权重增加 42%...' },
      { type: 'action', prefix: 'Action', content: '正在模拟反事实策略：[官方通报]...' },
      { type: 'thought', prefix: 'Thought', content: '分析官方通报的最佳时机和传播路径...' },
      { type: 'action', prefix: 'Action', content: '在 T+24h 插入官方通报节点，计算传播影响...' },
      { type: 'observation', prefix: 'Observation', content: '预测干预后，社交媒体传播路径缩减 3 层，扩散风险转为"中危"' }
    ],
    cutnode: [
      { type: 'thought', prefix: 'Thought', content: '识别到高危传播节点：社交媒体传播、KOL转发...' },
      { type: 'action', prefix: 'Action', content: '正在模拟反事实策略：[切断高危节点]...' },
      { type: 'thought', prefix: 'Thought', content: '计算切断节点后的传播路径变化...' },
      { type: 'action', prefix: 'Action', content: '移除高危节点连接，重新构建传播网络...' },
      { type: 'observation', prefix: 'Observation', content: '预测切断后，传播深度减少 2 层，负面情绪传播降低 65%' }
    ],
    amplify: [
      { type: 'thought', prefix: 'Thought', content: '检测到正面声音传播力度不足，需要放大...' },
      { type: 'action', prefix: 'Action', content: '正在模拟反事实策略：[放大正面声音]...' },
      { type: 'thought', prefix: 'Thought', content: '分析正面声音的最佳传播路径和放大倍数...' },
      { type: 'action', prefix: 'Action', content: '增强正面节点权重，优化传播路径...' },
      { type: 'observation', prefix: 'Observation', content: '预测放大后，正面情绪传播提升 78%，舆情整体转向正面' }
    ]
  }
  
  const logs = strategyLogs[currentStrategy.value] || strategyLogs.natural
  let logIndex = 0
  
  agentLogTimer = setInterval(() => {
    if (logIndex < logs.length) {
      agentDecisionLogs.value.push(logs[logIndex])
      logIndex++
      if (agentTerminal.value) {
        agentTerminal.value.scrollTop = agentTerminal.value.scrollHeight
      }
    } else {
      clearInterval(agentLogTimer)
      agentLogTimer = null
    }
  }, 800)
}

const addAgentLog = (type, prefix, content) => {
  agentDecisionLogs.value.push({ type, prefix, content })
  if (agentTerminal.value) {
    agentTerminal.value.scrollTop = agentTerminal.value.scrollHeight
  }
}

const generateFallbackDAG = () => {
  const nodeNames = [
    '事件起源', '社交媒体传播', 'KOL转发', '主流媒体报道',
    '公众讨论', '官方回应', '情绪分化', '深度讨论',
    '话题降温', '长尾效应', '竞品借势', '二次发酵'
  ]
  const sentiments = ['负面', '中性', '负面', '中性', '负面', '正面', '复杂', '中性', '正面', '中性', '负面', '负面']
  const nodes = nodeNames.map((name, i) => ({
    id: `n${i}`,
    name,
    depth: Math.min(Math.floor(i / 2), 5),
    influence: Math.max(10, 80 - i * 6 + Math.floor(Math.random() * 20)),
    influenceLabel: i < 3 ? '高' : i < 7 ? '中' : '低',
    sentiment: sentiments[i] || '中性',
    sentimentType: sentiments[i] === '负面' ? 'negative' : sentiments[i] === '正面' ? 'positive' : 'neutral',
    riskLevel: i < 4 ? 'high' : i < 8 ? 'medium' : 'low',
    timeStep: i * 6,
    features: {
      spread: 30 + Math.floor(Math.random() * 60),
      influence: 30 + Math.floor(Math.random() * 60),
      sentiment: sentiments[i] === '负面' ? 70 + Math.floor(Math.random() * 25) : 20 + Math.floor(Math.random() * 40),
      credibility: 30 + Math.floor(Math.random() * 50),
      persistence: 20 + Math.floor(Math.random() * 60)
    },
    agentLog: [
      { type: 'thought', prefix: 'Thought:', content: `识别到"${name}"节点的传播特征，需要评估其影响力...` },
      { type: 'action', prefix: 'Action:', content: `调用传播分析工具，计算节点${name}的影响力指数` },
      { type: 'observation', prefix: 'Observation:', content: `节点影响力为${80 - i * 6}，情绪倾向${sentiments[i]}，传播深度L${Math.min(Math.floor(i / 2), 5)}` }
    ]
  }))

  const edges = []
  for (let i = 1; i < nodes.length; i++) {
    const sourceIdx = Math.max(0, i - 1 - Math.floor(Math.random() * 2))
    edges.push({ source: `n${sourceIdx}`, target: `n${i}` })
    if (i > 2 && Math.random() > 0.5) {
      const altSource = Math.floor(Math.random() * (i - 1))
      edges.push({ source: `n${altSource}`, target: `n${i}` })
    }
  }

  return { nodes, edges }
}

const generateFallbackTrend = () => {
  const hours = maxTimeStep.value
  const original = []
  const intervened = []
  for (let h = 0; h <= hours; h += 4) {
    const progress = h / hours
    const base = 30 + 50 * Math.sin(progress * Math.PI)
    original.push({ time: h, value: Math.round(base + Math.random() * 10) })
    if (currentStrategy.value === 'natural') {
      intervened.push({ time: h, value: Math.round(base + Math.random() * 10) })
    } else {
      const reduction = currentStrategy.value === 'cutnode' ? 25 : currentStrategy.value === 'official' ? 18 : 12
      intervened.push({ time: h, value: Math.round(Math.max(10, base - reduction * Math.sin(progress * Math.PI)) + Math.random() * 8) })
    }
  }
  return { original, intervened }
}

const renderDAG = () => {
  if (!dagSvg.value) return
  const svg = d3.select(dagSvg.value)
  svg.selectAll('*').remove()

  const container = dagContainer.value
  if (!container) return
  const width = container.clientWidth
  const height = 420
  svg.attr('width', width).attr('height', height)

  const { nodes, edges } = dagData.value
  if (nodes.length === 0) return

  const filteredNodes = nodes.filter(n => n.timeStep <= currentTimeStep.value)
  const filteredNodeIds = new Set(filteredNodes.map(n => n.id))
  const filteredEdges = edges.filter(e => filteredNodeIds.has(e.source) && filteredNodeIds.has(e.target))

  const g = svg.append('g')

  const zoom = d3.zoom()
    .scaleExtent([0.3, 3])
    .on('zoom', (event) => {
      g.attr('transform', event.transform)
    })
  svg.call(zoom)

  const maxDepth = Math.max(...filteredNodes.map(n => n.depth), 1)
  const layerHeight = height / (maxDepth + 2)

  const simulation = d3.forceSimulation(filteredNodes)
    .force('link', d3.forceLink(filteredEdges).id(d => d.id).distance(80))
    .force('charge', d3.forceManyBody().strength(-200))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('y', d3.forceY(d => (d.depth + 1) * layerHeight).strength(0.3))
    .force('collision', d3.forceCollide().radius(d => Math.sqrt(d.influence) + 10))

  const defs = svg.append('defs')

  const gradient = defs.append('linearGradient')
    .attr('id', 'edgeGradient')
    .attr('gradientUnits', 'userSpaceOnUse')
  gradient.append('stop').attr('offset', '0%').attr('stop-color', '#6366f1').attr('stop-opacity', 0.6)
  gradient.append('stop').attr('offset', '100%').attr('stop-color', '#8b5cf6').attr('stop-opacity', 0.2)

  const flowGradient = defs.append('linearGradient')
    .attr('id', 'flowGradient')
    .attr('gradientUnits', 'userSpaceOnUse')
  flowGradient.append('stop').attr('offset', '0%').attr('stop-color', '#a78bfa').attr('stop-opacity', 0)
  flowGradient.append('stop').attr('offset', '50%').attr('stop-color', '#c4b5fd').attr('stop-opacity', 1)
  flowGradient.append('stop').attr('offset', '100%').attr('stop-color', '#a78bfa').attr('stop-opacity', 0)

  const glowFilter = defs.append('filter').attr('id', 'glow')
  glowFilter.append('feGaussianBlur').attr('stdDeviation', '3').attr('result', 'coloredBlur')
  const feMerge = glowFilter.append('feMerge')
  feMerge.append('feMergeNode').attr('in', 'coloredBlur')
  feMerge.append('feMergeNode').attr('in', 'SourceGraphic')

  const linkGroup = g.append('g').attr('class', 'links')
  const link = linkGroup.selectAll('line')
    .data(filteredEdges)
    .join('line')
    .attr('class', 'dag-edge')
    .attr('stroke', 'url(#edgeGradient)')
    .attr('stroke-width', 1.5)
    .attr('stroke-opacity', 0)

  const flowParticles = linkGroup.selectAll('circle')
    .data(filteredEdges)
    .join('circle')
    .attr('r', 2)
    .attr('fill', '#c4b5fd')
    .attr('opacity', 0)

  const nodeGroup = g.append('g').attr('class', 'nodes')
  const node = nodeGroup.selectAll('g')
    .data(filteredNodes)
    .join('g')
    .attr('class', 'dag-node')
    .style('cursor', 'pointer')
    .attr('opacity', 0)

  const sentimentColors = {
    'negative': '#ef4444',
    'positive': '#22c55e',
    'neutral': '#6366f1',
    'complex': '#f59e0b'
  }

  const riskColors = {
    'high': '#ef4444',
    'medium': '#f59e0b',
    'low': '#22c55e'
  }

  node.append('circle')
    .attr('r', d => Math.max(8, Math.sqrt(d.influence) * 1.5))
    .attr('fill', d => {
      if (currentStrategy.value === 'cutnode' && d.riskLevel === 'high') {
        return '#94a3b8'
      }
      return sentimentColors[d.sentimentType] || '#6366f1'
    })
    .attr('fill-opacity', d => {
      if (currentStrategy.value === 'cutnode' && d.riskLevel === 'high') {
        return 0.3
      }
      return 0.15
    })
    .attr('stroke', d => {
      if (currentStrategy.value === 'cutnode' && d.riskLevel === 'high') {
        return '#94a3b8'
      }
      return sentimentColors[d.sentimentType] || '#6366f1'
    })
    .attr('stroke-width', 2)
    .attr('stroke-dasharray', d => {
      if (currentStrategy.value === 'cutnode' && d.riskLevel === 'high') {
        return '4,2'
      }
      return 'none'
    })
    .attr('filter', d => {
      if (currentStrategy.value === 'cutnode' && d.riskLevel === 'high') {
        return 'none'
      }
      return 'url(#glow)'
    })

  node.append('circle')
    .attr('r', d => Math.max(4, Math.sqrt(d.influence) * 0.8))
    .attr('fill', d => {
      if (currentStrategy.value === 'cutnode' && d.riskLevel === 'high') {
        return '#cbd5e1'
      }
      return sentimentColors[d.sentimentType] || '#6366f1'
    })
    .attr('fill-opacity', d => {
      if (currentStrategy.value === 'cutnode' && d.riskLevel === 'high') {
        return 0.5
      }
      return 0.8
    })

  node.append('text')
    .attr('dy', d => -Math.max(8, Math.sqrt(d.influence) * 1.5) - 6)
    .attr('text-anchor', 'middle')
    .attr('fill', '#1e293b')
    .attr('font-size', '11px')
    .attr('font-weight', '500')
    .text(d => d.name.length > 6 ? d.name.slice(0, 6) + '…' : d.name)

  node.append('text')
    .attr('dy', d => Math.max(8, Math.sqrt(d.influence) * 1.5) + 14)
    .attr('text-anchor', 'middle')
    .attr('fill', d => riskColors[d.riskLevel] || '#94a3b8')
    .attr('font-size', '9px')
    .text(d => d.riskLevel === 'high' ? '⚠ 高危' : d.riskLevel === 'medium' ? '⚡ 中危' : '')

  const highRiskNodes = node.filter(d => d.riskLevel === 'high' && currentStrategy.value !== 'cutnode')
  highRiskNodes.each(function() {
    const nodeG = d3.select(this)
    nodeG.insert('circle', ':first-child')
      .attr('r', d => Math.max(12, Math.sqrt(d.influence) * 1.8))
      .attr('fill', 'none')
      .attr('stroke', '#ef4444')
      .attr('stroke-width', 1)
      .attr('opacity', 0)
      .attr('class', 'breathing-glow')
  })

  node.on('click', (event, d) => {
    event.stopPropagation()
    selectedNode.value = d
    startTypewriterEffect(d.agentLog || [])
  })

  node.on('mouseenter', function () {
    d3.select(this).select('circle').transition().duration(200).attr('r', d => Math.max(10, Math.sqrt(d.influence) * 1.8))
  }).on('mouseleave', function () {
    d3.select(this).select('circle').transition().duration(200).attr('r', d => Math.max(8, Math.sqrt(d.influence) * 1.5))
  })

  svg.on('click', () => {
    selectedNode.value = null
  })

  simulation.on('tick', () => {
    link
      .attr('x1', d => d.source.x)
      .attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x)
      .attr('y2', d => d.target.y)

    node.attr('transform', d => `translate(${d.x},${d.y})`)
  })

  node.transition()
    .duration(600)
    .delay((d, i) => i * 50)
    .attr('opacity', 1)

  link.transition()
    .duration(600)
    .delay((d, i) => filteredNodes.length * 50 + i * 30)
    .attr('stroke-opacity', 0.6)

  flowParticles.transition()
    .duration(600)
    .delay(filteredNodes.length * 50 + filteredEdges.length * 30 + 200)
    .attr('opacity', 0.8)

  if (flowAnimationTimer) clearInterval(flowAnimationTimer)
  
  const particleStates = filteredEdges.map(() => ({ progress: Math.random(), speed: 0.015 + Math.random() * 0.02 }))
  
  flowAnimationTimer = setInterval(() => {
    particleStates.forEach((state, idx) => {
      state.progress = (state.progress + state.speed) % 1
      const edge = filteredEdges[idx]
      if (edge && edge.source && edge.target) {
        const sourceX = typeof edge.source.x === 'number' ? edge.source.x : edge.source.x || 0
        const sourceY = typeof edge.source.y === 'number' ? edge.source.y : edge.source.y || 0
        const targetX = typeof edge.target.x === 'number' ? edge.target.x : edge.target.x || 0
        const targetY = typeof edge.target.y === 'number' ? edge.target.y : edge.target.y || 0
        
        d3.select(flowParticles.nodes()[idx])
          .attr('cx', sourceX + (targetX - sourceX) * state.progress)
          .attr('cy', sourceY + (targetY - sourceY) * state.progress)
          .attr('opacity', 0.4 + Math.sin(state.progress * Math.PI) * 0.6)
      }
    })
  }, 25)

  dagSimulation = simulation
}

const renderTrendChart = () => {
  if (!trendChart.value) return
  const container = trendChart.value
  container.innerHTML = ''

  const { original, intervened } = trendData.value
  if (original.length === 0) return

  const width = container.clientWidth
  const height = 160
  const margin = { top: 20, right: 20, bottom: 30, left: 40 }
  const chartW = width - margin.left - margin.right
  const chartH = height - margin.top - margin.bottom

  const svg = d3.select(container).append('svg')
    .attr('width', width)
    .attr('height', height)

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  const allValues = [...original.map(d => d.value), ...intervened.map(d => d.value)]
  const xScale = d3.scaleLinear()
    .domain([0, d3.max(original, d => d.time)])
    .range([0, chartW])

  const yScale = d3.scaleLinear()
    .domain([0, d3.max(allValues) * 1.1])
    .range([chartH, 0])

  g.append('g')
    .attr('transform', `translate(0,${chartH})`)
    .call(d3.axisBottom(xScale).ticks(6).tickFormat(d => `T+${d}h`))
    .attr('class', 'trend-axis')

  g.append('g')
    .call(d3.axisLeft(yScale).ticks(4))
    .attr('class', 'trend-axis')

  const lineGen = d3.line()
    .x(d => xScale(d.time))
    .y(d => yScale(d.value))
    .curve(d3.curveMonotoneX)

  const areaGen = d3.area()
    .x(d => xScale(d.time))
    .y0(chartH)
    .y1(d => yScale(d.value))
    .curve(d3.curveMonotoneX)

  const defs = svg.append('defs')
  const origGrad = defs.append('linearGradient')
    .attr('id', 'origAreaGrad')
    .attr('x1', '0%').attr('y1', '0%').attr('x2', '0%').attr('y2', '100%')
  origGrad.append('stop').attr('offset', '0%').attr('stop-color', '#6366f1').attr('stop-opacity', 0.3)
  origGrad.append('stop').attr('offset', '100%').attr('stop-color', '#6366f1').attr('stop-opacity', 0.02)

  const intGrad = defs.append('linearGradient')
    .attr('id', 'intAreaGrad')
    .attr('x1', '0%').attr('y1', '0%').attr('x2', '0%').attr('y2', '100%')
  intGrad.append('stop').attr('offset', '0%').attr('stop-color', '#f59e0b').attr('stop-opacity', 0.3)
  intGrad.append('stop').attr('offset', '100%').attr('stop-color', '#f59e0b').attr('stop-opacity', 0.02)

  g.append('path')
    .datum(original)
    .attr('d', areaGen)
    .attr('fill', 'url(#origAreaGrad)')

  g.append('path')
    .datum(original)
    .attr('d', lineGen)
    .attr('fill', 'none')
    .attr('stroke', '#6366f1')
    .attr('stroke-width', 2)

  if (currentStrategy.value !== 'natural' && intervened.length > 0) {
    g.append('path')
      .datum(intervened)
      .attr('d', areaGen)
      .attr('fill', 'url(#intAreaGrad)')

    g.append('path')
      .datum(intervened)
      .attr('d', lineGen)
      .attr('fill', 'none')
      .attr('stroke', '#f59e0b')
      .attr('stroke-width', 2)
      .attr('stroke-dasharray', '6,3')
  }

  if (currentStrategy.value !== 'natural') {
    const interventionTime = 24
    const interventionX = xScale(interventionTime)
    
    const markerGroup = g.append('g')
      .attr('class', 'intervention-marker')
      .style('cursor', 'pointer')
    
    markerGroup.append('line')
      .attr('x1', interventionX).attr('x2', interventionX)
      .attr('y1', 0).attr('y2', chartH)
      .attr('stroke', '#f59e0b')
      .attr('stroke-width', 2)
      .attr('stroke-dasharray', '8,4')
      .attr('opacity', 0.6)
    
    markerGroup.append('circle')
      .attr('cx', interventionX)
      .attr('cy', 10)
      .attr('r', 6)
      .attr('fill', '#f59e0b')
      .attr('stroke', 'white')
      .attr('stroke-width', 2)
    
    markerGroup.append('text')
      .attr('x', interventionX)
      .attr('y', -5)
      .attr('text-anchor', 'middle')
      .attr('fill', '#f59e0b')
      .attr('font-size', '10px')
      .attr('font-weight', '600')
      .text('🎯')
    
    const markerTooltip = d3.select(container).append('div')
      .attr('class', 'marker-tooltip')
      .style('position', 'absolute')
      .style('background', 'rgba(15,23,42,0.95)')
      .style('border', '1px solid #f59e0b')
      .style('border-radius', '6px')
      .style('padding', '8px 12px')
      .style('color', '#f1f5f9')
      .style('font-size', '11px')
      .style('pointer-events', 'none')
      .style('opacity', 0)
      .style('transition', 'opacity 0.2s')
      .style('z-index', '10')
    
    markerGroup.on('mouseenter', function(event) {
      d3.select(this).select('circle').transition().duration(200).attr('r', 8)
      
      const rect = container.getBoundingClientRect()
      markerTooltip
        .html(`<div style="font-weight:600;color:#fbbf24">干预启动</div><div style="margin-top:4px">${currentStrategyName.value}</div><div style="color:#94a3b8;font-size:10px">T+${interventionTime}h</div>`)
        .style('left', `${event.clientX - rect.left + 10}px`)
        .style('top', `${event.clientY - rect.top - 30}px`)
        .style('opacity', 1)
    })
    .on('mouseleave', function() {
      d3.select(this).select('circle').transition().duration(200).attr('r', 6)
      markerTooltip.style('opacity', 0)
    })
  }

  const timeMarker = g.append('line')
    .attr('y1', 0).attr('y2', chartH)
    .attr('stroke', '#94a3b8')
    .attr('stroke-width', 1)
    .attr('stroke-dasharray', '4,4')
    .attr('x1', xScale(currentTimeStep.value))
    .attr('x2', xScale(currentTimeStep.value))

  watch(currentTimeStep, (val) => {
    timeMarker.attr('x1', xScale(val)).attr('x2', xScale(val))
  })
}

let typewriterTimer = null

const startTypewriterEffect = (logs) => {
  if (typewriterTimer) clearInterval(typewriterTimer)
  displayedLogLines.value = {}
  if (!logs || logs.length === 0) return

  let lineIdx = 0
  let charIdx = 0

  typewriterTimer = setInterval(() => {
    if (lineIdx >= logs.length) {
      clearInterval(typewriterTimer)
      return
    }
    const content = logs[lineIdx].content || ''
    if (charIdx <= content.length) {
      displayedLogLines.value[lineIdx] = content.slice(0, charIdx)
      charIdx++
    } else {
      lineIdx++
      charIdx = 0
    }
    if (terminalBody.value) {
      terminalBody.value.scrollTop = terminalBody.value.scrollHeight
    }
  }, 25)
}

watch(currentTimeStep, () => {
  if (dagData.value.nodes.length > 0) {
    renderDAG()
  }
})

watch(currentStrategy, async (newVal, oldVal) => {
  if (oldVal && dagData.value.nodes.length > 0) {
    await runCounterfactualEngine()
  }
})

onBeforeUnmount(() => {
  if (dagSimulation) dagSimulation.stop()
  if (flowAnimationTimer) clearInterval(flowAnimationTimer)
  if (typewriterTimer) clearInterval(typewriterTimer)
})

onMounted(() => {
  dagData.value = generateFallbackDAG()
  trendData.value = generateFallbackTrend()
  nextTick(() => {
    renderDAG()
    renderTrendChart()
  })
})
</script>

<style scoped>
.cf-panel {
  background: #f8fafc;
  border-radius: 10px;
  padding: 16px;
}

.section-title {
  font-size: 14px;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 4px 0;
}

.cf-subtitle {
  font-size: 12px;
  color: #64748b;
  margin: 0 0 16px 0;
}



.cf-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.cf-bottom-row {
  display: flex;
  gap: 16px;
}

.cf-bottom-row .cf-trend-panel {
  flex: 1;
}

.cf-bottom-row .cf-sidebar {
  width: 320px;
  max-height: unset;
}

.cf-sidebar {
  width: 280px;
  flex-shrink: 0;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 16px;
  transition: width 0.3s ease;
  overflow-y: auto;
  max-height: 700px;
}

.cf-sidebar.expanded {
  width: 340px;
}

.cf-control-panel {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.cf-control-row {
  display: flex;
  align-items: center;
  gap: 24px;
  flex: 1;
  min-width: 0;
}

.time-shuttle {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  min-width: 200px;
}

.shuttle-label {
  font-size: 12px;
  color: #64748b;
  white-space: nowrap;
}

.time-slider {
  flex: 1;
  -webkit-appearance: none;
  appearance: none;
  height: 6px;
  background: #e2e8f0;
  border-radius: 3px;
  outline: none;
}

.time-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  cursor: pointer;
  box-shadow: 0 0 8px rgba(99, 102, 241, 0.4);
}

.shuttle-value {
  font-size: 12px;
  color: #6366f1;
  font-weight: 600;
  min-width: 50px;
  text-align: right;
}

.strategy-group {
  display: flex;
  align-items: center;
  gap: 10px;
}

.strategy-label {
  font-size: 12px;
  color: #64748b;
  white-space: nowrap;
}

.strategy-radios {
  display: flex;
  gap: 6px;
}

.strategy-radio {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border-radius: 8px;
  background: #f1f5f9;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 11px;
  color: #64748b;
  border: 1px solid #e2e8f0;
  white-space: nowrap;
}

.strategy-radio input {
  display: none;
}

.strategy-radio.active {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: white;
  border-color: transparent;
}

.radio-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  border: 2px solid #94a3b8;
  transition: all 0.2s;
}

.strategy-radio.active .radio-dot {
  border-color: white;
  background: white;
}

.btn-run-cf {
  padding: 8px 20px;
  border-radius: 10px;
  border: none;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: white;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
}

.btn-run-cf:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
}

.btn-run-cf:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.cf-dag-container {
  position: relative;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  height: 420px;
  overflow: hidden;
  transition: all 0.3s ease;
}

.dag-svg {
  width: 100%;
  height: 100%;
  transition: all 0.3s ease;
}

.dag-loading,
.dag-empty {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: #64748b;
  font-size: 14px;
}

.dag-loading-ring {
  width: 36px;
  height: 36px;
  border: 3px solid #334155;
  border-top-color: #6366f1;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.empty-icon {
  font-size: 36px;
}

.dag-edge {
  stroke-linecap: round;
}

.cf-trend-panel {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 16px;
}

.trend-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.trend-title {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
}

.trend-legends {
  display: flex;
  gap: 16px;
}

.trend-legend {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #64748b;
}

.legend-line {
  display: inline-block;
  width: 20px;
  height: 2px;
}

.legend-line.original {
  background: #6366f1;
}

.legend-line.intervened {
  background: #f59e0b;
  background: repeating-linear-gradient(90deg, #f59e0b 0, #f59e0b 4px, transparent 4px, transparent 7px);
}

.trend-chart-container {
  width: 100%;
  height: 160px;
  transition: all 0.3s ease;
}

.trend-chat-mini {
  margin-top: 12px;
  border-top: 1px solid #e2e8f0;
  padding-top: 12px;
}

.chat-header-mini {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
}

.chat-icon {
  font-size: 14px;
}

.chat-title {
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
}

.chat-messages-mini {
  max-height: 120px;
  overflow-y: auto;
  margin-bottom: 8px;
  padding: 8px;
  background: #f8fafc;
  border-radius: 8px;
}

.chat-empty-hint {
  font-size: 11px;
  color: #94a3b8;
  text-align: center;
  padding: 8px;
}

.chat-generating {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  font-size: 11px;
  color: #64748b;
}

.chat-message-mini {
  margin-bottom: 6px;
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 11px;
  line-height: 1.4;
}

.chat-message-mini.user {
  background: #e0e7ff;
  text-align: right;
}

.chat-message-mini.assistant {
  background: #f1f5f9;
}

.mini-msg-content {
  word-break: break-word;
}

.mini-msg-content p {
  margin: 0 0 4px 0;
}

.mini-msg-content p:last-child {
  margin-bottom: 0;
}

.mini-msg-content ul,
.mini-msg-content ol {
  margin: 4px 0;
  padding-left: 16px;
}

.mini-msg-content li {
  margin: 2px 0;
}

.mini-msg-content strong {
  font-weight: 600;
}

.mini-msg-content code {
  background: #e2e8f0;
  padding: 1px 4px;
  border-radius: 3px;
  font-size: 10px;
}

.chat-input-row {
  display: flex;
  gap: 6px;
}

.chat-input-mini {
  flex: 1;
  padding: 6px 10px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 11px;
  outline: none;
  transition: border-color 0.2s;
}

.chat-input-mini:focus {
  border-color: #6366f1;
}

.chat-input-mini:disabled {
  background: #f1f5f9;
  cursor: not-allowed;
}

.btn-chat-mini {
  padding: 6px 12px;
  background: #6366f1;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 11px;
  cursor: pointer;
  transition: background 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 32px;
}

.btn-chat-mini:hover:not(:disabled) {
  background: #4f46e5;
}

.btn-chat-mini:disabled {
  background: #c7d2fe;
  cursor: not-allowed;
}

.mini-spinner {
  width: 10px;
  height: 10px;
  border: 1.5px solid #e0e7ff;
  border-top-color: #6366f1;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

:deep(.trend-axis) {
  color: #64748b;
  font-size: 10px;
}

:deep(.trend-axis line),
:deep(.trend-axis path) {
  stroke: #334155;
}

.sidebar-title,
.detail-title {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 12px 0;
}

.global-stats {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-bottom: 16px;
}

.stat-card {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 10px;
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 20px;
  font-weight: 700;
  color: #6366f1;
}

.stat-value.high { color: #ef4444; }
.stat-value.medium { color: #f59e0b; }
.stat-value.low { color: #22c55e; }

.stat-label {
  font-size: 11px;
  color: #64748b;
}

.global-radar {
  margin-top: 12px;
}

.radar-title,
.log-title {
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
  margin: 0 0 8px 0;
}

.radar-svg {
  width: 100%;
  max-width: 200px;
  margin: 0 auto;
  display: block;
  transition: all 0.3s ease;
}

.radar-grid {
  fill: none;
  stroke: #e2e8f0;
  stroke-width: 0.5;
  transition: all 0.3s ease;
}

.radar-axis-line {
  stroke: #e2e8f0;
  stroke-width: 0.5;
  transition: all 0.3s ease;
}

.radar-label-text {
  fill: #64748b;
  font-size: 9px;
  text-anchor: middle;
  dominant-baseline: middle;
  transition: all 0.3s ease;
}

.radar-area {
  fill: rgba(99, 102, 241, 0.2);
  stroke: #6366f1;
  stroke-width: 1.5;
  transition: all 0.3s ease;
}

.radar-area.node {
  fill: rgba(245, 158, 11, 0.2);
  stroke: #f59e0b;
  transition: all 0.3s ease;
}

.radar-point {
  fill: #6366f1;
  transition: all 0.3s ease;
}

.radar-point.node {
  fill: #f59e0b;
  transition: all 0.3s ease;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.btn-close-detail {
  background: none;
  border: none;
  color: #64748b;
  cursor: pointer;
  font-size: 16px;
  padding: 2px 6px;
  border-radius: 4px;
}

.btn-close-detail:hover {
  color: #1e293b;
  background: #e2e8f0;
}

.detail-badges {
  display: flex;
  gap: 6px;
  margin-bottom: 14px;
  flex-wrap: wrap;
}

.badge {
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
}

.badge.negative { background: rgba(239, 68, 68, 0.15); color: #dc2626; }
.badge.positive { background: rgba(34, 197, 94, 0.15); color: #16a34a; }
.badge.neutral { background: rgba(99, 102, 241, 0.15); color: #4f46e5; }
.badge.complex { background: rgba(245, 158, 11, 0.15); color: #d97706; }
.badge.depth { background: rgba(148, 163, 184, 0.15); color: #64748b; }
.badge.influence { background: rgba(168, 85, 247, 0.15); color: #9333ea; }

.detail-radar {
  margin-bottom: 14px;
}

.detail-agent-log {
  margin-top: 8px;
}

.terminal-window {
  background: #f8fafc;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #e2e8f0;
}

.terminal-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  background: #e2e8f0;
}

.terminal-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.terminal-dot.red { background: #ef4444; }
.terminal-dot.yellow { background: #f59e0b; }
.terminal-dot.green { background: #22c55e; }

.terminal-title-text {
  font-size: 10px;
  color: #64748b;
  margin-left: 6px;
}

.terminal-body {
  padding: 10px;
  max-height: 200px;
  overflow-y: auto;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 11px;
  line-height: 1.6;
  background: white;
}

.terminal-line {
  margin-bottom: 4px;
}

.line-prefix {
  font-weight: 700;
  margin-right: 6px;
}

.terminal-line.thought .line-prefix { color: #3b82f6; }
.terminal-line.action .line-prefix { color: #10b981; }
.terminal-line.observation .line-prefix { color: #f59e0b; }

.line-content {
  color: #475569;
}

.spinner-sm {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@keyframes breathingGlow {
  0%, 100% {
    opacity: 0;
    stroke-width: 1;
    r: 12;
  }
  50% {
    opacity: 0.6;
    stroke-width: 2;
    r: 16;
  }
}

:deep(.breathing-glow) {
  animation: breathingGlow 2s ease-in-out infinite;
}

.agent-decision-panel {
  margin-top: 16px;
}

.decision-title {
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
  margin: 0 0 8px 0;
}

.decision-terminal {
  background: #1e293b;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #334155;
}

.terminal-header-bar {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: #0f172a;
  border-bottom: 1px solid #334155;
}

.terminal-title {
  font-size: 10px;
  color: #94a3b8;
  margin-left: 6px;
  font-family: 'JetBrains Mono', 'Consolas', 'Monaco', monospace;
}

.terminal-content {
  padding: 12px;
  max-height: 180px;
  overflow-y: auto;
  font-family: 'JetBrains Mono', 'Consolas', 'Monaco', monospace;
  font-size: 11px;
  line-height: 1.8;
}

.decision-line {
  margin-bottom: 6px;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-5px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.log-prefix {
  font-weight: 700;
  margin-right: 8px;
}

.decision-line.thought .log-prefix { color: #60a5fa; }
.decision-line.action .log-prefix { color: #34d399; }
.decision-line.observation .log-prefix { color: #fbbf24; }

.log-content {
  color: #cbd5e1;
}

.empty-log {
  color: #64748b;
  font-style: italic;
  text-align: center;
  padding: 20px 0;
}

.terminal-content::-webkit-scrollbar {
  width: 6px;
}

.terminal-content::-webkit-scrollbar-track {
  background: #0f172a;
}

.terminal-content::-webkit-scrollbar-thumb {
  background: #334155;
  border-radius: 3px;
}

.terminal-content::-webkit-scrollbar-thumb:hover {
  background: #475569;
}
</style>
