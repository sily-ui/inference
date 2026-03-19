<template>
  <div class="simulation-panel">
    <div class="sim-header-card">
      <div class="header-top">
        <div class="header-left">
          <span class="card-title">国内舆情环境模拟</span>
          <span class="sim-id mono">{{ simulationId || 'NO_SIM' }}</span>
        </div>
        <div class="header-right">
          <span class="status-badge" :class="statusClass">{{ statusText }}</span>
        </div>
      </div>
      
      <div class="header-stats">
        <div class="stat-item">
          <span class="stat-label">模拟轮数</span>
          <span class="stat-value mono">{{ currentRound }}<span class="stat-total">/{{ totalRounds }}</span></span>
        </div>
        <div class="stat-item">
          <span class="stat-label">模拟时长</span>
          <span class="stat-value mono">{{ estimatedTime }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">已用时长</span>
          <span class="stat-value mono">{{ elapsedTime }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">事件总数</span>
          <span class="stat-value mono">{{ uniqueActions.length }}</span>
        </div>
      </div>
      
      <div class="progress-section">
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
        </div>
        <span class="progress-text">{{ progressPercent }}%</span>
      </div>
    </div>

    <div class="chat-area" ref="chatContainer">
      <div class="chat-messages">
        <TransitionGroup name="message">
          <div 
            v-for="msg in uniqueActions" 
            :key="msg._uniqueId"
            class="chat-message"
            :class="msg.type"
          >
            <div class="msg-avatar">{{ (msg.agent_name || 'A')[0] }}</div>
            <div class="msg-content">
              <div class="msg-header">
                <span class="msg-name">{{ msg.agent_name || 'Agent' }}</span>
                <span class="msg-time">R{{ msg.round_num }} · {{ formatTime(msg.timestamp) }}</span>
              </div>
              <div class="msg-text">{{ msg.content }}</div>
            </div>
          </div>
        </TransitionGroup>
        
        <div v-if="uniqueActions.length === 0" class="empty-state">
          <div class="pulse-ring"></div>
          <span>等待模拟开始...</span>
        </div>
      </div>
    </div>

    <div class="action-bar">
      <button 
        class="btn-primary"
        :disabled="phase !== 2 || isGeneratingReport"
        @click="handleNextStep"
      >
        <span v-if="isGeneratingReport" class="spinner"></span>
        {{ isGeneratingReport ? '生成中...' : '生成报告' }}
        <span v-if="!isGeneratingReport">→</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { startSimulation, stopSimulation, getRunStatus, getRunStatusDetail } from '../api/simulation'
import { generateReport } from '../api/report'

const props = defineProps({
  simulationId: String,
  maxRounds: Number,
  minutesPerRound: { type: Number, default: 60 },
  projectData: Object,
  graphData: Object,
  systemLogs: Array
})

const emit = defineEmits(['go-back', 'next-step', 'add-log', 'update-status'])

const router = useRouter()

const phase = ref(0)
const isGeneratingReport = ref(false)
const runStatus = ref({})
const allActions = ref([])
const actionIds = ref(new Set())
const seenContents = ref(new Set())
const chatContainer = ref(null)

const currentRound = computed(() => {
  if (runStatus.value.current_round > 0) {
    return runStatus.value.current_round
  }
  const maxRound = allActions.value.reduce((max, action) => {
    return action.round_num > max ? action.round_num : max
  }, 0)
  return maxRound
})

const totalRounds = computed(() => {
  return runStatus.value.total_rounds || props.maxRounds || 15
})

const progressPercent = computed(() => {
  if (!totalRounds.value) return 0
  return Math.round((currentRound.value / totalRounds.value) * 100)
})

const estimatedTime = computed(() => {
  const hours = runStatus.value.total_simulation_hours || 0
  if (hours >= 24) {
    const days = Math.floor(hours / 24)
    const remainingHours = hours % 24
    return `${days}d ${remainingHours}h`
  }
  return `${hours}h 0m`
})

const elapsedTime = computed(() => {
  const hours = runStatus.value.simulated_hours || 0
  if (hours >= 24) {
    const days = Math.floor(hours / 24)
    const remainingHours = hours % 24
    return `${days}d ${remainingHours}h`
  }
  return `${hours}h 0m`
})

const statusClass = computed(() => {
  if (phase.value === 0) return 'pending'
  if (phase.value === 1) return 'running'
  if (phase.value === 2) return 'completed'
  return ''
})

const statusText = computed(() => {
  if (phase.value === 0) return '等待中'
  if (phase.value === 1) return '模拟中'
  if (phase.value === 2) return '已完成'
  return ''
})

const uniqueActions = computed(() => {
  const seen = new Set()
  return allActions.value
    .filter(a => {
      const content = extractContent(a)
      if (!content || seen.has(content)) return false
      seen.add(content)
      return true
    })
    .map(a => ({
      ...a,
      content: extractContent(a),
      type: getMsgType(a.action_type)
    }))
})

const extractContent = (action) => {
  if (action.action_type === 'CREATE_POST' && action.action_args?.content) {
    return action.action_args.content
  }
  if (action.action_type === 'CREATE_COMMENT' && action.action_args?.content) {
    return action.action_args.content
  }
  if (action.action_type === 'QUOTE_POST' && action.action_args?.quote_content) {
    return action.action_args.quote_content
  }
  return null
}

const getMsgType = (type) => {
  if (['CREATE_POST', 'QUOTE_POST'].includes(type)) return 'post'
  if (['CREATE_COMMENT'].includes(type)) return 'comment'
  return 'action'
}

const formatTime = (timestamp) => {
  if (!timestamp) return ''
  try {
    return new Date(timestamp).toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit' })
  } catch { return '' }
}

const addLog = (msg) => emit('add-log', msg)

const resetAllState = () => {
  phase.value = 0
  runStatus.value = {}
  allActions.value = []
  actionIds.value = new Set()
  seenContents.value = new Set()
  stopPolling()
}

const doStartSimulation = async () => {
  if (!props.simulationId) return
  
  addLog('正在检查模拟状态...')
  emit('update-status', 'processing')
  
  try {
    // 先检查模拟是否已经在运行中
    const statusRes = await getRunStatus(props.simulationId)
    
    if (statusRes.success && statusRes.data) {
      const runnerStatus = statusRes.data.runner_status
      
      // 如果模拟已经在运行中，直接开始轮询
      if (runnerStatus === 'running') {
        addLog('✓ 模拟已在运行中，继续监视...')
        runStatus.value = statusRes.data
        phase.value = 1
        startStatusPolling()
        startDetailPolling()
        return
      }
      
      // 如果模拟已完成，显示完成状态
      if (runnerStatus === 'completed' || runnerStatus === 'stopped') {
        addLog('✓ 模拟已完成')
        runStatus.value = statusRes.data
        phase.value = 2
        emit('update-status', 'completed')
        return
      }
    }
    
    // 模拟未运行，需要启动
    resetAllState()
    addLog('正在启动模拟...')
    
    const params = {
      simulation_id: props.simulationId,
      platform: 'parallel',
      force: true,
      enable_graph_memory_update: true
    }
    
    if (props.maxRounds) {
      params.max_rounds = props.maxRounds
    }
    
    const res = await startSimulation(params)
    
    if (res.success && res.data) {
      addLog('✓ 模拟引擎启动成功')
      phase.value = 1
      runStatus.value = res.data
      startStatusPolling()
      startDetailPolling()
    } else {
      addLog(`✗ 启动失败: ${res.error || '未知错误'}`)
      emit('update-status', 'error')
    }
  } catch (err) {
    addLog(`✗ 启动异常: ${err.message}`)
    emit('update-status', 'error')
  }
}

let statusTimer = null
let detailTimer = null

const startStatusPolling = () => {
  statusTimer = setInterval(fetchRunStatus, 2000)
}

const startDetailPolling = () => {
  detailTimer = setInterval(fetchRunStatusDetail, 3000)
}

const stopPolling = () => {
  if (statusTimer) { clearInterval(statusTimer); statusTimer = null }
  if (detailTimer) { clearInterval(detailTimer); detailTimer = null }
}

const prevRound = ref(0)

const fetchRunStatus = async () => {
  if (!props.simulationId) return
  
  try {
    const res = await getRunStatus(props.simulationId)

    if (res.success && res.data) {
      runStatus.value = res.data

      if (res.data.current_round > prevRound.value) {
        addLog(`R${res.data.current_round}/${res.data.total_rounds} | 事件: ${res.data.actions_count || 0}`)
        prevRound.value = res.data.current_round
      }

      const isCompleted = res.data.runner_status === 'completed' ||
                          res.data.runner_status === 'stopped' ||
                          res.data.current_round >= res.data.total_rounds

      if (isCompleted) {
        addLog('✓ 模拟已完成')
        phase.value = 2
        stopPolling()
        emit('update-status', 'completed')
      }
    }
  } catch (err) {
    console.warn('获取状态失败:', err)
  }
}

const fetchRunStatusDetail = async () => {
  if (!props.simulationId) return
  
  try {
    const res = await getRunStatusDetail(props.simulationId)
    
    if (res.success && res.data) {
      const serverActions = res.data.all_actions || []
      
      serverActions.forEach(action => {
        const actionId = action.id || `${action.timestamp}-${action.platform}-${action.agent_id}-${action.action_type}`
        
        if (!actionIds.value.has(actionId)) {
          actionIds.value.add(actionId)
          allActions.value.push({
            ...action,
            _uniqueId: actionId
          })
        }
      })
      
      nextTick(() => {
        if (chatContainer.value) {
          chatContainer.value.scrollTop = chatContainer.value.scrollHeight
        }
      })
    }
  } catch (err) {
    console.warn('获取详情失败:', err)
  }
}

const handleNextStep = async () => {
  if (!props.simulationId || isGeneratingReport.value) return
  
  isGeneratingReport.value = true
  addLog('正在生成报告...')
  
  try {
    const res = await generateReport({
      simulation_id: props.simulationId,
      force_regenerate: true
    })
    
    if (res.success && res.data) {
      addLog(`✓ 报告生成任务已启动`)
      router.push({ name: 'Report', params: { reportId: res.data.report_id } })
    } else {
      addLog(`✗ 生成失败: ${res.error || '未知错误'}`)
      isGeneratingReport.value = false
    }
  } catch (err) {
    addLog(`✗ 生成异常: ${err.message}`)
    isGeneratingReport.value = false
  }
}

onMounted(() => {
  addLog('Step3 模拟运行初始化')
  addLog(`simulationId: ${props.simulationId}`)
  addLog(`maxRounds: ${props.maxRounds}`)
  if (props.simulationId) {
    doStartSimulation()
  } else {
    addLog('错误: 缺少 simulationId，无法启动模拟')
  }
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.simulation-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #fff;
  font-family: 'Space Grotesk', 'Noto Sans SC', system-ui, sans-serif;
}

.sim-header-card {
  background: #FAFAFA;
  border-bottom: 1px solid #EAEAEA;
  padding: 16px 20px;
}

.header-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #000;
}

.sim-id {
  font-size: 11px;
  color: #999;
  background: #F0F0F0;
  padding: 2px 8px;
  border-radius: 4px;
}

.status-badge {
  font-size: 12px;
  font-weight: 500;
  padding: 4px 10px;
  border-radius: 4px;
}

.status-badge.pending { background: #F0F0F0; color: #999; }
.status-badge.running { background: #000; color: #fff; }
.status-badge.completed { background: #1a936f; color: #fff; }

.header-stats {
  display: flex;
  gap: 24px;
  margin-bottom: 12px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stat-label {
  font-size: 11px;
  color: #999;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.stat-value {
  font-size: 18px;
  font-weight: 600;
  color: #000;
}

.stat-total {
  font-size: 14px;
  color: #999;
  font-weight: 400;
}

.progress-section {
  display: flex;
  align-items: center;
  gap: 12px;
}

.progress-bar {
  flex: 1;
  height: 6px;
  background: #EAEAEA;
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #000;
  border-radius: 3px;
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 13px;
  font-weight: 600;
  color: #000;
  min-width: 40px;
  text-align: right;
}

.chat-area {
  flex: 1;
  overflow-y: auto;
  padding: 16px 20px;
}

.chat-messages {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.chat-message {
  display: flex;
  gap: 10px;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.msg-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #000;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
  flex-shrink: 0;
}

.msg-content {
  flex: 1;
  background: #F5F5F5;
  border-radius: 12px;
  padding: 10px 14px;
}

.chat-message.post .msg-content {
  background: #000;
  color: #fff;
}

.chat-message.post .msg-name,
.chat-message.post .msg-time {
  color: rgba(255,255,255,0.7);
}

.chat-message.post .msg-text {
  color: #fff;
}

.msg-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.msg-name {
  font-size: 13px;
  font-weight: 600;
  color: #000;
}

.msg-time {
  font-size: 11px;
  color: #999;
}

.msg-text {
  font-size: 14px;
  line-height: 1.5;
  color: #333;
  word-break: break-word;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #999;
  gap: 12px;
}

.pulse-ring {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: 2px solid #EAEAEA;
  border-top-color: #000;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.action-bar {
  padding: 16px 20px;
  border-top: 1px solid #EAEAEA;
  display: flex;
  justify-content: flex-end;
}

.btn-primary {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: #000;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary:hover:not(:disabled) {
  background: #333;
}

.btn-primary:disabled {
  background: #CCC;
  cursor: not-allowed;
}

.spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.mono {
  font-family: 'SF Mono', 'Consolas', monospace;
}
</style>
