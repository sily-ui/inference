/**
 * 临时存储待上传的文件和需求
 * 用于首页点击启动引擎后立即跳转，在Process页面再进行API调用
 */
import { reactive } from 'vue'

const state = reactive({
  files: [],
  simulationRequirement: '',
  isPending: false,
  dataSource: 'file',
  tavilyData: null
})

export function setPendingUpload(files, requirement, dataSource = 'file', tavilyData = null) {
  state.files = files
  state.simulationRequirement = requirement
  state.isPending = true
  state.dataSource = dataSource
  state.tavilyData = tavilyData
}

export function getPendingUpload() {
  return {
    files: state.files,
    simulationRequirement: state.simulationRequirement,
    isPending: state.isPending,
    dataSource: state.dataSource,
    tavilyData: state.tavilyData
  }
}

export function clearPendingUpload() {
  state.files = []
  state.simulationRequirement = ''
  state.isPending = false
  state.dataSource = 'file'
  state.tavilyData = null
}

export default state
