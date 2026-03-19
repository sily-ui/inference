<template>
  <div class="main-view">
    <header class="app-header">
      <div class="header-left">
        <div class="brand" @click="router.push('/')">MIROFISH</div>
      </div>
      
      <div class="header-center">
        <StepProgressBar 
          :steps="stepNames" 
          :currentStep="currentStep - 1"
          @step-click="handleProgressBarClick"
        />
      </div>

      <div class="header-right">
        <span class="status-indicator" :class="statusClass">
          <span class="dot"></span>
          {{ statusText }}
        </span>
      </div>
    </header>

    <main class="content-area">
      <div class="panel-wrapper left" :style="leftPanelStyle">
        <GraphPanel 
          :graphData="graphData"
          :loading="graphLoading"
          :currentPhase="currentPhase"
          @refresh="refreshGraph"
          @toggle-maximize="toggleMaximize('graph')"
        />
      </div>

      <div class="panel-wrapper right" :style="rightPanelStyle">
        <Step1GraphBuild 
          v-if="currentStep === 1"
          :currentPhase="currentPhase"
          :projectData="projectData"
          :ontologyProgress="ontologyProgress"
          :buildProgress="buildProgress"
          :graphData="graphData"
          :systemLogs="systemLogs"
          @next-step="handleNextStep"
        />
        <Step2EnvSetup
          v-else-if="currentStep === 2"
          :projectData="projectData"
          :graphData="graphData"
          :systemLogs="systemLogs"
          @go-back="handleGoBack"
          @next-step="handleNextStep"
          @add-log="addLog"
        />
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import GraphPanel from '../components/GraphPanel.vue'
import StepProgressBar from '../components/StepProgressBar.vue'
import Step1GraphBuild from '../components/Step1GraphBuild.vue'
import Step2EnvSetup from '../components/Step2EnvSetup.vue'
import { generateOntology, generateOntologyFromText, getProject, buildGraph, getTaskStatus, getGraphData } from '../api/graph'
import { getPendingUpload, clearPendingUpload } from '../store/pendingUpload'

const route = useRoute()
const router = useRouter()

const viewMode = ref('split')

const currentStep = ref(1)
const stepNames = ['本体生成', '图谱构建', '模拟', '报告', '舆情预测']

const steps = ref([
  { name: '本体生成', status: 'pending', data: null, needRerun: false },
  { name: '图谱构建', status: 'pending', data: null, needRerun: false },
  { name: '模拟', status: 'pending', data: null, needRerun: false },
  { name: '报告', status: 'pending', data: null, needRerun: false },
  { name: '舆情预测', status: 'pending', data: null, needRerun: false },
])

const markStepCompleted = (idx, data = null) => {
  steps.value[idx].status = 'completed'
  steps.value[idx].data = data
  steps.value[idx].needRerun = false
}

const markStepRunning = (idx) => {
  steps.value[idx].status = 'running'
  steps.value.forEach((s, i) => {
    if (i < idx && s.status === 'viewing') {
      s.status = 'completed'
    }
  })
}

// 检查步骤是否需要重新运行
const checkNeedRerun = (idx) => {
  return steps.value[idx]?.needRerun || false
}

// 步骤切换时检查是否需要重新运行
const handleStepChange = (newStep) => {
  if (checkNeedRerun(newStep - 1)) {
    addLog(`Step ${newStep} 需要重新运行，将重新初始化...`)
  }
}

// 处理进度条点击 - 跳转到对应视图
const handleProgressBarClick = (stepIdx) => {
  const targetStep = stepIdx + 1
  
  if (targetStep === 1 || targetStep === 2) {
    currentStep.value = targetStep
  } else if (targetStep === 3 && projectData.value?.simulation_id) {
    router.push({ name: 'Simulation', params: { simulationId: projectData.value.simulation_id } })
  } else if (targetStep === 4 && projectData.value?.simulation_id) {
    const simulationId = projectData.value.simulation_id
    router.push({ name: 'Simulation', params: { simulationId } })
    setTimeout(() => {
      router.push({ name: 'Report', params: { reportId: `report_${simulationId.split('_')[1]}` } })
    }, 100)
  } else if (targetStep === 5 && projectData.value?.simulation_id) {
    const simulationId = projectData.value.simulation_id
    router.push({ name: 'Simulation', params: { simulationId } })
    setTimeout(() => {
      router.push({ name: 'Prediction', params: { reportId: `report_${simulationId.split('_')[1]}` } })
    }, 100)
  }
}

