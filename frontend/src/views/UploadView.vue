<script setup>
import { ref } from 'vue'
import { UploadFilled } from '@element-plus/icons-vue'
import { uploadDocument } from '@/api'
import { ElMessage } from 'element-plus'

const fileList = ref([])
const uploadingFiles = ref([])

async function handleUpload(options) {
  const file = options.file
  const entry = {
    name: file.name,
    size: (file.size / 1024 / 1024).toFixed(2) + ' MB',
    status: 'uploading',
    progress: 0,
    doc_id: null,
  }
  uploadingFiles.value.unshift(entry)

  try {
    const data = await uploadDocument(file, (e) => {
      if (e.total > 0) {
        entry.progress = Math.round((e.loaded / e.total) * 100)
      }
    })
    entry.status = 'success'
    entry.doc_id = data.doc_id
    ElMessage.success(`"${file.name}" 上传并处理成功`)
  } catch {
    entry.status = 'error'
    entry.progress = 0
  }
}

function statusType(status) {
  const map = { uploading: 'warning', success: 'success', error: 'danger' }
  return map[status] || 'info'
}

function statusText(status) {
  const map = { uploading: '处理中...', success: '已完成', error: '失败' }
  return map[status] || status
}
</script>

<template>
  <div>
    <!-- 上传区域 -->
    <el-upload
      drag
      :auto-upload="true"
      :show-file-list="false"
      :http-request="handleUpload"
      accept=".pdf,.docx"
      multiple
    >
      <el-icon :size="60" color="#c0c4cc"><UploadFilled /></el-icon>
      <div style="margin-top: 12px; color: #606266;">
        将 PDF / DOCX 文件拖到此处，或 <em style="color: #409eff;">点击上传</em>
      </div>
      <template #tip>
        <div style="color: #909399; font-size: 12px; margin-top: 8px;">
          支持 .pdf 和 .docx 格式，单文件不超过 50MB
        </div>
      </template>
    </el-upload>

    <!-- 上传记录列表 -->
    <el-table
      v-if="uploadingFiles.length > 0"
      :data="uploadingFiles"
      style="margin-top: 24px;"
    >
      <el-table-column prop="name" label="文件名" />
      <el-table-column prop="size" label="大小" width="120" />
      <el-table-column label="状态" width="160">
        <template #default="{ row }">
          <el-progress
            v-if="row.status === 'uploading'"
            :percentage="row.progress"
            :stroke-width="6"
            style="width: 120px;"
          />
          <el-tag v-else :type="statusType(row.status)" size="small">
            {{ statusText(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>
