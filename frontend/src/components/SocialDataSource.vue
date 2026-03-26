<template>
  <div class="tavily-source-container">
    <!-- Tavily 在线搜索模式 -->
    <div class="tavily-mode">
      <div class="search-intro">
        <div class="intro-content">
          <div class="intro-icon">🔍</div>
          <div class="intro-title">输入简短描述，完整还原事件</div>
          <div class="intro-desc">输入你了解的部分信息，Tavily 会帮你搜索并整合完整的新闻事件</div>
        </div>
      </div>

      <!-- 搜索输入 -->
      <div class="search-section">
        <div class="search-input-wrapper">
          <textarea
            v-model="searchQuery"
            class="search-input"
            placeholder="例如：小米汽车 SU7 发布会发生了什么？/ 特斯拉最新降价事件 / 某明星官宣恋情"
            rows="3"
            @keydown.ctrl.enter="startSearch"
          ></textarea>
          <div class="search-hint">输入简短描述，按 Ctrl+Enter 搜索</div>
        </div>

        <div class="search-options">
          <div class="option-group">
            <label class="option-label">搜索深度</label>
            <select v-model="searchDepth" class="option-select">
              <option value="basic">基础搜索</option>
              <option value="advanced">深度搜索</option>
            </select>
          </div>
          <div class="option-group">
            <label class="option-label">主题类型</label>
            <select v-model="topic" class="option-select">
              <option value="general">综合</option>
              <option value="news">新闻</option>
              <option value="finance">财经</option>
            </select>
          </div>
          <div class="option-group">
            <label class="option-label">结果数量</label>
            <select v-model="maxResults" class="option-select">
              <option :value="5">5 条</option>
              <option :value="10">10 条</option>
              <option :value="15">15 条</option>
            </select>
          </div>
        </div>

        <button class="search-btn" @click="startSearch" :disabled="searching || !searchQuery">
          {{ searching ? '搜索中...' : '🔍 开始搜索' }}
        </button>
        <div class="tavily-notice">
          <span class="notice-icon">ℹ️</span>
          <span class="notice-text">Tavily 官方只支持 3 种主题：general / news / finance</span>
        </div>
      </div>

      <!-- 搜索结果 -->
      <div v-if="searchResults" class="results-section">
        <!-- 摘要 -->
        <div v-if="searchResults.answer" class="answer-card">
          <div class="answer-header">
            <span class="answer-icon">📋</span>
            <span class="answer-title">事件摘要</span>
            <span v-if="searching" class="streaming-indicator">
              <span class="stream-dot"></span>
              <span class="stream-dot"></span>
              <span class="stream-dot"></span>
            </span>
          </div>
          <div class="answer-content">{{ searchResults.answer }}</div>
        </div>

        <!-- 详细内容 -->
        <div v-if="searchResults.results?.length" class="results-list-section">
          <div class="results-list-header">
            <span class="results-count">共 {{ searchResults.results.length }} 条搜索结果</span>
          </div>
          <div class="results-list">
            <div v-for="(result, index) in searchResults.results" :key="index" class="result-item">
              <div class="result-index">{{ index + 1 }}</div>
              <div class="result-content">
                <div class="result-title-row">
                  <a :href="result.url" target="_blank" class="result-title">{{ result.title }}</a>
                  <span class="result-score">{{ (result.score * 100).toFixed(0) }}% 相关度</span>
                </div>
                <div class="result-meta">
                  <span v-if="result.published_date" class="result-date">{{ result.published_date }}</span>
                </div>
                <p class="result-text">{{ result.content }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- 模拟提示词（通用） -->
        <div class="console-divider">
          <span>输入参数</span>
        </div>

        <div class="input-section">
          <div class="input-header">
            <span class="input-label">>_ 模拟提示词</span>
          </div>
          <div class="input-wrapper">
            <textarea
              v-model="formData.simulationRequirement"
              class="code-input"
              placeholder="// 用自然语言输入模拟或预测需求"
              rows="4"
            ></textarea>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="action-buttons">
          <button class="extract-btn" @click="startSimulation" :disabled="!canSubmit || extracting">
            {{ extracting ? '启动中...' : '🚀 提取并启动引擎' }}
          </button>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-else-if="searched && !searching" class="empty-results">
        <div class="empty-icon">🔍</div>
        <div class="empty-text">未找到相关信息</div>
        <div class="empty-hint">请尝试其他描述词</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const API_BASE = import.meta.env.VITE_API_BASE || '/api'

const dataSource = ref('tavily')

const searchQuery = ref('')
const searchDepth = ref('basic')
const topic = ref('general')
const maxResults = ref(10)
const searching = ref(false)
const searched = ref(false)
const searchResults = ref(null)
const streamedAnswer = ref('')  // 流式输出的中文摘要
const extracting = ref(false)

const formData = ref({
  simulationRequirement: ''
})

const canSubmit = computed(() => {
  return searchResults.value && formData.value.simulationRequirement.trim()
})

// 处理搜索结果内容：清理markdown符号、限制长度、去除乱码
const formatContent = (content) => {
  if (!content) return ''
  
  let cleaned = content
  
  // 检测并移除 SVG URL 编码乱码 (如: user203e3cdefs3e3cstyle3e20.st0)
  if (/user[0-9a-f]{4,}|style[0-9a-f]{2,}|3c[a-z0-9]+3e/i.test(cleaned)) {
    cleaned = '[内容格式异常]'
  } else {
    // 移除markdown标题符号 (# ## ###)
    cleaned = cleaned.replace(/^#{1,6}\s*/gm, '')
    
    // 移除markdown加粗/斜体符号 (** * __ _)
    cleaned = cleaned.replace(/\*\*/g, '')
    cleaned = cleaned.replace(/\*/g, '')
    cleaned = cleaned.replace(/__/g, '')
    cleaned = cleaned.replace(/_/g, '')
    
    // 移除markdown链接 [text](url) 保留文本
    cleaned = cleaned.replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
    
    // 移除markdown图片 ![alt](url)
    cleaned = cleaned.replace(/!\[([^\]]*)\]\([^)]+\)/g, '')
    
    // 移除markdown代码块标记
    cleaned = cleaned.replace(/```[\s\S]*?```/g, '')
    cleaned = cleaned.replace(/`([^`]+)`/g, '$1')
    
    // 移除markdown列表符号
    cleaned = cleaned.replace(/^[-*+]\s*/gm, '')
    cleaned = cleaned.replace(/^\d+\.\s*/gm, '')
    
    // 移除HTML标签
    cleaned = cleaned.replace(/<[^>]+>/g, '')
    
    // 移除URL链接
    cleaned = cleaned.replace(/https?:\/\/[^\s]+/g, '')
    
    // 移除转义字符和特殊符号
    cleaned = cleaned.replace(/\\([\\`*_{}\[\]()#+\-.!])/g, '$1')
    cleaned = cleaned.replace(/&nbsp;/g, ' ')
    cleaned = cleaned.replace(/&amp;/g, '&')
    cleaned = cleaned.replace(/&lt;/g, '<')
    cleaned = cleaned.replace(/&gt;/g, '>')
    cleaned = cleaned.replace(/&quot;/g, '"')
    
    // 移除连续的特殊字符
    cleaned = cleaned.replace(/[#\*\-_]{2,}/g, '')
    
    // 移除乱码字符（移除非中文、非英文、非常见标点、非数字的字符）
    cleaned = cleaned.replace(/[^\u4e00-\u9fa5a-zA-Z0-9\s，。！？、；：""''（）【】《》·—…「」『』【】.,!?;:'"()\[\]\-]/g, '')
    
    // 移除多余空格和换行
    cleaned = cleaned.replace(/\n+/g, ' ')
    cleaned = cleaned.replace(/\s+/g, ' ')
  }
  
  // 去除首尾空格
  cleaned = cleaned.trim()
  
  // 如果清理后为空或太短，返回提示
  if (!cleaned || cleaned.length < 5) {
    return '[内容格式异常]'
  }
  
  // 清理句子开头的标点
  cleaned = cleaned.replace(/^[，。！？、；：""''（）【】《》]+/, '')
  
  // 限制200字
  if (cleaned.length > 200) {
    cleaned = cleaned.substring(0, 200) + '...'
  }
  
  return cleaned
}

const startSearch = async () => {
  if (!searchQuery.value || searching.value) return
  
  searching.value = true
  searched.value = true
  searchResults.value = null
  
  try {
    const response = await fetch(`${API_BASE}/social/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: searchQuery.value,
        search_depth: searchDepth.value,
        topic: topic.value,
        max_results: maxResults.value
      })
    })
    
    const result = await response.json()
    
    if (result.success) {
      // 处理搜索结果内容
      if (result.data && result.data.results) {
        result.data.results = result.data.results.map(item => ({
          ...item,
          content: formatContent(item.content)
        }))
      }
      searchResults.value = result.data
    } else {
      alert('搜索失败: ' + result.error)
    }
  } catch (error) {
    console.error('搜索失败:', error)
    alert('搜索失败，请检查网络连接')
  } finally {
    searching.value = false
  }
}

// 流式搜索
const startSearchStream = async () => {
  if (!searchQuery.value || searching.value) return
  
  searching.value = true
  searched.value = true
  searchResults.value = null
  streamedAnswer.value = ''
  
  try {
    const response = await fetch(`${API_BASE}/social/search/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: searchQuery.value,
        search_depth: searchDepth.value,
        topic: topic.value,
        max_results: maxResults.value
      })
    })
    
    if (!response.ok) {
      throw new Error('搜索失败')
    }
    
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      
      const chunk = decoder.decode(value)
      const lines = chunk.split('\n')
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))
            
            if (data.type === 'results') {
              // 处理搜索结果
              if (data.data.results) {
                data.data.results = data.data.results.map(item => ({
                  ...item,
                  content: formatContent(item.content)
                }))
              }
              searchResults.value = data.data
            } else if (data.type === 'chunk') {
              // 流式输出中文摘要
              streamedAnswer.value += data.content
              searchResults.value = {
                ...searchResults.value,
                answer: streamedAnswer.value
              }
            } else if (data.type === 'done') {
              console.log('[DEBUG] 流式输出完成:', data.summary)
            } else if (data.type === 'error') {
              console.error('[ERROR] 流式输出错误:', data.error)
            }
          } catch (e) {
            console.warn('[WARN] 解析SSE数据失败:', e)
          }
        }
      }
    }
  } catch (error) {
    console.error('流式搜索失败:', error)
    alert('搜索失败，请检查网络连接')
  } finally {
    searching.value = false
  }
}

