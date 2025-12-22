<template>
  <div class="slide-verify">
    <div class="verify-container">
      <!-- 背景图和拼图 -->
      <div class="image-container">
        <img :src="captchaData.background" alt="背景" class="bg-image" />
        <img 
          :src="captchaData.puzzle" 
          alt="拼图" 
          class="puzzle-image"
          :style="{ top: `${captchaData.y}px`, left: `${puzzleLeft}px` }"
        />
      </div>
      
      <!-- 滑块轨道 -->
      <div class="slider-track">
        <div class="slider-bar" :style="{ width: `${sliderWidth}px` }">
          <span class="slider-text" v-if="!isSliding && !verifyStatus">{{ sliderText }}</span>
          <span class="slider-text success" v-if="verifyStatus === 'success'">✓ 验证成功</span>
          <span class="slider-text error" v-if="verifyStatus === 'error'">✗ 验证失败</span>
        </div>
        <div 
          class="slider-button" 
          :class="{ active: isSliding, success: verifyStatus === 'success', error: verifyStatus === 'error' }"
          :style="{ left: `${sliderWidth}px` }"
          @mousedown="handleMouseDown"
          @touchstart="handleTouchStart"
        >
          <span class="slider-icon">→</span>
        </div>
      </div>
      
      <!-- 刷新按钮 -->
      <div class="refresh-btn" @click="refreshCaptcha" title="刷新验证码">
        <span>⟳</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { getCaptcha, type CaptchaData } from '@/api/system'
import { message } from 'ant-design-vue'

const emit = defineEmits<{
  success: [captchaKey: string, xOffset: number]
  error: []
}>()

// 验证码数据
const captchaData = reactive<CaptchaData>({
  captcha_key: '',
  background: '',
  puzzle: '',
  y: 0
})

// 滑块状态
const sliderWidth = ref(0)
const puzzleLeft = ref(0)
const isSliding = ref(false)
const verifyStatus = ref<'success' | 'error' | null>(null)
const sliderText = ref('向右滑动完成验证')

// 鼠标/触摸起始位置
let startX = 0
const maxSliderWidth = 280 - 50 // 容器宽度 - 滑块宽度

// 加载验证码
const loadCaptcha = async () => {
  try {
    const response = await getCaptcha()
    if (response.data.code === 200) {
      Object.assign(captchaData, response.data.data)
      resetSlider()
    }
  } catch (error) {
    message.error('获取验证码失败')
  }
}

// 刷新验证码
const refreshCaptcha = () => {
  loadCaptcha()
}

// 重置滑块
const resetSlider = () => {
  sliderWidth.value = 0
  puzzleLeft.value = 0
  isSliding.value = false
  verifyStatus.value = null
  sliderText.value = '向右滑动完成验证'
}

// 鼠标按下
const handleMouseDown = (e: MouseEvent) => {
  if (verifyStatus.value) return
  isSliding.value = true
  startX = e.clientX
  
  document.addEventListener('mousemove', handleMouseMove)
  document.addEventListener('mouseup', handleMouseUp)
}

// 触摸开始
const handleTouchStart = (e: TouchEvent) => {
  if (verifyStatus.value) return
  isSliding.value = true
  startX = e.touches[0]?.clientX || 0
  
  document.addEventListener('touchmove', handleTouchMove)
  document.addEventListener('touchend', handleTouchEnd)
}

// 鼠标移动
const handleMouseMove = (e: MouseEvent) => {
  if (!isSliding.value) return
  
  const moveX = e.clientX - startX
  updatePosition(moveX)
}

// 触摸移动
const handleTouchMove = (e: TouchEvent) => {
  if (!isSliding.value) return
  
  const moveX = (e.touches[0]?.clientX || 0) - startX
  updatePosition(moveX)
}

// 更新位置
const updatePosition = (moveX: number) => {
  // 限制滑动范围
  const newWidth = Math.max(0, Math.min(moveX, maxSliderWidth))
  sliderWidth.value = newWidth
  puzzleLeft.value = newWidth
}

// 鼠标释放
const handleMouseUp = () => {
  document.removeEventListener('mousemove', handleMouseMove)
  document.removeEventListener('mouseup', handleMouseUp)
  
  verifySlider()
}

// 触摸结束
const handleTouchEnd = () => {
  document.removeEventListener('touchmove', handleTouchMove)
  document.removeEventListener('touchend', handleTouchEnd)
  
  verifySlider()
}

// 验证滑块位置
const verifySlider = () => {
  if (!isSliding.value) return
  
  isSliding.value = false
  
  // 这里不调用后端验证，而是将数据传给父组件
  // 父组件会在登录时一并验证
  const xOffset = Math.round(puzzleLeft.value)
  
  // 简单的前端视觉反馈（实际验证由后端完成）
  if (xOffset > 30) {
    verifyStatus.value = 'success'
    setTimeout(() => {
      emit('success', captchaData.captcha_key, xOffset)
    }, 300)
  } else {
    verifyStatus.value = 'error'
    setTimeout(() => {
      resetSlider()
      emit('error')
    }, 1000)
  }
}

// 组件挂载时加载验证码
onMounted(() => {
  loadCaptcha()
})

// 组件卸载时清理事件监听
onUnmounted(() => {
  document.removeEventListener('mousemove', handleMouseMove)
  document.removeEventListener('mouseup', handleMouseUp)
  document.removeEventListener('touchmove', handleTouchMove)
  document.removeEventListener('touchend', handleTouchEnd)
})
</script>

<style scoped>
.slide-verify {
  width: 100%;
}

.verify-container {
  position: relative;
  width: 280px;
  margin: 0 auto;
}

.image-container {
  position: relative;
  width: 280px;
  height: 155px;
  border-radius: 8px;
  overflow: hidden;
  background: #f5f5f5;
  margin-bottom: 12px;
}

.bg-image {
  width: 100%;
  height: 100%;
  display: block;
  user-select: none;
  pointer-events: none;
}

.puzzle-image {
  position: absolute;
  width: 50px;
  height: 50px;
  user-select: none;
  pointer-events: none;
  transition: left 0.1s;
}

.slider-track {
  position: relative;
  width: 280px;
  height: 40px;
  background: #f0f0f0;
  border-radius: 20px;
  overflow: hidden;
}

.slider-bar {
  position: absolute;
  left: 0;
  top: 0;
  height: 100%;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
  border-radius: 20px;
  transition: width 0.1s;
}

.slider-text {
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  color: #999;
  font-size: 14px;
  white-space: nowrap;
  user-select: none;
  pointer-events: none;
  z-index: 1;
}

.slider-text.success {
  color: #52c41a;
  font-weight: 500;
}

.slider-text.error {
  color: #ff4d4f;
  font-weight: 500;
}

.slider-button {
  position: absolute;
  left: 0;
  top: 0;
  width: 50px;
  height: 40px;
  background: #fff;
  border-radius: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: left 0.1s;
  z-index: 2;
}

.slider-button:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.slider-button.active {
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.slider-button.success {
  background: #52c41a;
}

.slider-button.error {
  background: #ff4d4f;
}

.slider-icon {
  font-size: 20px;
  color: #667eea;
  user-select: none;
}

.slider-button.success .slider-icon,
.slider-button.error .slider-icon {
  color: #fff;
}

.refresh-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 32px;
  height: 32px;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.refresh-btn:hover {
  background: #fff;
  transform: rotate(180deg);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.refresh-btn span {
  font-size: 18px;
  color: #667eea;
}
</style>
