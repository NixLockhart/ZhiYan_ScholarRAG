<script setup>
import { useRouter } from 'vue-router'
import { Upload, FolderOpened, ChatDotRound } from '@element-plus/icons-vue'

const router = useRouter()

const features = [
  { icon: Upload, title: '上传文档', desc: '支持 PDF、DOCX 格式的学术论文', path: '/upload', color: '#409eff' },
  { icon: FolderOpened, title: '知识库管理', desc: '查看和管理已上传的论文文献', path: '/library', color: '#67c23a' },
  { icon: ChatDotRound, title: '智能问答', desc: '基于文献内容的 AI 对话问答', path: '/chat', color: '#e6a23c' },
]
</script>

<template>
  <div class="home-container">
    <h1>欢迎使用 知研</h1>
    <p class="subtitle">基于 RAG 检索增强生成的学术论文阅读助手</p>

    <div class="feature-cards">
      <el-card
        v-for="item in features"
        :key="item.path"
        shadow="hover"
        @click="router.push(item.path)"
      >
        <div class="feature-icon" :style="{ color: item.color }">
          <el-icon :size="40"><component :is="item.icon" /></el-icon>
        </div>
        <h3>{{ item.title }}</h3>
        <p style="color: #909399; font-size: 13px; margin-top: 8px;">{{ item.desc }}</p>
      </el-card>
    </div>
  </div>
</template>
