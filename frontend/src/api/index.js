import axios from 'axios'
import { ElMessage } from 'element-plus'

const request = axios.create({
  baseURL: '/api',
  timeout: 60000,
})

// 响应拦截器：统一处理后端响应格式
request.interceptors.response.use(
  (response) => {
    const res = response.data
    if (res.code === 200) {
      return res.data
    }
    ElMessage.error(res.message || '请求失败')
    return Promise.reject(new Error(res.message))
  },
  (error) => {
    if (error.code === 'ECONNABORTED') {
      ElMessage.error('请求超时，请稍后重试')
    } else if (!error.response) {
      ElMessage.error('网络异常，无法连接服务器')
    } else {
      const status = error.response.status
      const messages = {
        413: '文件过大，请上传小于50MB的文件',
        422: '文档解析失败，请检查文件格式',
        500: '服务器内部错误',
        504: '请求超时，请稍后重试',
      }
      ElMessage.error(messages[status] || `请求错误 (${status})`)
    }
    return Promise.reject(error)
  }
)

// ========== 文档管理 API ==========

/** 上传文档 */
export function uploadDocument(file, onProgress) {
  const formData = new FormData()
  formData.append('file', file)
  return request.post('/documents/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000,
    onUploadProgress: onProgress,
  })
}

/** 获取文档列表 */
export function getDocuments() {
  return request.get('/documents')
}

/** 获取文档详情 */
export function getDocument(docId) {
  return request.get(`/documents/${docId}`)
}

/** 删除文档 */
export function deleteDocument(docId) {
  return request.delete(`/documents/${docId}`)
}

/** 获取知识库统计 */
export function getDocumentStats() {
  return request.get('/documents/stats')
}

// ========== 智能对话 API ==========

/** 发送问题（流式 SSE） */
export function sendChatStream(question, docIds = null, { onToken, onSources, onDone, onError }) {
  const controller = new AbortController()

  fetch('/api/chat/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, doc_ids: docIds }),
    signal: controller.signal,
  })
    .then(async (response) => {
      if (!response.ok) {
        throw new Error(`请求失败 (${response.status})`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })

        // 解析 SSE 数据行
        const lines = buffer.split('\n')
        buffer = lines.pop() // 保留未完成的行

        for (const line of lines) {
          const trimmed = line.trim()
          if (!trimmed.startsWith('data: ')) continue

          try {
            const payload = JSON.parse(trimmed.slice(6))
            if (payload.type === 'token') {
              onToken?.(payload.data)
            } else if (payload.type === 'sources') {
              onSources?.(payload.data)
            } else if (payload.type === 'done') {
              onDone?.(payload.data)
            }
          } catch {
            // 忽略解析失败的行
          }
        }
      }
    })
    .catch((err) => {
      if (err.name !== 'AbortError') {
        onError?.(err.message || '流式请求失败')
      }
    })

  // 返回 abort 函数，允许前端取消请求
  return () => controller.abort()
}

/** 发送问题（完整响应，备用） */
export function sendChat(question, docIds = null) {
  return request.post('/chat', { question, doc_ids: docIds }, { timeout: 120000 })
}

/** 获取对话历史 */
export function getChatHistory() {
  return request.get('/chat/history')
}

/** 清空对话历史 */
export function clearChatHistory() {
  return request.delete('/chat/history')
}

// ========== 系统设置 API ==========

/** 获取RAG配置 */
export function getSettings() {
  return request.get('/settings')
}

/** 更新RAG配置 */
export function updateSettings(config) {
  return request.put('/settings', config)
}

export default request