const startSimulation = async () => {
  console.log('[DEBUG] startSimulation called')
  console.log('[DEBUG] canSubmit:', canSubmit.value)
  console.log('[DEBUG] searchResults:', searchResults.value ? 'exists' : 'null')
  console.log('[DEBUG] simulationRequirement:', formData.value.simulationRequirement)
  
  if (!canSubmit.value) {
    console.error('[ERROR] canSubmit is false, cannot submit!')
    alert('请先完成搜索并输入模拟需求')
    return
  }
  
  const { setPendingUpload } = await import('../store/pendingUpload.js')
  
  console.log('[DEBUG] 开始生成数据...')
   
  // 直接使用搜索结果数据，避免再次调用耗时的extract API
  // 将搜索结果转换为Process页面需要的格式
  const tavilyData = {
    query: searchQuery.value,
    extracted_text: generateExtractedText(),
    summary: searchResults.value?.answer || '',
    key_points: searchResults.value?.results?.map(r => ({
      title: r.title,
      content: r.content?.substring(0, 200) || '',
      url: r.url
    })) || [],
    sources: searchResults.value?.results?.map(r => ({
      title: r.title,
      url: r.url
    })) || []
  }
  
  console.log('[DEBUG] tavilyData generated, extracted_text length:', tavilyData.extracted_text.length)
   
  setPendingUpload([], formData.value.simulationRequirement, 'social', tavilyData)
   
  console.log('[DEBUG] 准备跳转到 Process 页面...')
   
  router.push({
    name: 'Process',
    params: { projectId: 'new' }
  })
}

