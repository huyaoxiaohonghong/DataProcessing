<template>
  <div class="login-container">
    <!-- Ambient glow orbs -->
    <div class="orb orb-1"></div>
    <div class="orb orb-2"></div>
    <div class="orb orb-3"></div>

    <div class="login-card">
      <div class="login-header">
        <div class="logo-icon">D</div>
        <h1>数据处理管理系统</h1>
        <p>Data Processing System</p>
      </div>
      
      <a-form
        :model="formState"
        :rules="rules"
        @finish="handleLoginClick"
        layout="vertical"
        class="login-form"
        ref="formRef"
      >
        <a-form-item name="username">
          <a-input
            v-model:value="formState.username"
            placeholder="请输入用户名"
            size="large"
          >
            <template #prefix><UserOutlined /></template>
          </a-input>
        </a-form-item>

        <a-form-item name="password">
          <a-input-password
            v-model:value="formState.password"
            placeholder="请输入密码"
            size="large"
          >
            <template #prefix><LockOutlined /></template>
          </a-input-password>
        </a-form-item>

        <a-form-item>
          <a-checkbox v-model:checked="rememberMe">记住我</a-checkbox>
        </a-form-item>

        <a-form-item>
          <a-button type="primary" html-type="submit" size="large" block :loading="loading">
            登录
          </a-button>
        </a-form-item>
      </a-form>

      <div class="login-footer">
        <p>默认账号: admin / admin123</p>
      </div>
    </div>
    
    <a-modal
      v-model:open="showVerifyModal"
      title="安全验证"
      :footer="null"
      :maskClosable="false"
      :width="340"
      centered
    >
      <SlideVerify 
        @success="handleVerifySuccess"
        @error="handleVerifyError"
      />
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import { UserOutlined, LockOutlined } from '@ant-design/icons-vue'
import { useUserStore } from '@/stores/user'
import SlideVerify from '@/components/SlideVerify/index.vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const loading = ref(false)
const rememberMe = ref(false)
const showVerifyModal = ref(false)

// Enhanced captcha verification data
const captchaKey = ref('')
const xOffset = ref(0)
const trajectory = ref('')
const duration = ref(0)
const captchaFingerprint = ref('')

const formState = reactive({ username: '', password: '' })
const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

function handleLoginClick() { showVerifyModal.value = true }

function handleVerifySuccess(data: { captchaKey: string; xOffset: number; trajectory: string; duration: number; fingerprint: string }) {
  captchaKey.value = data.captchaKey
  xOffset.value = data.xOffset
  trajectory.value = data.trajectory
  duration.value = data.duration
  captchaFingerprint.value = data.fingerprint
  showVerifyModal.value = false
  performLogin()
}

function handleVerifyError() { message.error('验证失败，请重试') }

function resetCaptchaData() {
  captchaKey.value = ''
  xOffset.value = 0
  trajectory.value = ''
  duration.value = 0
  captchaFingerprint.value = ''
}

async function performLogin() {
  loading.value = true
  try {
    const result = await userStore.loginAction({
      ...formState,
      captcha_key: captchaKey.value,
      x_offset: xOffset.value,
      trajectory: trajectory.value,
      duration: duration.value,
      fingerprint: captchaFingerprint.value
    })
    if (result.success) {
      message.success(result.message)
      router.push((route.query.redirect as string) || '/dashboard')
    } else {
      if (result.status === 429) {
        message.warning(result.message)
      } else {
        message.error(result.message)
      }
      resetCaptchaData()
    }
  } finally { loading.value = false }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  background: #000;
}

.orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(120px);
  pointer-events: none;
  z-index: 0;
}

.orb-1 {
  width: 500px; height: 500px;
  top: -150px; right: -100px;
  background: radial-gradient(circle, rgba(99,102,241,0.3), transparent 70%);
  animation: float 20s ease-in-out infinite;
}

.orb-2 {
  width: 400px; height: 400px;
  bottom: -100px; left: -80px;
  background: radial-gradient(circle, rgba(139,92,246,0.25), transparent 70%);
  animation: float 25s ease-in-out infinite reverse;
}

.orb-3 {
  width: 300px; height: 300px;
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  background: radial-gradient(circle, rgba(99,102,241,0.1), transparent 70%);
  animation: pulse-glow 10s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translate(0, 0); }
  50% { transform: translate(30px, -20px); }
}

@keyframes pulse-glow {
  0%, 100% { opacity: 0.5; transform: translate(-50%, -50%) scale(1); }
  50% { opacity: 1; transform: translate(-50%, -50%) scale(1.2); }
}

.login-card {
  position: relative;
  z-index: 1;
  width: 420px;
  padding: 48px 40px;
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 24px;
  box-shadow: 0 24px 64px rgba(0, 0, 0, 0.5);
}

.login-header {
  text-align: center;
  margin-bottom: 36px;
}

.login-header .logo-icon {
  width: 56px; height: 56px;
  border-radius: 16px;
  background: linear-gradient(135deg, #6366F1, #8B5CF6);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-family: 'Fira Code', monospace;
  font-weight: 700;
  font-size: 24px;
  color: #fff;
  box-shadow: 0 8px 24px rgba(99, 102, 241, 0.4);
  margin-bottom: 16px;
}

.login-header h1 {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
  font-family: 'Fira Code', monospace;
  color: #F1F5F9;
}

.login-header p {
  margin: 6px 0 0;
  color: #64748B;
  font-size: 13px;
  letter-spacing: 0.05em;
}

.login-form :deep(.ant-input-affix-wrapper) {
  background: rgba(255, 255, 255, 0.04) !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  border-radius: 10px !important;
  height: 48px;
}

.login-form :deep(.ant-input-affix-wrapper:focus),
.login-form :deep(.ant-input-affix-wrapper-focused) {
  border-color: #6366F1 !important;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15) !important;
}

.login-form :deep(.ant-btn-primary) {
  height: 48px;
  border-radius: 10px;
  font-size: 16px;
  font-weight: 600;
}

.login-footer {
  text-align: center;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.login-footer p {
  margin: 0;
  color: #475569;
  font-size: 12px;
}
</style>
