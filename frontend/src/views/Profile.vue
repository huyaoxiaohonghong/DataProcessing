<template>
  <div class="profile-page">
    <h2 class="page-title">个人中心</h2>
    
    <a-row :gutter="24">
      <a-col :span="8">
        <a-card title="个人信息" :bordered="false" class="profile-card">
          <div class="avatar-section">
            <a-avatar :size="100">
              {{ userStore.username?.charAt(0)?.toUpperCase() }}
            </a-avatar>
            <h3>{{ userStore.userInfo?.username }}</h3>
            <a-tag :color="roleColor">{{ userStore.userInfo?.role_display }}</a-tag>
          </div>
          
          <a-descriptions :column="1" class="info-list">
            <a-descriptions-item label="邮箱">
              {{ userStore.userInfo?.email || '-' }}
            </a-descriptions-item>
            <a-descriptions-item label="手机">
              {{ userStore.userInfo?.phone || '-' }}
            </a-descriptions-item>
            <a-descriptions-item label="部门">
              {{ userStore.userInfo?.department || '-' }}
            </a-descriptions-item>
            <a-descriptions-item label="注册时间">
              {{ formatDate(userStore.userInfo?.date_joined) }}
            </a-descriptions-item>
          </a-descriptions>
        </a-card>
      </a-col>
      
      <a-col :span="16">
        <a-card title="修改密码" :bordered="false" class="password-card">
          <a-form
            :model="passwordForm"
            :rules="passwordRules"
            @finish="handleChangePassword"
            layout="vertical"
            style="max-width: 400px;"
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
              <a-button type="primary" html-type="submit" :loading="loading">
                修改密码
              </a-button>
            </a-form-item>
          </a-form>
        </a-card>
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

const passwordForm = reactive({
  old_password: '',
  new_password: '',
  new_password_confirm: '',
})

const passwordRules = {
  old_password: [{ required: true, message: '请输入原密码' }],
  new_password: [
    { required: true, message: '请输入新密码' },
    { min: 6, message: '密码至少6个字符' },
  ],
  new_password_confirm: [
    { required: true, message: '请确认新密码' },
    {
      validator: (_: any, value: string) => {
        if (value !== passwordForm.new_password) {
          return Promise.reject('两次输入的密码不一致')
        }
        return Promise.resolve()
      },
    },
  ],
}

const roleColor = computed(() => {
  const colors: Record<string, string> = {
    admin: 'red',
    operator: 'blue',
    viewer: 'green',
  }
  return colors[userStore.userInfo?.role || 'viewer'] || 'default'
})

function formatDate(date?: string) {
  if (!date) return '-'
  return new Date(date).toLocaleDateString('zh-CN')
}

async function handleChangePassword() {
  loading.value = true
  try {
    await changePassword(passwordForm)
    message.success('密码修改成功')
    // 清空表单
    passwordForm.old_password = ''
    passwordForm.new_password = ''
    passwordForm.new_password_confirm = ''
  } catch (error: any) {
    message.error(error.response?.data?.message || '修改失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.profile-page {
  padding: 0;
}

.page-title {
  margin: 0 0 24px;
  font-size: 24px;
  font-weight: 600;
  color: #1f2937;
}

.profile-card,
.password-card {
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.avatar-section {
  text-align: center;
  padding: 24px 0;
  border-bottom: 1px solid #f0f0f0;
  margin-bottom: 24px;
}

.avatar-section h3 {
  margin: 16px 0 8px;
  font-size: 18px;
}

.info-list {
  padding: 0 16px;
}
</style>