// 生成提取文本（用于Process页面处理）
const generateExtractedText = () => {
  if (!searchResults.value) return ''
  
  const parts = []
  const searchTime = new Date().toLocaleString('zh-CN')
  
  // 标题部分
  parts.push(`# 事件调查报告：${searchQuery.value}`)
  parts.push(`\n检索时间：${searchTime}`)
  parts.push(`\n## 事件摘要\n${searchResults.value.answer || '暂无摘要'}`)
  
  // 搜索统计信息
  const totalResults = searchResults.value.results?.length || 0
  const topSources = searchResults.value.visualization?.top_sources || []
  parts.push(`\n## 数据来源统计`)
  parts.push(`- 共获取 ${totalResults} 条相关信息`)
  if (topSources.length > 0) {
    parts.push(`- 主要信息来源：${topSources.map(s => s.domain).join('、')}`)
  }
  
  // 详细信息（完整内容）
  parts.push(`\n## 详细内容\n`)
  searchResults.value.results?.forEach((r, i) => {
    parts.push(`### ${i + 1}. ${r.title}`)
    parts.push(`**来源链接**：${r.url}`)
    if (r.published_date) {
      parts.push(`**发布时间**：${r.published_date}`)
    }
    parts.push(`**相关度**：${(r.score * 100).toFixed(0)}%`)
    parts.push(`\n${r.content || '暂无内容'}`)
    parts.push('\n---\n')
  })
  
  return parts.join('\n')
}
</script>

<style scoped>
.tavily-source-container {
  padding: 20px;
}

.search-intro {
  text-align: center;
  padding: 30px 20px;
  background: #f8f9fa;
  border-radius: 12px;
  margin-bottom: 20px;
}

.intro-icon {
  font-size: 48px;
  margin-bottom: 15px;
}

