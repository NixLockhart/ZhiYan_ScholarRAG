<script setup>
import { ref, onMounted } from 'vue'
import { getSettings, updateSettings } from '@/api'
import { ElMessage } from 'element-plus'

const config = ref({
  use_multi_query: true,
  multi_query_count: 3,
  retrieve_k: 10,
  rerank_top_k: 5,
  use_rerank: true,
  use_compression: false,
})

const loading = ref(false)
const saving = ref(false)

const defaultConfig = {
  use_multi_query: true,
  multi_query_count: 3,
  retrieve_k: 10,
  rerank_top_k: 5,
  use_rerank: true,
  use_compression: false,
}

async function loadSettings() {
  loading.value = true
  try {
    const data = await getSettings()
    config.value = { ...defaultConfig, ...data }
  } catch {
    // 使用默认配置
  } finally {
    loading.value = false
  }
}

async function saveSettings() {
  saving.value = true
  try {
    await updateSettings(config.value)
    ElMessage.success('配置已保存')
  } catch {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

function resetSettings() {
  config.value = { ...defaultConfig }
  ElMessage.info('已恢复默认配置（需点击保存生效）')
}

onMounted(() => {
  loadSettings()
})
</script>

<template>
  <div v-loading="loading" style="max-width: 600px;">
    <el-form label-width="140px" label-position="left">
      <h3 style="margin-bottom: 20px; color: #303133;">RAG 检索增强配置</h3>

      <el-alert
        type="info"
        :closable="false"
        style="margin-bottom: 20px;"
      >
        <p>以下配置会影响问答时的检索策略和结果质量。</p>
        <p>开启更多功能可以提高回答准确率，但会增加响应时间。</p>
      </el-alert>

      <el-divider content-position="left">检索策略</el-divider>

      <el-form-item label="多查询检索">
        <el-switch v-model="config.use_multi_query" />
        <span style="margin-left: 12px; font-size: 12px; color: #909399;">
          自动将问题改写为多个不同角度的查询，提高文档召回率
        </span>
      </el-form-item>

      <el-form-item v-if="config.use_multi_query" label="查询扩展数量">
        <el-slider
          v-model="config.multi_query_count"
          :min="2"
          :max="5"
          :step="1"
          show-stops
          style="width: 300px;"
        />
      </el-form-item>

      <el-form-item label="检索文档数量">
        <el-slider
          v-model="config.retrieve_k"
          :min="3"
          :max="20"
          :step="1"
          show-input
          style="width: 300px;"
        />
      </el-form-item>

      <el-divider content-position="left">结果优化</el-divider>

      <el-form-item label="重排序优化">
        <el-switch v-model="config.use_rerank" />
        <span style="margin-left: 12px; font-size: 12px; color: #909399;">
          将最相关的内容放在上下文首尾，缓解"中间丢失"问题
        </span>
      </el-form-item>

      <el-form-item v-if="config.use_rerank" label="重排序保留数量">
        <el-slider
          v-model="config.rerank_top_k"
          :min="3"
          :max="10"
          :step="1"
          show-input
          style="width: 300px;"
        />
      </el-form-item>

      <el-form-item label="上下文压缩">
        <el-switch v-model="config.use_compression" />
        <span style="margin-left: 12px; font-size: 12px; color: #909399;">
          用LLM过滤无关段落，只保留与问题相关的语句（较慢）
        </span>
      </el-form-item>

      <el-divider />

      <el-form-item>
        <el-button type="primary" :loading="saving" @click="saveSettings">保存配置</el-button>
        <el-button @click="resetSettings">恢复默认</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>
