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
      <div
        class="refresh-btn"
        :class="{ disabled: refreshDisabled }"
        @click="refreshCaptcha"
        :title="refreshDisabled ? '请稍后再试' : '刷新验证码'"
      >
        <span>⟳</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { getCaptcha, type CaptchaData } from '@/api/system'
import { message } from 'ant-design-vue'

// --- Task 6.3: Updated emit interface ---
const emit = defineEmits<{
  success: [data: { captchaKey: string; xOffset: number; trajectory: string; duration: number; fingerprint: string }]
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
let startY = 0
const maxSliderWidth = 280 - 50 // 容器宽度 - 滑块宽度

// --- Task 6.1: Client fingerprint ---
const fingerprint = ref('')

async function generateFingerprint(): Promise<string> {
  const data = {
    userAgent: navigator.userAgent,
    screenResolution: `${screen.width}x${screen.height}`,
    timezoneOffset: new Date().getTimezoneOffset()
  }
  const raw = JSON.stringify(data)
  const encoder = new TextEncoder()
  const hashBuffer = await crypto.subtle.digest('SHA-256', encoder.encode(raw))
  const hashArray = Array.from(new Uint8Array(hashBuffer))
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('')
}

// --- Task 6.2: Trajectory tracking ---
interface TrackPoint {
  x: number
  y: number
  t: number
}

const trackPoints = ref<TrackPoint[]>([])
let slideStartTime = 0
let lastTrackTime = 0

// --- Task 6.4: 429 handling ---
const refreshDisabled = ref(false)
let refreshTimer: ReturnType<typeof setTimeout> | null = null

// 加载验证码
const loadCaptcha = async () => {
  try {
    // Task 6.1: pass fingerprint as query parameter
    const response = await getCaptcha(fingerprint.value)
    if (response.data.code === 200) {
      Object.assign(captchaData, response.data.data)
      resetSlider()
    }
  } catch (error: any) {
    // Task 6.4: Handle 429 status code
    if (error?.response?.status === 429) {
      message.warning('请求过于频繁，请稍后再试')
      refreshDisabled.value = true
      refreshTimer = setTimeout(() => {
        refreshDisabled.value = false
      }, 60000)
    } else {
      message.error('获取验证码失败')
    }
  }
}

// 刷新验证码
const refreshCaptcha = () => {
  if (refreshDisabled.value) return
  loadCaptcha()
}

// 重置滑块
const resetSlider = () => {
  sliderWidth.value = 0
  puzzleLeft.value = 0
  isSliding.value = false
  verifyStatus.value = null
  sliderText.value = '向右滑动完成验证'
  trackPoints.value = []
  slideStartTime = 0
  lastTrackTime = 0
}

// 鼠标按下
const handleMouseDown = (e: MouseEvent) => {
  if (verifyStatus.value) return
  isSliding.value = true
  startX = e.clientX
  startY = e.clientY

  // Task 6.2: Record start time and reset track
  slideStartTime = Date.now()
  lastTrackTime = 0
  trackPoints.value = []

  document.addEventListener('mousemove', handleMouseMove)
  document.addEventListener('mouseup', handleMouseUp)
}

// 触摸开始
const handleTouchStart = (e: TouchEvent) => {
  if (verifyStatus.value) return
  isSliding.value = true
  startX = e.touches[0]?.clientX || 0
  startY = e.touches[0]?.clientY || 0

  // Task 6.2: Record start time and reset track
  slideStartTime = Date.now()
  lastTrackTime = 0
  trackPoints.value = []

  document.addEventListener('touchmove', handleTouchMove)
  document.addEventListener('touchend', handleTouchEnd)
}

// 鼠标移动
const handleMouseMove = (e: MouseEvent) => {
  if (!isSliding.value) return

  const moveX = e.clientX - startX
  updatePosition(moveX)

  // Task 6.2: Record track point with ≤50ms throttle
  recordTrackPoint(e.clientX - startX, e.clientY - startY)
}

// 触摸移动
const handleTouchMove = (e: TouchEvent) => {
  if (!isSliding.value) return

  const touch = e.touches[0]
  const moveX = (touch?.clientX || 0) - startX
  updatePosition(moveX)

  // Task 6.2: Record track point with ≤50ms throttle
  recordTrackPoint((touch?.clientX || 0) - startX, (touch?.clientY || 0) - startY)
}

// Task 6.2: Record a track point with ≤50ms interval throttle
function recordTrackPoint(x: number, y: number) {
  const now = Date.now()
  const t = now - slideStartTime
  if (t - lastTrackTime >= 50 || trackPoints.value.length === 0) {
    trackPoints.value.push({ x: Math.round(x), y: Math.round(y), t })
    lastTrackTime = t
  }
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

  const xOffset = Math.round(puzzleLeft.value)

  // Task 6.2: Calculate total slide duration
  const duration = Date.now() - slideStartTime

  // Task 6.3: Base64 encode trajectory data
  const trajectory = btoa(JSON.stringify(trackPoints.value))

  // Task 6.3: Always emit success — no client-side xOffset > 30 filtering
  // All validation is delegated to the backend
  verifyStatus.value = 'success'
  setTimeout(() => {
    emit('success', {
      captchaKey: captchaData.captcha_key,
      xOffset,
      trajectory,
      duration,
      fingerprint: fingerprint.value
    })
  }, 300)
}

// 组件挂载时加载验证码和生成指纹
onMounted(async () => {
  // Task 6.1: Generate fingerprint on mount
  fingerprint.value = await generateFingerprint()
  loadCaptcha()
})

// 组件卸载时清理事件监听和定时器
onUnmounted(() => {
  document.removeEventListener('mousemove', handleMouseMove)
  document.removeEventListener('mouseup', handleMouseUp)
  document.removeEventListener('touchmove', handleTouchMove)
  document.removeEventListener('touchend', handleTouchEnd)
  if (refreshTimer) {
    clearTimeout(refreshTimer)
    refreshTimer = null
  }
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

.refresh-btn.disabled {
  opacity: 0.5;
  cursor: not-allowed;
  pointer-events: none;
}

.refresh-btn span {
  font-size: 18px;
  color: #667eea;
}
</style>