// Data State
const currentProjectId = ref(route.params.projectId)
const loading = ref(false)
const graphLoading = ref(false)
const error = ref('')
const projectData = ref(null)
const graphData = ref(null)
const currentPhase = ref(-1) // -1: Upload, 0: Ontology, 1: Build, 2: Complete
const ontologyProgress = ref(null)
const buildProgress = ref(null)
const systemLogs = ref([])

// Polling timers
let pollTimer = null
let graphPollTimer = null

// --- Computed Layout Styles ---
const leftPanelStyle = computed(() => {
  if (viewMode.value === 'graph') return { width: '100%', opacity: 1, transform: 'translateX(0)' }
  if (viewMode.value === 'workbench') return { width: '0%', opacity: 0, transform: 'translateX(-20px)' }
  return { width: '50%', opacity: 1, transform: 'translateX(0)' }
})

const rightPanelStyle = computed(() => {
  if (viewMode.value === 'workbench') return { width: '100%', opacity: 1, transform: 'translateX(0)' }
  if (viewMode.value === 'graph') return { width: '0%', opacity: 0, transform: 'translateX(20px)' }
  return { width: '50%', opacity: 1, transform: 'translateX(0)' }
})

// --- Status Computed ---
const statusClass = computed(() => {
  if (error.value) return 'error'
  if (currentPhase.value >= 2) return 'completed'
  return 'processing'
})

const statusText = computed(() => {
  if (error.value) return 'Error'
  if (currentPhase.value >= 2) return 'Ready'
  if (currentPhase.value === 1) return 'Building Graph'
  if (currentPhase.value === 0) return 'Generating Ontology'
  return 'Initializing'
})

// --- Helpers ---
const addLog = (msg) => {
  const time = new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }) + '.' + new Date().getMilliseconds().toString().padStart(3, '0')
  systemLogs.value.push({ time, msg })
  // Keep last 100 logs
  if (systemLogs.value.length > 100) {
    systemLogs.value.shift()
  }
}

// --- Layout Methods ---
const toggleMaximize = (target) => {
  if (viewMode.value === target) {
    viewMode.value = 'split'
  } else {
    viewMode.value = target
  }
}

const handleNextStep = (params = {}) => {
  // 检查当前步骤是否需要重新运行
  if (checkNeedRerun(currentStep.value - 1)) {
    addLog(`Step ${currentStep.value} 之前被标记需要重新运行，已完成重新运行`)
    // 清除重新运行标记
    steps.value[currentStep.value - 1].needRerun = false
  }
  
  // 标记当前步骤完成
  markStepCompleted(currentStep.value - 1, params)
  
  if (currentStep.value < 5) {
    currentStep.value++
    markStepRunning(currentStep.value - 1)
    addLog(`进入 Step ${currentStep.value}: ${stepNames[currentStep.value - 1]}`)
    
    // 如果是从 Step 2 进入 Step 3，记录模拟轮数配置
    if (currentStep.value === 3 && params.maxRounds) {
      addLog(`自定义模拟轮数: ${params.maxRounds} 轮`)
    }
  }
}

const handleGoBack = () => {
  if (currentStep.value > 1) {
    // 标记当前步骤需要重新运行
    steps.value[currentStep.value - 1].needRerun = true
    currentStep.value--
    addLog(`返回 Step ${currentStep.value}: ${stepNames[currentStep.value - 1]}`)
  }
}

// --- Data Logic ---

const initProject = async () => {
  addLog('Project view initialized.')
  if (currentProjectId.value === 'new') {
    await handleNewProject()
  } else {
    await loadProject()
  }
}

const handleNewProject = async () => {
  const pending = getPendingUpload()
  if (!pending.isPending) {
    error.value = 'No pending data found.'
    addLog('Error: No pending data found for new project.')
    return
  }
  
  try {
    loading.value = true
    currentPhase.value = 0
    ontologyProgress.value = { message: 'Uploading and analyzing docs...' }
    
    let res
    
    if (pending.dataSource === 'social' && pending.tavilyData) {
      addLog('Starting ontology generation from Tavily search results...')
      res = await generateOntologyFromText({
        text: pending.tavilyData.extracted_text,
        simulation_requirement: pending.simulationRequirement,
        summary: pending.tavilyData.summary,
        key_points: pending.tavilyData.key_points,
        sources: pending.tavilyData.sources
      })
    } else if (pending.files.length > 0) {
      addLog('Starting ontology generation: Uploading files...')
      const formData = new FormData()
      pending.files.forEach(f => formData.append('files', f))
      formData.append('simulation_requirement', pending.simulationRequirement)
      res = await generateOntology(formData)
    } else {
      error.value = 'No files or Tavily data found.'
      addLog('Error: No files or Tavily data found.')
      return
    }
    
    if (res.success) {
      clearPendingUpload()
      currentProjectId.value = res.data.project_id
      projectData.value = res.data
      
      router.replace({ name: 'Process', params: { projectId: res.data.project_id } })
      ontologyProgress.value = null
      addLog(`Ontology generated successfully for project ${res.data.project_id}`)
      await startBuildGraph()
    } else {
      error.value = res.error || 'Ontology generation failed'
      addLog(`Error generating ontology: ${error.value}`)
    }
  } catch (err) {
    error.value = err.message
    addLog(`Exception in handleNewProject: ${err.message}`)
  } finally {
    loading.value = false
  }
}

