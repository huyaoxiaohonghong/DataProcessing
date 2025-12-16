<template>
  <div class="dashboard">
    <h2 class="page-title">仪表盘</h2>
    
    <!-- 统计卡片 -->
    <a-row :gutter="[24, 24]">
      <a-col :xs="24" :sm="12" :lg="6">
        <div class="stat-card stat-card-primary">
          <div class="stat-icon">
            <FolderOutlined />
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.total_files }}</div>
            <div class="stat-label">总文件数</div>
          </div>
        </div>
      </a-col>
      
      <a-col :xs="24" :sm="12" :lg="6">
        <div class="stat-card stat-card-success">
          <div class="stat-icon">
            <HddOutlined />
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ formatSize(stats.total_size) }}</div>
            <div class="stat-label">总存储占用</div>
          </div>
        </div>
      </a-col>
      
      <a-col :xs="24" :sm="12" :lg="6">
        <div class="stat-card stat-card-warning">
          <div class="stat-icon">
            <CloudDownloadOutlined />
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.total_downloads }}</div>
            <div class="stat-label">总下载次数</div>
          </div>
        </div>
      </a-col>
      
      <a-col :xs="24" :sm="12" :lg="6">
        <div class="stat-card stat-card-danger">
          <div class="stat-icon">
            <TeamOutlined />
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ userStore.userInfo?.role_display || '用户' }}</div>
            <div class="stat-label">当前角色</div>
          </div>
        </div>
      </a-col>
    </a-row>

    <!-- 快捷操作 -->
    <a-card title="快捷操作" class="quick-actions" :bordered="false">
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
    </a-card>

    <!-- 欢迎信息 -->
    <a-card class="welcome-card" :bordered="false">
      <a-result
        status="success"
        title="欢迎使用数据处理系统"
        sub-title="您可以在此上传、下载、管理您的数据文件。"
      >
        <template #extra>
          <a-button type="primary" @click="$router.push('/files')">
            浏览文件
          </a-button>
        </template>
      </a-result>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, onMounted } from 'vue'
import {
  FolderOutlined,
  HddOutlined,
  TeamOutlined,
  CloudDownloadOutlined,
  FolderAddOutlined,
  UserOutlined,
} from '@ant-design/icons-vue'
import { useUserStore } from '@/stores/user'
import { getFileStatistics } from '@/api/file'

const userStore = useUserStore()

// 统计数据
const stats = reactive({
  total_files: 0,
  total_size: 0,
  total_downloads: 0,
})

onMounted(async () => {
    try {
        const res = await getFileStatistics()
        if (res.data.code === 200) {
            Object.assign(stats, res.data.data)
        }
    } catch (e) {
        console.error('获取统计数据失败', e)
    }
})

function formatSize(bytes: number) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}
</script>

<style scoped>
.dashboard {
  padding: 0;
}

.page-title {
  margin: 0 0 24px;
  font-size: 24px;
  font-weight: 600;
  color: #1f2937;
}

.stat-card {
  display: flex;
  align-items: center;
  padding: 24px;
  border-radius: 12px;
  color: #fff;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s, box-shadow 0.3s;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.stat-card-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-card-success {
  background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
}

.stat-card-warning {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.stat-card-danger {
  background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);
}

.stat-icon {
  font-size: 48px;
  opacity: 0.8;
  margin-right: 20px;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  line-height: 1.2;
}

.stat-label {
  font-size: 14px;
  opacity: 0.9;
  margin-top: 4px;
}

.quick-actions {
  margin-top: 24px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.welcome-card {
  margin-top: 24px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}
</style>
