<template>
  <div class="profile-page">
    <h2 class="page-title">个人中心</h2>
    
    <a-row :gutter="24">
      <a-col :span="8">
        <div class="glass-panel">
          <div class="panel-header">个人信息</div>
          <div class="avatar-section">
            <a-avatar :size="100">
              {{ userStore.username?.charAt(0)?.toUpperCase() }}
            </a-avatar>
            <h3 class="avatar-name">{{ userStore.userInfo?.username }}</h3>
            <a-tag :color="roleColor">{{ userStore.userInfo?.role_display }}</a-tag>
          </div>
          
          <div class="info-list">
            <div class="info-item">
              <span class="info-label">邮箱</span>
              <span class="info-value">{{ userStore.userInfo?.email || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">手机</span>
              <span class="info-value">{{ userStore.userInfo?.phone || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">部门</span>
              <span class="info-value">{{ userStore.userInfo?.department || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">注册时间</span>
              <span class="info-value">{{ formatDate(userStore.userInfo?.date_joined) }}</span>
            </div>
          </div>
        </div>
      </a-col>
      
      <a-col :span="16">
        <div class="glass-panel">
          <div class="panel-header">修改密码</div>
          <a-form
            :model="passwordForm"
            :rules="passwordRules"
            @finish="handleChangePassword"
            layout="vertical"
            style="max-width: 400px; padding: 24px;"
          >
            <a-form-item label="原密码" name="old_password">
              <a-input-password v-model:value="passwordForm.old_password" />
            </a-form-item>
            <a-form-item label="新密码" name="new_password">
              <a-input-password v-model:value="passwordForm.new_password" />
            </a-form-item>
            <a-form-item label="确认新密码" name="new_password_confirm">
              <a-input-password v-model:value="passwordForm.new_password_confirm" />
            </a-form-item>
            <a-form-item>
              <a-button type="primary" html-type="submit" :loading="loading">修改密码</a-button>
            </a-form-item>
          </a-form>
        </div>
      </a-col>
    </a-row>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, computed } from 'vue'
import { message } from 'ant-design-vue'
import { useUserStore } from '@/stores/user'
import { changePassword } from '@/api/user'

const userStore = useUserStore()
const loading = ref(false)
const passwordForm = reactive({ old_password: '', new_password: '', new_password_confirm: '' })

const passwordRules = {
  old_password: [{ required: true, message: '请输入原密码' }],
  new_password: [{ required: true, message: '请输入新密码' }, { min: 6, message: '密码至少6个字符' }],
  new_password_confirm: [
    { required: true, message: '请确认新密码' },
    { validator: (_: any, value: string) => value !== passwordForm.new_password ? Promise.reject('两次输入的密码不一致') : Promise.resolve() },
  ],
}

const roleColor = computed(() => {
  const m: Record<string, string> = { super_admin: 'purple', admin: 'red', user: 'blue' }
  return m[userStore.userInfo?.role || ''] || 'default'
})

function formatDate(date?: string) {
  return date ? new Date(date).toLocaleDateString('zh-CN') : '-'
}

async function handleChangePassword() {
  loading.value = true
  try {
    await changePassword(passwordForm)
    message.success('密码修改成功')
    Object.assign(passwordForm, { old_password: '', new_password: '', new_password_confirm: '' })
  } catch (error: any) {
    message.error(error.response?.data?.message || '修改失败')
  } finally { loading.value = false }
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

.glass-panel {
  background: var(--glass-bg);
  backdrop-filter: blur(var(--glass-blur));
  -webkit-backdrop-filter: blur(var(--glass-blur));
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--glass-shadow);
  overflow: hidden;
}

.panel-header {
  padding: 16px 24px;
  font-family: 'Fira Code', monospace;
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text);
  border-bottom: 1px solid var(--color-border);
}

.avatar-section {
  text-align: center;
  padding: 32px 24px 24px;
  border-bottom: 1px solid var(--color-border);
}

.avatar-name {
  margin: 16px 0 8px;
  font-size: 18px;
  color: var(--color-text);
  font-family: 'Fira Code', monospace;
}

.info-list {
  padding: 16px 24px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  padding: 12px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
}

.info-item:last-child {
  border-bottom: none;
}

.info-label {
  color: var(--color-text-muted);
  font-size: 13px;
}

.info-value {
  color: var(--color-text);
  font-size: 13px;
}
</style>
