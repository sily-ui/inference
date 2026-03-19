import service from './index.js'

/**
 * 舆情预测相关API
 */

/**
 * 获取完整舆情预测
 * @param {Object} data - 预测参数
 * @param {string} data.simulation_id - 模拟ID
 * @param {string} data.report_id - 报告ID（可选）
 * @param {string} data.event_summary - 事件摘要
 * @param {string} data.current_sentiment - 当前情绪
 * @param {number} data.time_range - 预测天数（默认7天）
 * @returns {Promise<Object>} 预测结果
 */
export function predictPublicOpinion(data) {
  return service({
    url: '/api/prediction/predict',
    method: 'post',
    data
  })
}

/**
 * 模拟干预策略效果
 * @param {Object} data - 干预参数
 * @param {string} data.event_summary - 事件摘要
 * @param {string} data.intervention - 干预措施描述
 * @param {string} data.current_sentiment - 当前情绪
 * @returns {Promise<Object>} 干预效果预测
 */
export function simulateIntervention(data) {
  return service({
    url: '/api/prediction/intervention',
    method: 'post',
    data
  })
}

/**
 * AI对话 - 基于预测结果问答
 * @param {Object} data - 对话参数
 * @param {string} data.question - 用户问题
 * @param {Object} data.prediction_data - 预测数据
 * @returns {Promise<Object>} 回答内容
 */
export function chatAboutPrediction(data) {
  return service({
    url: '/api/prediction/chat',
    method: 'post',
    data
  })
}

/**
 * 获取演示预测数据（用于测试）
 * @returns {Promise<Object>} 演示数据
 */
export function getDemoPrediction() {
  return service({
    url: '/api/prediction/demo',
    method: 'get'
  })
}

/**
 * 生成推荐问题
 * @param {Object} data - 生成参数
 * @param {string} data.event_summary - 事件摘要
 * @param {Array} data.scenarios - 预测情景列表
 * @param {Object} data.sentiment_distribution - 情绪分布
 * @returns {Promise<Object>} 推荐问题列表
 */
export function generateRecommendedQuestions(data) {
  return service({
    url: '/api/prediction/recommend-questions',
    method: 'post',
    data
  })
}

/**
 * Agent模式舆情预测 - ReACT架构
 * @param {Object} data - 预测参数
 * @param {string} data.simulation_id - 模拟ID
 * @param {string} data.event_summary - 事件摘要
 * @param {string} data.current_sentiment - 当前情绪
 * @param {number} data.time_range - 预测天数
 * @param {Object} data.simulation_data - 模拟运行数据
 * @returns {Promise<Object>} 预测结果
 */
export function agentPredict(data) {
  return service({
    url: '/api/prediction/agent/predict',
    method: 'post',
    data
  })
}

/**
 * Agent模式舆情预测 - 流式返回（SSE）
 * @param {Object} data - 预测参数
 * @param {Function} onLog - 日志回调
 * @param {Function} onProgress - 进度回调
 * @param {Function} onResult - 结果回调
 * @param {Function} onError - 错误回调
 * @returns {EventSource} EventSource实例
 */
export function agentPredictStream(data, { onLog, onProgress, onResult, onError }) {
  const eventSource = new EventSource('/api/prediction/agent/stream', {
    headers: {
      'Content-Type': 'application/json'
    }
  })

  eventSource.addEventListener('log', (event) => {
    try {
      const logEntry = JSON.parse(event.data)
      if (onLog) onLog(logEntry)
    } catch (e) {
      console.error('Parse log error:', e)
    }
  })

  eventSource.addEventListener('progress', (event) => {
    try {
      const progressData = JSON.parse(event.data)
      if (onProgress) onProgress(progressData)
    } catch (e) {
      console.error('Parse progress error:', e)
    }
  })

  eventSource.addEventListener('result', (event) => {
    try {
      const resultData = JSON.parse(event.data)
      if (onResult) onResult(resultData)
      eventSource.close()
    } catch (e) {
      console.error('Parse result error:', e)
    }
  })

  eventSource.addEventListener('error', (event) => {
    try {
      const errorData = JSON.parse(event.data)
      if (onError) onError(errorData)
    } catch (e) {
      if (onError) onError({ error: 'Unknown error' })
    }
    eventSource.close()
  })

  eventSource.onerror = () => {
    if (onError) onError({ error: 'Connection error' })
    eventSource.close()
  }

  return eventSource
}

/**
 * 获取Agent预测日志
 * @param {string} predictionId - 预测ID
 * @returns {Promise<Object>} 日志列表
 */
export function getAgentLogs(predictionId) {
  return service({
    url: `/api/prediction/agent/logs/${predictionId}`,
    method: 'get'
  })
}
