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
        <img src="@/assets/vue.svg" alt="Logo" />
        <span v-show="!collapsed">数据处理系统</span>
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
        
        <!-- 数据处理模块 -->
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
          <a-menu-item key="logs/login" @click="router.push('/logs/login')">
            <template #icon><FileProtectOutlined /></template>
            <span>登录日志</span>
          </a-menu-item>
          <a-menu-item key="logs/operation" @click="router.push('/logs/operation')">
            <template #icon><FileSearchOutlined /></template>
            <span>操作日志</span>
          </a-menu-item>
        </a-sub-menu>
        
        <a-menu-item v-if="userStore.isAdmin" key="departments" @click="router.push('/departments')">
          <template #icon><ApartmentOutlined /></template>
          <span>部门管理</span>
        </a-menu-item>
        
        <a-menu-item v-if="userStore.isAdmin" key="menus" @click="router.push('/menus')">
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
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </a-layout-content>

      <!-- 底部 -->
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
  DashboardOutlined,
  FolderOutlined,
  TeamOutlined,
  FileTextOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  UserOutlined,
  LogoutOutlined,
  FileProtectOutlined,
  FileSearchOutlined,
  ApartmentOutlined,
  MenuOutlined,
  SwapOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons-vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const collapsed = ref(false)
const selectedKeys = ref<string[]>(['dashboard'])
const openKeys = ref<string[]>(['logs', 'processing']) // 默认展开日志和数据处理菜单

// 根据路由设置选中菜单
watch(
  () => route.path,
  (path) => {
    if (path) {
      if (path.includes('/logs/login')) selectedKeys.value = ['logs/login']
      else if (path.includes('/logs/operation')) selectedKeys.value = ['logs/operation']
      else if (path.includes('/processing/mappings')) selectedKeys.value = ['processing/mappings']
      else if (path.includes('/processing/tasks')) selectedKeys.value = ['processing/tasks']
      else selectedKeys.value = [path.split('/')[1] || 'dashboard']
    }
  },
  { immediate: true }
)

// 菜单点击
function handleMenuClick({ key }: { key: string }) {
  router.push(`/${key}`)
}

// 退出登录
async function handleLogout() {
  await userStore.logoutAction()
}

// 获取用户信息
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
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.15);
}

.logo {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  background: rgba(255, 255, 255, 0.05);
  margin: 0;
  overflow: hidden;
}

.logo img {
  width: 32px;
  height: 32px;
}

.logo span {
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  white-space: nowrap;
}

.header {
  background: #fff;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
}

.header-left {
  display: flex;
  align-items: center;
}

.trigger {
  font-size: 18px;
  cursor: pointer;
  transition: color 0.3s;
  padding: 0 12px;
}

.trigger:hover {
  color: #1890ff;
}

.header-right {
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: background 0.3s;
}

.user-info:hover {
  background: #f5f5f5;
}

.username {
  color: #333;
}

.content {
  margin: 24px;
  padding: 24px;
  background: #fff;
  border-radius: 8px;
  min-height: calc(100vh - 64px - 70px - 48px);
}

.footer {
  text-align: center;
  color: #999;
  background: transparent;
}

/* 路由切换动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
