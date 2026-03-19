import service from './index'

/**
 * Tavily 搜索服务 API
 * 
 * 功能：
 * - 搜索事件信息
 * - 提取文本用于推理
 */

/**
 * 使用 Tavily 搜索完整事件信息
 * @param {Object} data - 搜索参数
 * @param {string} data.query - 搜索查询
 * @param {string} data.search_depth - 搜索深度 (basic | advanced)
 * @param {string} data.topic - 主题类型 (general | news | finance)
 * @param {number} data.max_results - 最大结果数
 * @returns {Promise}
 */
export function searchWithTavily(data) {
  return service({
    url: '/api/social/search',
    method: 'post',
    data
  })
}

/**
 * 提取文本用于推理
 * @param {Object} data - 提取参数
 * @param {string} data.query - 搜索查询
 * @param {boolean} data.include_raw_content - 是否包含原始内容
 * @returns {Promise}
 */
export function extractForInference(data) {
  return service({
    url: '/api/social/extract',
    method: 'post',
    data
  })
}
