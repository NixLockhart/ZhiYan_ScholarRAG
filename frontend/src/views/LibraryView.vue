<script setup>
import { ref, onMounted } from 'vue'
import { Delete, Document, Refresh } from '@element-plus/icons-vue'
import { getDocuments, deleteDocument, getDocumentStats } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'

const documents = ref([])
const stats = ref({ doc_count: 0, total_chunks: 0, total_pages: 0 })
const loading = ref(false)

async function loadDocuments() {
  loading.value = true
  try {
    documents.value = await getDocuments()
  } catch {
    documents.value = []
  } finally {
    loading.value = false
  }
}

async function loadStats() {
  try {
    stats.value = await getDocumentStats()
  } catch {
    // 保持默认值
  }
}

async function handleDelete(doc) {
  try {
    await ElMessageBox.confirm(
      `确定删除文档 "${doc.filename}" 吗？删除后将无法恢复。`,
      '删除确认',
      { type: 'warning' }
    )
    await deleteDocument(doc.doc_id)
    ElMessage.success('删除成功')
    loadDocuments()
    loadStats()
  } catch {
    // 用户取消
  }
}

function formatTime(time) {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

function fileTypeTag(type) {
  return type === 'pdf' ? 'danger' : 'primary'
}

onMounted(() => {
  loadDocuments()
  loadStats()
})
</script>

<template>
  <div>
    <!-- 统计卡片 -->
    <el-row :gutter="20" style="margin-bottom: 24px;">
      <el-col :span="8">
        <el-statistic title="文档总数" :value="stats.doc_count" />
      </el-col>
      <el-col :span="8">
        <el-statistic title="总页数" :value="stats.total_pages" />
      </el-col>
      <el-col :span="8">
        <el-statistic title="文本块数" :value="stats.total_chunks" />
      </el-col>
    </el-row>

    <!-- 操作栏 -->
    <div style="display: flex; justify-content: flex-end; margin-bottom: 16px;">
      <el-button :icon="Refresh" @click="loadDocuments(); loadStats()">刷新</el-button>
    </div>

    <!-- 文档列表 -->
    <el-row :gutter="16" v-loading="loading">
      <el-col
        v-for="doc in documents"
        :key="doc.doc_id"
        :xs="24" :sm="12" :md="8" :lg="6"
        style="margin-bottom: 16px;"
      >
        <el-card shadow="hover" class="doc-card">
          <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
            <el-icon :size="24" color="#909399"><Document /></el-icon>
            <el-tag :type="fileTypeTag(doc.file_type)" size="small">
              {{ doc.file_type?.toUpperCase() }}
            </el-tag>
          </div>
          <h4 style="margin-bottom: 8px; word-break: break-all;">{{ doc.filename }}</h4>
          <p style="font-size: 12px; color: #909399;">
            {{ doc.page_count }} 页 · {{ doc.chunk_count }} 个文本块
          </p>
          <p style="font-size: 12px; color: #c0c4cc; margin-top: 4px;">
            {{ formatTime(doc.upload_time) }}
          </p>
          <div style="margin-top: 12px; text-align: right;">
            <el-button
              type="danger"
              :icon="Delete"
              size="small"
              text
              @click="handleDelete(doc)"
            >
              删除
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 空状态 -->
    <el-empty
      v-if="!loading && documents.length === 0"
      description="暂无文档，请先上传论文"
    />
  </div>
</template>