.intro-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 8px;
}

.intro-desc {
  font-size: 13px;
  color: #666;
}

.search-section {
  margin-bottom: 25px;
}

.search-input-wrapper {
  margin-bottom: 15px;
}

.search-input {
  width: 100%;
  padding: 14px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  resize: vertical;
  outline: none;
}

.search-input:focus {
  border-color: #000;
}

.search-hint {
  font-size: 12px;
  color: #999;
  margin-top: 8px;
}

.search-options {
  display: flex;
  gap: 15px;
  margin-bottom: 15px;
  flex-wrap: wrap;
}

.option-group {
  flex: 1;
  min-width: 120px;
}

.option-label {
  display: block;
  font-size: 12px;
  color: #666;
  margin-bottom: 6px;
}

.option-select {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 13px;
  background: #fff;
}

.search-btn {
  width: 100%;
  padding: 14px;
  background: #000;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
}

.search-btn:disabled {
  background: #999;
  cursor: not-allowed;
}

.tavily-notice {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  margin-top: 12px;
  padding: 10px 16px;
  background: #f0f7ff;
  border: 1px solid #d0e3ff;
  border-radius: 8px;
  font-size: 12px;
  color: #4a6fa5;
}

.notice-icon {
  font-size: 14px;
}

.notice-text {
  font-size: 12px;
}

.results-section {
  margin-top: 20px;
}

.answer-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 10px 40px rgba(102, 126, 234, 0.3);
  position: relative;
  overflow: hidden;
}

.answer-card::before {
  content: '';
  position: absolute;
  top: -50%;
  right: -50%;
  width: 100%;
  height: 100%;
  background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
  pointer-events: none;
}

.answer-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.answer-icon {
  font-size: 20px;
}

.answer-title {
  font-weight: 600;
  font-size: 15px;
}

.streaming-indicator {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-left: auto;
}

.stream-dot {
  width: 6px;
  height: 6px;
  background: #fff;
  border-radius: 50%;
  animation: streamPulse 1.4s infinite ease-in-out;
}

.stream-dot:nth-child(1) { animation-delay: 0s; }
.stream-dot:nth-child(2) { animation-delay: 0.2s; }
.stream-dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes streamPulse {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.5; }
  40% { transform: scale(1); opacity: 1; }
}

.answer-content {
  font-size: 14px;
  line-height: 1.7;
}

.action-buttons {
  margin-top: 20px;
}

.extract-btn {
  width: 100%;
  padding: 14px;
  background: #667eea;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
}

.extract-btn:disabled {
  background: #999;
  cursor: not-allowed;
}

.empty-results {
  text-align: center;
  padding: 40px;
  color: #999;
}

.empty-icon {
  font-size: 40px;
  margin-bottom: 10px;
}

.empty-text {
  font-size: 16px;
  margin-bottom: 5px;
}

.empty-hint {
  font-size: 13px;
}

.console-divider {
  display: flex;
  align-items: center;
  margin: 20px 0;
}

.console-divider::before,
.console-divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: #eee;
}

.console-divider span {
  padding: 0 15px;
  font-size: 12px;
  color: #bbb;
}

.input-section {
  margin-bottom: 20px;
}

.input-header {
  margin-bottom: 10px;
}

.input-label {
  font-family: monospace;
  font-size: 13px;
  color: #666;
}

.input-wrapper textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid #ddd;
  font-family: monospace;
  font-size: 13px;
  resize: vertical;
  outline: none;
}

.results-list-section {
  margin-bottom: 24px;
}

.results-list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e5e7eb;
}

.results-count {
  font-size: 13px;
  color: #6b7280;
  font-weight: 500;
}

.results-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.result-item {
  display: flex;
  gap: 16px;
  padding: 16px;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.result-item:hover {
  border-color: #667eea;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.1);
}

.result-index {
  flex-shrink: 0;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  font-size: 12px;
  font-weight: 600;
  border-radius: 6px;
}

.result-content {
  flex: 1;
  min-width: 0;
}

.result-title {
  display: block;
  font-size: 15px;
  font-weight: 600;
  color: #111827;
  text-decoration: none;
  margin-bottom: 8px;
  line-height: 1.4;
}

.result-title:hover {
  color: #667eea;
  text-decoration: underline;
}

.result-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 10px;
}

.result-date {
  font-size: 12px;
  color: #6b7280;
}

.result-title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.result-title-row .result-title {
  flex: 1;
}

.result-score {
  font-size: 11px;
  color: #10b981;
  background: #ecfdf5;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 500;
}

.result-text {
  font-size: 13px;
  color: #4b5563;
  line-height: 1.7;
  margin: 0;
}

</style>
