<template>
  <a-layout class="main-layout">
    <!-- 侧边栏 -->
    <a-layout-sider 
      v-model:collapsed="collapsed" 
      :trigger="null" 
      collapsible
      class="sider"
      theme="dark"
    >
      <div class="logo">
        <div class="logo-icon">D</div>
        <span v-show="!collapsed" class="logo-text">数据处理系统</span>
      </div>
      
      <a-menu
        v-model:selectedKeys="selectedKeys"
        v-model:openKeys="openKeys"
        theme="dark"
        mode="inline"
        @click="handleMenuClick"
      >
        <a-menu-item key="dashboard">
          <template #icon><DashboardOutlined /></template>
          <span>仪表盘</span>
        </a-menu-item>
        
        <a-menu-item key="files">
          <template #icon><FolderOutlined /></template>
          <span>文件管理</span>
        </a-menu-item>
        
        <a-sub-menu key="processing">
          <template #icon><SwapOutlined /></template>
          <template #title>数据处理</template>
          <a-menu-item key="processing/mappings">
            <template #icon><SwapOutlined /></template>
            <span>映射配置</span>
          </a-menu-item>
          <a-menu-item key="processing/tasks">
            <template #icon><ThunderboltOutlined /></template>
            <span>处理任务</span>
          </a-menu-item>
        </a-sub-menu>
        
        <a-menu-item v-if="userStore.isAdmin" key="users">
          <template #icon><TeamOutlined /></template>
          <span>用户管理</span>
        </a-menu-item>
        
        <a-sub-menu v-if="userStore.isAdmin" key="logs">
          <template #icon><FileTextOutlined /></template>
          <template #title>系统日志</template>
          <a-menu-item key="logs/login">
            <template #icon><FileProtectOutlined /></template>
            <span>登录日志</span>
          </a-menu-item>
          <a-menu-item key="logs/operation">
            <template #icon><FileSearchOutlined /></template>
            <span>操作日志</span>
          </a-menu-item>
        </a-sub-menu>
        
        <a-menu-item v-if="userStore.isAdmin" key="departments">
          <template #icon><ApartmentOutlined /></template>
          <span>部门管理</span>
        </a-menu-item>
        
        <a-menu-item v-if="userStore.isAdmin" key="menus">
          <template #icon><MenuOutlined /></template>
          <span>菜单管理</span>
        </a-menu-item>
      </a-menu>
    </a-layout-sider>

    <a-layout>
      <!-- 顶部导航 -->
      <a-layout-header class="header">
        <div class="header-left">
          <MenuFoldOutlined 
            v-if="!collapsed" 
            class="trigger" 
            @click="collapsed = true" 
          />
          <MenuUnfoldOutlined 
            v-else 
            class="trigger" 
            @click="collapsed = false" 
          />
        </div>
        
        <div class="header-right">
          <a-dropdown>
            <div class="user-info">
              <a-avatar :size="32">
                {{ userStore.username?.charAt(0)?.toUpperCase() }}
              </a-avatar>
              <span class="username">{{ userStore.username }}</span>
            </div>
            <template #overlay>
              <a-menu>
                <a-menu-item key="profile" @click="router.push('/profile')">
                  <UserOutlined />
                  <span>个人中心</span>
                </a-menu-item>
                <a-menu-divider />
                <a-menu-item key="logout" @click="handleLogout">
                  <LogoutOutlined />
                  <span>退出登录</span>
                </a-menu-item>
              </a-menu>
            </template>
          </a-dropdown>
        </div>
      </a-layout-header>

      <!-- 内容区 -->
      <a-layout-content class="content">
        <router-view v-slot="{ Component, route: currentRoute }">
          <transition name="fade" mode="out-in">
            <keep-alive :include="cachedViews">
              <component :is="Component" :key="currentRoute.path" />
            </keep-alive>
          </transition>
        </router-view>
      </a-layout-content>

      <a-layout-footer class="footer">
        数据处理系统 ©2025 Created by Antigravity
      </a-layout-footer>
    </a-layout>
  </a-layout>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import {
  DashboardOutlined, FolderOutlined, TeamOutlined, FileTextOutlined,
  MenuFoldOutlined, MenuUnfoldOutlined, UserOutlined, LogoutOutlined,
  FileProtectOutlined, FileSearchOutlined, ApartmentOutlined, MenuOutlined,
  SwapOutlined, ThunderboltOutlined,
} from '@ant-design/icons-vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const collapsed = ref(false)
const selectedKeys = ref<string[]>(['dashboard'])
const openKeys = ref<string[]>(['logs', 'processing'])
const cachedViews = ref(['Dashboard', 'Files', 'MappingList', 'TaskList'])

watch(() => route.path, (path) => {
  if (path) {
    if (path.includes('/logs/login')) selectedKeys.value = ['logs/login']
    else if (path.includes('/logs/operation')) selectedKeys.value = ['logs/operation']
    else if (path.includes('/processing/mappings')) selectedKeys.value = ['processing/mappings']
    else if (path.includes('/processing/tasks')) selectedKeys.value = ['processing/tasks']
    else selectedKeys.value = [path.split('/')[1] || 'dashboard']
  }
}, { immediate: true })

function handleMenuClick({ key }: { key: string }) {
  router.push(`/${key}`)
}

async function handleLogout() {
  await userStore.logoutAction()
}

onMounted(async () => {
  if (userStore.isLoggedIn && !userStore.userInfo) {
    await userStore.fetchUserInfo()
  }
})
</script>

<style scoped>
.main-layout {
  min-height: 100vh;
}

.sider {
  background: rgba(255, 255, 255, 0.03) !important;
  backdrop-filter: blur(20px);
  border-right: 1px solid rgba(255, 255, 255, 0.06);
}

.logo {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  overflow: hidden;
}

.logo-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: linear-gradient(135deg, #6366F1, #8B5CF6);
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: 'Fira Code', monospace;
  font-weight: 700;
  font-size: 18px;
  color: #fff;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
  flex-shrink: 0;
}

.logo-text {
  color: #F1F5F9;
  font-size: 15px;
  font-weight: 600;
  white-space: nowrap;
  font-family: 'Fira Sans', sans-serif;
}

.header {
  background: rgba(255, 255, 255, 0.04) !important;
  backdrop-filter: blur(16px);
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.trigger {
  font-size: 18px;
  cursor: pointer;
  color: var(--color-text-muted);
  transition: color var(--transition-smooth);
  padding: 0 12px;
}

.trigger:hover {
  color: var(--color-primary);
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: var(--radius-sm);
  transition: background var(--transition-smooth);
}

.user-info:hover {
  background: rgba(255, 255, 255, 0.06);
}

.username {
  color: var(--color-text);
}

.content {
  margin: 24px;
  padding: 24px;
  background: rgba(255, 255, 255, 0.03);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: var(--radius-lg);
  min-height: calc(100vh - 64px - 70px - 48px);
}

.footer {
  text-align: center;
  color: var(--color-text-dim);
  background: transparent;
  font-size: 13px;
}
</style>