const loadProject = async () => {
  try {
    loading.value = true
    addLog(`Loading project ${currentProjectId.value}...`)
    const res = await getProject(currentProjectId.value)
    if (res.success) {
      projectData.value = res.data
      updatePhaseByStatus(res.data.status)
      addLog(`Project loaded. Status: ${res.data.status}`)
      
      if (res.data.status === 'ontology_generated' && !res.data.graph_id) {
        await startBuildGraph()
      } else if (res.data.status === 'graph_building' && res.data.graph_build_task_id) {
        currentPhase.value = 1
        startPollingTask(res.data.graph_build_task_id)
        startGraphPolling()
      } else if (res.data.status === 'graph_completed' && res.data.graph_id) {
        currentPhase.value = 2
        await loadGraph(res.data.graph_id)
      }
    } else {
      error.value = res.error
      addLog(`Error loading project: ${res.error}`)
    }
  } catch (err) {
    error.value = err.message
    addLog(`Exception in loadProject: ${err.message}`)
  } finally {
    loading.value = false
  }
}

const updatePhaseByStatus = (status) => {
  switch (status) {
    case 'created':
    case 'ontology_generated': currentPhase.value = 0; break;
    case 'graph_building': currentPhase.value = 1; break;
    case 'graph_completed': currentPhase.value = 2; break;
    case 'failed': error.value = 'Project failed'; break;
  }
}

const startBuildGraph = async () => {
  try {
    currentPhase.value = 1
    buildProgress.value = { progress: 0, message: 'Starting build...' }
    addLog('Initiating graph build...')
    
    const res = await buildGraph({ project_id: currentProjectId.value })
    if (res.success) {
      addLog(`Graph build task started. Task ID: ${res.data.task_id}`)
      startGraphPolling()
      startPollingTask(res.data.task_id)
    } else {
      error.value = res.error
      addLog(`Error starting build: ${res.error}`)
    }
  } catch (err) {
    error.value = err.message
    addLog(`Exception in startBuildGraph: ${err.message}`)
  }
}

const startGraphPolling = () => {
  addLog('Started polling for graph data...')
  fetchGraphData()
  graphPollTimer = setInterval(fetchGraphData, 10000)
}

const fetchGraphData = async () => {
  try {
    // Refresh project info to check for graph_id
    const projRes = await getProject(currentProjectId.value)
    if (projRes.success && projRes.data.graph_id) {
      const gRes = await getGraphData(projRes.data.graph_id)
      if (gRes.success) {
        graphData.value = gRes.data
        const nodeCount = gRes.data.node_count || gRes.data.nodes?.length || 0
        const edgeCount = gRes.data.edge_count || gRes.data.edges?.length || 0
        addLog(`Graph data refreshed. Nodes: ${nodeCount}, Edges: ${edgeCount}`)
      }
    }
  } catch (err) {
    console.warn('Graph fetch error:', err)
  }
}

const startPollingTask = (taskId) => {
  pollTaskStatus(taskId)
  pollTimer = setInterval(() => pollTaskStatus(taskId), 2000)
}

const pollTaskStatus = async (taskId) => {
  try {
    const res = await getTaskStatus(taskId)
    if (res.success) {
      const task = res.data
      
      // Log progress message if it changed
      if (task.message && task.message !== buildProgress.value?.message) {
        addLog(task.message)
      }
      
      buildProgress.value = { progress: task.progress || 0, message: task.message }
      
      if (task.status === 'completed') {
        addLog('Graph build task completed.')
        stopPolling()
        stopGraphPolling() // Stop polling, do final load
        currentPhase.value = 2
        
        // Final load
        const projRes = await getProject(currentProjectId.value)
        if (projRes.success && projRes.data.graph_id) {
            projectData.value = projRes.data
            await loadGraph(projRes.data.graph_id)
        }
      } else if (task.status === 'failed') {
        stopPolling()
        error.value = task.error
        addLog(`Graph build task failed: ${task.error}`)
      }
    }
  } catch (e) {
    console.error(e)
  }
}

