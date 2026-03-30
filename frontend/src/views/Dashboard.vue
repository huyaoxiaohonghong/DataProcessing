<template>
  <div class="dashboard">
    <h2 class="page-title">仪表盘</h2>
    
    <!-- 3D Stat Cards -->
    <a-row :gutter="[20, 20]">
      <a-col :xs="24" :sm="12" :lg="6">
        <div class="stat-card stat-card--primary">
          <div class="stat-icon"><FolderOutlined /></div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.total_files }}</div>
            <div class="stat-label">总文件数</div>
          </div>
        </div>
      </a-col>
      <a-col :xs="24" :sm="12" :lg="6">
        <div class="stat-card stat-card--success">
          <div class="stat-icon"><HddOutlined /></div>
          <div class="stat-content">
            <div class="stat-value">{{ formatSize(stats.total_size) }}</div>
            <div class="stat-label">总存储占用</div>
          </div>
        </div>
      </a-col>
      <a-col :xs="24" :sm="12" :lg="6">
        <div class="stat-card stat-card--warning">
          <div class="stat-icon"><CloudDownloadOutlined /></div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.total_downloads }}</div>
            <div class="stat-label">总下载次数</div>
          </div>
        </div>
      </a-col>
      <a-col :xs="24" :sm="12" :lg="6">
        <div class="stat-card stat-card--accent">
          <div class="stat-icon"><TeamOutlined /></div>
          <div class="stat-content">
            <div class="stat-value">{{ userStore.userInfo?.role_display || '用户' }}</div>
            <div class="stat-label">当前角色</div>
          </div>
        </div>
      </a-col>
    </a-row>

    <!-- Quick Actions -->
    <div class="glass-section">
      <h3 class="section-title">快捷操作</h3>
      <a-row :gutter="16">
        <a-col :span="8">
          <a-button type="primary" block size="large" @click="$router.push('/files')">
            <FolderAddOutlined /> 上传文件
          </a-button>
        </a-col>
        <a-col :span="8">
          <a-button block size="large" @click="$router.push('/profile')">
            <UserOutlined /> 个人中心
          </a-button>
        </a-col>
        <a-col :span="8" v-if="userStore.isAdmin">
          <a-button block size="large" @click="$router.push('/users')">
            <TeamOutlined /> 用户管理
          </a-button>
        </a-col>
      </a-row>
    </div>

    <!-- Welcome -->
    <div class="glass-section">
      <a-result
        status="success"
        title="欢迎使用数据处理系统"
        sub-title="您可以在此上传、下载、管理您的数据文件。"
      >
        <template #extra>
          <a-button type="primary" @click="$router.push('/files')">浏览文件</a-button>
        </template>
      </a-result>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, onMounted } from 'vue'
import {
  FolderOutlined, HddOutlined, TeamOutlined, CloudDownloadOutlined,
  FolderAddOutlined, UserOutlined,
} from '@ant-design/icons-vue'
import { useUserStore } from '@/stores/user'
import { getFileStatistics } from '@/api/file'

const userStore = useUserStore()
const stats = reactive({ total_files: 0, total_size: 0, total_downloads: 0 })

onMounted(async () => {
  try {
    const res = await getFileStatistics()
    if (res.data.code === 200) Object.assign(stats, res.data.data)
  } catch (e) { console.error('获取统计数据失败', e) }
})

function formatSize(bytes: number) {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}
</script>

<style scoped>
.page-title {
  margin: 0 0 24px;
  font-size: 24px;
  font-weight: 700;
  font-family: 'Fira Code', monospace;
  color: var(--color-text);
}

/* 3D Glass Stat Cards */
.stat-card {
  display: flex;
  align-items: center;
  padding: 24px;
  background: var(--glass-bg);
  backdrop-filter: blur(var(--glass-blur));
  -webkit-backdrop-filter: blur(var(--glass-blur));
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--glass-shadow);
  transform-style: preserve-3d;
  transition: all 400ms cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
  position: relative;
  overflow: hidden;
}

.stat-card::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: inherit;
  background: linear-gradient(135deg, rgba(255,255,255,0.08) 0%, transparent 50%);
  pointer-events: none;
}

.stat-card:hover {
  transform: perspective(1000px) rotateX(2deg) rotateY(-3deg) translateZ(8px);
  border-color: var(--color-border-hover);
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.4),
    0 0 24px var(--glow);
}

.stat-card--primary  { --glow: rgba(99, 102, 241, 0.2); }
.stat-card--success  { --glow: rgba(16, 185, 129, 0.2); }
.stat-card--warning  { --glow: rgba(245, 158, 11, 0.2); }
.stat-card--accent   { --glow: rgba(139, 92, 246, 0.2); }

.stat-icon {
  font-size: 36px;
  margin-right: 20px;
  opacity: 0.7;
  color: var(--color-text-muted);
}

.stat-card--primary .stat-icon { color: #6366F1; }
.stat-card--success .stat-icon { color: #10B981; }
.stat-card--warning .stat-icon { color: #F59E0B; }
.stat-card--accent  .stat-icon { color: #8B5CF6; }

.stat-value {
  font-family: 'Fira Code', monospace;
  font-size: 28px;
  font-weight: 700;
  color: var(--color-text);
  line-height: 1.2;
}

.stat-card:hover .stat-value {
  text-shadow: 0 0 12px var(--glow);
}

.stat-label {
  font-family: 'Fira Sans', sans-serif;
  font-size: 13px;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-top: 4px;
}

/* Glass Sections */
.glass-section {
  margin-top: 24px;
  padding: 24px;
  background: var(--glass-bg);
  backdrop-filter: blur(var(--glass-blur));
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--glass-shadow);
}

.section-title {
  margin: 0 0 16px;
  font-family: 'Fira Code', monospace;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text);
}
</style>
