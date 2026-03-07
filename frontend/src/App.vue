<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  Upload,
  FolderOpened,
  ChatDotRound,
  Setting,
  HomeFilled,
} from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()

const isCollapse = ref(false)

const activeMenu = computed(() => route.path)

function handleMenuSelect(path) {
  router.push(path)
}

const pageTitle = computed(() => {
  const titles = {
    '/': '首页',
    '/upload': '上传文档',
    '/library': '知识库',
    '/chat': '智能对话',
    '/settings': '设置',
  }
  return titles[route.path] || '知研'
})
</script>

<template>
  <el-container style="height: 100vh">
    <!-- 侧边栏 -->
    <el-aside :width="isCollapse ? '64px' : '200px'" style="transition: width 0.3s; background: #304156;">
      <div class="sidebar-header">
        <span v-show="!isCollapse" class="logo-title">知研</span>
        <span v-show="!isCollapse" class="logo-subtitle">ScholarRAG</span>
        <span v-show="isCollapse" class="logo-title" style="font-size: 16px;">知</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409eff"
        :collapse="isCollapse"
        @select="handleMenuSelect"
        style="border-right: none;"
      >
        <el-menu-item index="/">
          <el-icon><HomeFilled /></el-icon>
          <template #title>首页</template>
        </el-menu-item>
        <el-menu-item index="/upload">
          <el-icon><Upload /></el-icon>
          <template #title>上传文档</template>
        </el-menu-item>
        <el-menu-item index="/library">
          <el-icon><FolderOpened /></el-icon>
          <template #title>知识库</template>
        </el-menu-item>
        <el-menu-item index="/chat">
          <el-icon><ChatDotRound /></el-icon>
          <template #title>智能对话</template>
        </el-menu-item>
        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          <template #title>设置</template>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 主区域 -->
    <el-container>
      <el-header class="main-header" height="60px">
        <div style="display: flex; align-items: center; gap: 12px;">
          <el-icon
            :size="20"
            style="cursor: pointer; color: #606266;"
            @click="isCollapse = !isCollapse"
          >
            <component :is="isCollapse ? 'Expand' : 'Fold'" />
          </el-icon>
          <h2>{{ pageTitle }}</h2>
        </div>
        <el-tag type="info" effect="plain">基于 RAG 的论文阅读助手</el-tag>
      </el-header>

      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>