const loadGraph = async (graphId) => {
  graphLoading.value = true
  addLog(`Loading full graph data: ${graphId}`)
  try {
    const res = await getGraphData(graphId)
    if (res.success) {
      graphData.value = res.data
      addLog('Graph data loaded successfully.')
    } else {
      addLog(`Failed to load graph data: ${res.error}`)
    }
  } catch (e) {
    addLog(`Exception loading graph: ${e.message}`)
  } finally {
    graphLoading.value = false
  }
}

const refreshGraph = () => {
  if (projectData.value?.graph_id) {
    addLog('Manual graph refresh triggered.')
    loadGraph(projectData.value.graph_id)
  }
}

const stopPolling = () => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

const stopGraphPolling = () => {
  if (graphPollTimer) {
    clearInterval(graphPollTimer)
    graphPollTimer = null
    addLog('Graph polling stopped.')
  }
}

// 监听步骤变化，检查是否需要重新运行
watch(currentStep, (newStep, oldStep) => {
  // 当进入新步骤时，检查前一步是否需要重新运行
  const prevStep = newStep - 1
  if (prevStep >= 0 && steps.value[prevStep]?.needRerun) {
    addLog(`Step ${newStep}: 前一步骤已变化，需要重新加载数据`)
    // 重新加载该步骤需要的数据
    if (newStep === 1) {
      // 重新加载项目
      loadProject()
    } else if (newStep === 2) {
      // Step 2 需要项目数据
      if (projectData.value?.project_id) {
        loadProject()
      }
    }
  }
})

onMounted(() => {
  initProject()
})

onUnmounted(() => {
  stopPolling()
  stopGraphPolling()
})
</script>

<style scoped>
.main-view {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #FFF;
  overflow: hidden;
  font-family: 'Space Grotesk', 'Noto Sans SC', system-ui, sans-serif;
}

/* Header */
.app-header {
  height: 60px;
  border-bottom: 1px solid #EAEAEA;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  background: #FFF;
  z-index: 100;
  position: relative;
}

.header-center {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
}

/* 步骤进度条样式 */
.step-progress-bar {
  display: flex;
  align-items: center;
  gap: 4px;
}

.progress-step {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.progress-step.pending {
  cursor: not-allowed;
  opacity: 0.5;
}

.progress-step.active .step-circle {
  background: #FF6B35;
  color: #fff;
  box-shadow: 0 0 0 3px rgba(255, 107, 53, 0.3);
}

.progress-step.completed .step-circle {
  background: #1A936F;
  color: #fff;
}

.progress-step.viewing .step-circle {
  background: #3B82F6;
  color: #fff;
}

.progress-step.need-rerun .step-circle {
  background: #F59E0B;
  color: #fff;
}

.progress-step.need-rerun .rerun-icon {
  font-size: 12px;
}

.step-circle {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #4B5563;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 600;
  transition: all 0.2s ease;
}

.step-label {
  font-size: 11px;
  color: #9CA3AF;
  white-space: nowrap;
}

.progress-step.active .step-label,
.progress-step.completed .step-label,
.progress-step.viewing .step-label {
  color: #fff;
}

.progress-step:hover:not(.pending) .step-circle {
  transform: scale(1.1);
}

.step-line {
  width: 24px;
  height: 2px;
  background: #4B5563;
  margin: 0 4px;
}

.step-line.completed {
  background: #1A936F;
}

.brand {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 800;
  font-size: 18px;
  letter-spacing: 1px;
  cursor: pointer;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #666;
  font-weight: 500;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.workflow-step {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

.step-num {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 700;
  color: #999;
}

.step-name {
  font-weight: 700;
  color: #000;
}

.step-divider {
  width: 1px;
  height: 14px;
  background-color: #E0E0E0;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #CCC;
}

.status-indicator.processing .dot { background: #FF5722; animation: pulse 1s infinite; }
.status-indicator.completed .dot { background: #4CAF50; }
.status-indicator.error .dot { background: #F44336; }

@keyframes pulse { 50% { opacity: 0.5; } }

/* Content */
.content-area {
  flex: 1;
  display: flex;
  position: relative;
  overflow: hidden;
}

.panel-wrapper {
  height: 100%;
  overflow: hidden;
  transition: width 0.4s cubic-bezier(0.25, 0.8, 0.25, 1), opacity 0.3s ease, transform 0.3s ease;
  will-change: width, opacity, transform;
}

.panel-wrapper.left {
  border-right: 1px solid #EAEAEA;
}
</style>
