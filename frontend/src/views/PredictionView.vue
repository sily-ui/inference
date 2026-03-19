<template>
  <div class="main-view">
    <header class="app-header">
      <div class="header-left">
        <div class="brand" @click="router.push('/')">MIROFISH</div>
      </div>
      
      <div class="header-center">
        <StepProgressBar 
          :steps="['本体生成', '图谱构建', '模拟', '报告', '舆情预测']" 
          :currentStep="4"
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
          :currentPhase="5"
          :isSimulating="false"
          @refresh="refreshGraph"
          @toggle-maximize="toggleMaximize('graph')"
        />
      </div>

      <div class="panel-wrapper right" :style="rightPanelStyle">
        <Step5Prediction
          :reportId="currentReportId"
          :simulationId="simulationId"
          :simulationConfig="simulationConfig"
          :projectData="projectData"
          @add-log="addLog"
        />
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import GraphPanel from '../components/GraphPanel.vue'
import StepProgressBar from '../components/StepProgressBar.vue'
import Step5Prediction from '../components/Step5Prediction.vue'
import { getProject, getGraphData } from '../api/graph'
import { getSimulation, getSimulationConfig } from '../api/simulation'
import { getReport } from '../api/report'

const route = useRoute()
const router = useRouter()

// Layout State - 默认切换到工作台视角
const viewMode = ref('workbench')

// Data State
const currentReportId = ref(route.params.reportId)
const simulationId = ref(null)
const projectData = ref(null)
const simulationConfig = ref(null)
const graphData = ref(null)
const graphLoading = ref(false)
const systemLogs = ref([])
const currentStatus = ref('ready') // ready | processing | completed | error

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
  return currentStatus.value
})

const statusText = computed(() => {
  if (currentStatus.value === 'error') return 'Error'
  if (currentStatus.value === 'completed') return 'Completed'
  if (currentStatus.value === 'processing') return 'Processing'
  return 'Ready'
})

// --- Helpers ---
const addLog = (msg) => {
  const time = new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }) + '.' + new Date().getMilliseconds().toString().padStart(3, '0')
  systemLogs.value.push({ time, msg })
  if (systemLogs.value.length > 200) {
    systemLogs.value.shift()
  }
}

// 处理进度条点击 - 跳转到对应视图
const handleProgressBarClick = (stepIdx) => {
  const targetStep = stepIdx + 1
  
  if (targetStep === 1 || targetStep === 2) {
    if (projectData.value?.project_id) {
      router.push({ name: 'Process', params: { projectId: projectData.value.project_id } })
    } else {
      router.push('/')
    }
  } else if (targetStep === 3) {
    if (simulationId.value) {
      router.push({ name: 'Simulation', params: { simulationId: simulationId.value } })
    }
  } else if (targetStep === 4 && currentReportId.value) {
    router.push({ name: 'Report', params: { reportId: currentReportId.value } })
  } else if (targetStep === 5) {
    // 已经在舆情预测页面
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

const refreshGraph = () => {
  if (projectData.value?.graph_id) {
    loadGraph(projectData.value.graph_id)
  }
}

// --- Data Logic ---
const loadReportData = async () => {
  try {
    addLog(`加载报告数据: ${currentReportId.value}`)
    
    // 获取 report 信息以获取 simulation_id
    const reportRes = await getReport(currentReportId.value)
    if (reportRes.success && reportRes.data) {
      const reportData = reportRes.data
      simulationId.value = reportData.simulation_id
      
      if (simulationId.value) {
        // 获取 simulation 信息
        const simRes = await getSimulation(simulationId.value)
        if (simRes.success && simRes.data) {
          const simData = simRes.data
          
          // 获取 simulation 配置
          try {
            const configRes = await getSimulationConfig(simulationId.value)
            if (configRes.success && configRes.data) {
              simulationConfig.value = configRes.data
              addLog('模拟配置加载成功')
            }
          } catch (e) {
            addLog(`获取模拟配置失败: ${e.message}`)
          }
          
          // 获取 project 信息
          if (simData.project_id) {
            const projRes = await getProject(simData.project_id)
            if (projRes.success && projRes.data) {
              projectData.value = projRes.data
              addLog(`项目加载成功: ${projRes.data.project_id}`)
              
              // 获取 graph 数据
              if (projRes.data.graph_id) {
                await loadGraph(projRes.data.graph_id)
              }
            }
          }
        }
      }
    } else {
      addLog(`获取报告信息失败: ${reportRes.error || '未知错误'}`)
    }
  } catch (err) {
    addLog(`加载异常: ${err.message}`)
  }
}

const loadGraph = async (graphId) => {
  graphLoading.value = true
  
  try {
    const res = await getGraphData(graphId)
    if (res.success) {
      graphData.value = res.data
      addLog('图谱数据加载成功')
    }
  } catch (err) {
    addLog(`图谱加载失败: ${err.message}`)
  } finally {
    graphLoading.value = false
  }
}

// Watch route params
watch(() => route.params.reportId, (newId) => {
  if (newId && newId !== currentReportId.value) {
    currentReportId.value = newId
    loadReportData()
  }
}, { immediate: true })

onMounted(() => {
  addLog('舆情预测页面初始化')
  loadReportData()
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

.brand {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 800;
  font-size: 18px;
  letter-spacing: 1px;
  cursor: pointer;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 500;
  padding: 6px 12px;
  border-radius: 20px;
  background: #f3f4f6;
  color: #6b7280;
}

.status-indicator.ready {
  background: #f0fdf4;
  color: #166534;
}

.status-indicator.processing {
  background: #fef3c7;
  color: #92400e;
}

.status-indicator.completed {
  background: #dbeafe;
  color: #1e40af;
}

.status-indicator.error {
  background: #fee2e2;
  color: #991b1b;
}

.status-indicator .dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: currentColor;
}

/* Content Area */
.content-area {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.panel-wrapper {
  transition: all 0.3s ease;
  overflow: hidden;
}

.panel-wrapper.left {
  border-right: 1px solid #EAEAEA;
}

.panel-wrapper.right {
  flex: 1;
  overflow: hidden;
}
</style>
