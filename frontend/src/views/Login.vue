<template>
  <div class="login-container">
    <div class="login-bg"></div>
    <div class="login-card">
      <div class="login-header">
        <h1>数据处理管理系统</h1>
        <p>Software Management System</p>
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
            <template #prefix>
              <UserOutlined />
            </template>
          </a-input>
        </a-form-item>

        <a-form-item name="password">
          <a-input-password
            v-model:value="formState.password"
            placeholder="请输入密码"
            size="large"
          >
            <template #prefix>
              <LockOutlined />
            </template>
          </a-input-password>
        </a-form-item>

        <a-form-item>
          <a-checkbox v-model:checked="rememberMe">记住我</a-checkbox>
        </a-form-item>

        <a-form-item>
          <a-button
            type="primary"
            html-type="submit"
            size="large"
            block
            :loading="loading"
          >
            登录
          </a-button>
        </a-form-item>
      </a-form>

      <div class="login-footer">
        <p>默认账号: admin / admin123</p>
      </div>
    </div>
    
    <!-- 滑动验证弹窗 -->
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

// 验证码数据
const captchaKey = ref('')
const xOffset = ref(0)

const formState = reactive({
  username: '',
  password: '',
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

// 点击登录按钮 - 显示验证弹窗
async function handleLoginClick() {
  showVerifyModal.value = true
}

// 验证成功回调
function handleVerifySuccess(key: string, offset: number) {
  captchaKey.value = key
  xOffset.value = offset
  showVerifyModal.value = false
  
  // 执行登录
  performLogin()
}

// 验证失败回调
function handleVerifyError() {
  message.error('验证失败，请重试')
}

// 执行登录
async function performLogin() {
  loading.value = true
  
  try {
    // 传递验证码数据
    const loginData = {
      ...formState,
      captcha_key: captchaKey.value,
      x_offset: xOffset.value
    }
    
    const result = await userStore.loginAction(loginData)
    
    if (result.success) {
      message.success(result.message)
      // 跳转到原来想访问的页面或首页
      const redirect = route.query.redirect as string || '/dashboard'
      router.push(redirect)
    } else {
      message.error(result.message)
      // 登录失败，重置验证码
      captchaKey.value = ''
      xOffset.value = 0
    }
  } finally {
    loading.value = false
  }
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
}

.login-bg {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  z-index: 0;
}

.login-bg::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 50%);
  animation: pulse 15s infinite;
}

@keyframes pulse {
  0%, 100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(10%, 10%);
  }
}

.login-card {
  position: relative;
  z-index: 1;
  width: 400px;
  padding: 40px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(10px);
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.login-header h1 {
  margin: 0;
  font-size: 28px;
  font-weight: 700;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.login-header p {
  margin: 8px 0 0;
  color: #999;
  font-size: 14px;
}

.login-form {
  margin-top: 24px;
}

.login-form :deep(.ant-input-affix-wrapper) {
  border-radius: 8px;
}

.login-form :deep(.ant-btn-primary) {
  height: 44px;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 500;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
}

.login-form :deep(.ant-btn-primary:hover) {
  opacity: 0.9;
}

.login-footer {
  text-align: center;
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #eee;
}

.login-footer p {
  margin: 0;
  color: #999;
  font-size: 12px;
}
</style>
