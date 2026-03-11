<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { Promotion, Delete, RefreshRight } from '@element-plus/icons-vue'
import { sendChatStream, getChatHistory, clearChatHistory, getDocuments } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import MarkdownIt from 'markdown-it'

const md = new MarkdownIt()

const messages = ref([])
const inputText = ref('')
const loading = ref(false)
const messagesRef = ref(null)

// 流式请求的取消函数
let abortStream = null

// 文档选择
const documents = ref([])
const selectedDocIds = ref([])
const selectAll = ref(true)

async function loadDocuments() {
  try {
    documents.value = await getDocuments()
  } catch {
    documents.value = []
  }
}

function handleSelectAll(val) {
  selectedDocIds.value = val ? [] : []
  selectAll.value = val
}

function getDocIds() {
  if (selectAll.value || selectedDocIds.value.length === 0) return null
  return selectedDocIds.value
}

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || loading.value) return

  // 添加用户消息
  messages.value.push({ role: 'user', content: text })
  inputText.value = ''
  loading.value = true
  scrollToBottom()

  // 添加一个空的 AI 消息占位，后续逐字填充
  const aiMessage = {
    role: 'ai',
    content: '',
    sources: [],
    time_ms: null,
    streaming: true,
  }
  messages.value.push(aiMessage)
  const aiIndex = messages.value.length - 1

  abortStream = sendChatStream(text, getDocIds(), {
    onToken(token) {
      messages.value[aiIndex].content += token
      scrollToBottom()
    },
    onSources(sources) {
      messages.value[aiIndex].sources = sources
    },
    onDone(data) {
      messages.value[aiIndex].time_ms = data.query_time_ms
      messages.value[aiIndex].streaming = false
      loading.value = false
      abortStream = null
      scrollToBottom()
    },
    onError(errMsg) {
      if (!messages.value[aiIndex].content) {
        messages.value[aiIndex].content = '抱歉，请求处理失败，请稍后重试。'
      }
      messages.value[aiIndex].streaming = false
      loading.value = false
      abortStream = null
      ElMessage.error(errMsg)
    },
  })
}

function stopGenerate() {
  if (abortStream) {
    abortStream()
    abortStream = null
  }
  // 标记当前流式消息为结束
  const lastMsg = messages.value[messages.value.length - 1]
  if (lastMsg && lastMsg.streaming) {
    lastMsg.streaming = false
    lastMsg.content += '\n\n*（已手动停止生成）*'
  }
  loading.value = false
}

function renderMarkdown(text) {
  return md.render(text || '')
}

async function handleClear() {
  try {
    await ElMessageBox.confirm('确定清空所有对话记录吗？', '清空确认', { type: 'warning' })
    await clearChatHistory()
    messages.value = []
    ElMessage.success('已清空对话记录')
  } catch {
    // 用户取消
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
}

// 示例问题
const exampleQuestions = [
  '这篇论文的研究背景和动机是什么？',
  '论文提出了什么方法或模型？',
  '实验结果和主要结论是什么？',
  '论文的创新点和贡献有哪些？',
]

function askExample(q) {
  inputText.value = q
  sendMessage()
}

async function loadHistory() {
  try {
    const history = await getChatHistory()
    messages.value = history.map(msg => ({
      role: msg.role,
      content: msg.content,
      sources: msg.sources || [],
      time_ms: msg.query_time_ms || null,
      streaming: false,
    }))
    scrollToBottom()
  } catch {
    // 加载失败不影响使用
  }
}

onMounted(() => {
  loadDocuments()
  loadHistory()
})
</script>

<template>
  <div class="chat-container">
    <!-- 顶部操作栏 -->
    <div style="display: flex; justify-content: space-between; align-items: center; padding: 0 0 12px; border-bottom: 1px solid #ebeef5;">
      <div style="display: flex; align-items: center; gap: 12px;">
        <span style="font-size: 13px; color: #909399;">问答范围：</span>
        <el-checkbox v-model="selectAll" @change="handleSelectAll">全部文档</el-checkbox>
        <el-select
          v-if="!selectAll"
          v-model="selectedDocIds"
          multiple
          collapse-tags
          collapse-tags-tooltip
          placeholder="选择文档"
          style="width: 300px;"
        >
          <el-option
            v-for="doc in documents"
            :key="doc.doc_id"
            :label="doc.filename"
            :value="doc.doc_id"
          />
        </el-select>
      </div>
      <el-button :icon="Delete" text type="danger" @click="handleClear">清空对话</el-button>
    </div>

    <!-- 消息列表 -->
    <div class="chat-messages" ref="messagesRef">
      <!-- 空状态：示例问题 -->
      <div v-if="messages.length === 0" style="text-align: center; padding: 60px 0;">
        <p style="color: #909399; margin-bottom: 20px;">试试问我关于论文的问题：</p>
        <div style="display: flex; flex-wrap: wrap; gap: 10px; justify-content: center;">
          <el-tag
            v-for="q in exampleQuestions"
            :key="q"
            effect="plain"
            style="cursor: pointer; font-size: 13px;"
            @click="askExample(q)"
          >
            {{ q }}
          </el-tag>
        </div>
      </div>

      <!-- 消息列表 -->
      <div
        v-for="(msg, idx) in messages"
        :key="idx"
        :class="['message-item', msg.role]"
      >
        <div class="message-bubble">
          <span v-if="msg.role === 'user'">{{ msg.content }}</span>
          <div v-else>
            <div v-html="renderMarkdown(msg.content)"></div>
            <!-- 流式生成时的光标 -->
            <span v-if="msg.streaming" class="streaming-cursor">|</span>
          </div>

          <!-- 引用来源（流式结束后显示） -->
          <div v-if="!msg.streaming && msg.sources && msg.sources.length > 0" class="source-tags">
            <el-popover
              v-for="(src, i) in msg.sources"
              :key="i"
              placement="top"
              :width="400"
              trigger="click"
            >
              <template #reference>
                <el-tag size="small" effect="plain" style="cursor: pointer;">
                  📄 {{ src.filename }} - {{ src.page_label }}
                </el-tag>
              </template>
              <div style="font-size: 13px; line-height: 1.6; max-height: 200px; overflow-y: auto;">
                {{ src.content }}
              </div>
            </el-popover>
          </div>

          <!-- 耗时（流式结束后显示） -->
          <div v-if="!msg.streaming && msg.time_ms" style="font-size: 11px; color: #c0c4cc; margin-top: 6px;">
            响应耗时 {{ (msg.time_ms / 1000).toFixed(1) }}s
          </div>
        </div>
      </div>
    </div>

    <!-- 输入区域 -->
    <div class="chat-input-area">
      <el-input
        v-model="inputText"
        placeholder="请输入您的问题..."
        @keyup.enter="sendMessage"
        :disabled="loading"
        size="large"
      />
      <!-- 生成中显示停止按钮，否则显示发送按钮 -->
      <el-button
        v-if="loading"
        type="danger"
        size="large"
        @click="stopGenerate"
      >
        停止
      </el-button>
      <el-button
        v-else
        type="primary"
        :icon="Promotion"
        size="large"
        @click="sendMessage"
      >
        发送
      </el-button>
    </div>
  </div>
</template>

<style scoped>
/* 流式光标闪烁动画 */
.streaming-cursor {
  display: inline-block;
  animation: blink 0.8s step-end infinite;
  color: #409eff;
  font-weight: bold;
  margin-left: 2px;
}

@keyframes blink {
  50% { opacity: 0; }
}
</style>
