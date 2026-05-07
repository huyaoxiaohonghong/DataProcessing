<template>
  <div class="slide-verify" :class="{ 'is-loading': loading }">
    <!-- 图片区 -->
    <div class="image-container" :class="{ shake: verifyStatus === 'error' }">
      <!-- 骨架屏 -->
      <div v-if="loading" class="skeleton">
        <div class="skeleton-shimmer" />
      </div>

      <template v-else>
        <img :src="captchaData.background" alt="背景" class="bg-image" draggable="false" />
        <img
          :src="captchaData.puzzle"
          alt="拼图"
          class="puzzle-image"
          :class="{ 'is-sliding': isSliding }"
          :style="puzzleStyle"
          draggable="false"
        />
        <!-- 拼图落位时的高光 -->
        <div v-if="verifyStatus === 'success'" class="success-flash" />
      </template>

      <!-- 刷新按钮 -->
      <button
        type="button"
        class="refresh-btn"
        :class="{ disabled: refreshDisabled || loading }"
        :disabled="refreshDisabled || loading"
        :title="refreshDisabled ? '请稍后再试' : '刷新验证码'"
        @click="refreshCaptcha"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="23 4 23 10 17 10"></polyline>
          <polyline points="1 20 1 14 7 14"></polyline>
          <path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"></path>
        </svg>
      </button>
    </div>

    <!-- 滑块轨道 -->
    <div class="slider-track" :class="{ 'is-sliding': isSliding, success: verifyStatus === 'success', error: verifyStatus === 'error' }">
      <div class="slider-bar" :style="{ width: `${sliderWidth + 25}px` }" />

      <div class="slider-hint">
        <transition name="fade-swap" mode="out-in">
          <span v-if="verifyStatus === 'success'" key="ok" class="hint success">验证通过</span>
          <span v-else-if="verifyStatus === 'error'" key="err" class="hint error">验证失败，请重试</span>
          <span v-else-if="!isSliding" key="idle" class="hint shine">向右滑动完成拼图</span>
          <span v-else key="sliding" class="hint sliding">松开鼠标以校验</span>
        </transition>
      </div>

      <div
        class="slider-handle"
        :class="{ active: isSliding, success: verifyStatus === 'success', error: verifyStatus === 'error' }"
        :style="{ transform: `translate3d(${sliderWidth}px, 0, 0)` }"
        @pointerdown="handlePointerDown"
      >
        <transition name="icon-swap" mode="out-in">
          <svg v-if="verifyStatus === 'success'" key="ok" class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="20 6 9 17 4 12"></polyline>
          </svg>
          <svg v-else-if="verifyStatus === 'error'" key="err" class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
          <svg v-else key="arrow" class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="9 6 15 12 9 18"></polyline>
          </svg>
        </transition>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import { getCaptcha, type CaptchaData } from '@/api/system'

// ========================= Types =========================
interface TrackPoint { x: number; y: number; t: number }

const emit = defineEmits<{
  success: [data: { captchaKey: string; xOffset: number; trajectory: string; duration: number; fingerprint: string }]
  error: []
}>()

// ========================= State =========================
const captchaData = reactive<CaptchaData>({ captcha_key: '', background: '', puzzle: '', y: 0 })
const loading = ref(true)
const refreshDisabled = ref(false)

const CONTAINER_WIDTH = 280
const HANDLE_WIDTH = 46
const MAX_SLIDE = CONTAINER_WIDTH - HANDLE_WIDTH

const sliderWidth = ref(0)
const isSliding = ref(false)
const verifyStatus = ref<'success' | 'error' | null>(null)

const puzzleStyle = computed(() => ({
  transform: `translate3d(${sliderWidth.value}px, ${captchaData.y}px, 0)`,
}))

// ========================= Fingerprint =========================
const fingerprint = ref('')

// FNV-1a 32-bit 哈希: 当 crypto.subtle 不可用 (非 HTTPS 场景) 时的降级方案
function fnv1a32(str: string): string {
  let h = 0x811c9dc5
  for (let i = 0; i < str.length; i++) {
    h ^= str.charCodeAt(i)
    h = Math.imul(h, 0x01000193)
  }
  return (h >>> 0).toString(16).padStart(8, '0')
}

async function sha256Hex(str: string): Promise<string> {
  const subtle = globalThis.crypto?.subtle
  if (!subtle) {
    // 非 secure context (HTTP / IP 直连): 拼接多轮 FNV-1a 作为弱指纹
    return fnv1a32(str) + fnv1a32(str + '|salt1') + fnv1a32(str + '|salt2') + fnv1a32(str + '|salt3')
  }
  const buf = await subtle.digest('SHA-256', new TextEncoder().encode(str))
  return Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2, '0')).join('')
}

async function generateFingerprint(): Promise<string> {
  // 增强指纹：加入 language / platform / hardwareConcurrency / colorDepth / canvas 特征
  const canvasSig = (() => {
    try {
      const c = document.createElement('canvas')
      c.width = 100; c.height = 40
      const ctx = c.getContext('2d')
      if (!ctx) return ''
      ctx.textBaseline = 'top'
      ctx.font = '14px "Arial"'
      ctx.fillStyle = '#f60'
      ctx.fillRect(0, 0, 100, 40)
      ctx.fillStyle = '#069'
      ctx.fillText('fp-canvas-🔒', 2, 2)
      return c.toDataURL().slice(-64)
    } catch {
      return ''
    }
  })()

  const raw = JSON.stringify({
    ua: navigator.userAgent,
    lang: navigator.language,
    platform: (navigator as any).platform || '',
    hc: (navigator as any).hardwareConcurrency || 0,
    res: `${screen.width}x${screen.height}`,
    depth: screen.colorDepth,
    tz: new Date().getTimezoneOffset(),
    canvas: canvasSig,
  })
  try {
    return await sha256Hex(raw)
  } catch {
    // 最终兜底：任何异常都不阻塞验证码加载
    return fnv1a32(raw)
  }
}

// ========================= Trajectory =========================
// 使用 rAF 节流 + 小幅度抖动过滤，降低轨迹体积 & 提升滑动流畅度
const trackPoints: TrackPoint[] = []
let slideStartTime = 0
let rafId: number | null = null
let pendingMove: { clientX: number; clientY: number } | null = null

function recordTrack(x: number, y: number) {
  const t = Date.now() - slideStartTime
  const last = trackPoints[trackPoints.length - 1]
  // 去重：距离过近的采样点合并，保持轨迹的真实波动
  if (last && Math.abs(last.x - x) < 1 && Math.abs(last.y - y) < 1 && t - last.t < 30) return
  trackPoints.push({ x: Math.round(x), y: Math.round(y), t })
}

// ========================= Pointer Handlers =========================
let startX = 0
let startY = 0
let activePointerId: number | null = null

function handlePointerDown(e: PointerEvent) {
  if (verifyStatus.value || loading.value) return
  activePointerId = e.pointerId
  ;(e.currentTarget as HTMLElement).setPointerCapture?.(e.pointerId)

  isSliding.value = true
  startX = e.clientX
  startY = e.clientY
  slideStartTime = Date.now()
  trackPoints.length = 0

  window.addEventListener('pointermove', handlePointerMove, { passive: false })
  window.addEventListener('pointerup', handlePointerUp)
  window.addEventListener('pointercancel', handlePointerUp)
  e.preventDefault()
}

function handlePointerMove(e: PointerEvent) {
  if (!isSliding.value || e.pointerId !== activePointerId) return
  e.preventDefault()
  pendingMove = { clientX: e.clientX, clientY: e.clientY }
  if (rafId === null) {
    rafId = requestAnimationFrame(flushMove)
  }
}

function flushMove() {
  rafId = null
  if (!pendingMove) return
  const dx = pendingMove.clientX - startX
  const dy = pendingMove.clientY - startY
  sliderWidth.value = clamp(dx, 0, MAX_SLIDE)
  recordTrack(dx, dy)
  pendingMove = null
}

function handlePointerUp(e: PointerEvent) {
  if (e.pointerId !== activePointerId) return
  activePointerId = null
  window.removeEventListener('pointermove', handlePointerMove)
  window.removeEventListener('pointerup', handlePointerUp)
  window.removeEventListener('pointercancel', handlePointerUp)

  if (rafId !== null) {
    cancelAnimationFrame(rafId)
    rafId = null
    flushMove()
  }
  finishVerify()
}

function clamp(v: number, lo: number, hi: number) { return v < lo ? lo : v > hi ? hi : v }

// ========================= Finish =========================
function finishVerify() {
  if (!isSliding.value) return
  isSliding.value = false

  // 直接提交到后端，由后端判断位置与轨迹
  const xOffset = Math.round(sliderWidth.value)
  const duration = Date.now() - slideStartTime

  // 以 UTF-8 安全的 Base64 编码轨迹
  const jsonStr = JSON.stringify(trackPoints)
  const trajectory = btoa(unescape(encodeURIComponent(jsonStr)))

  // 乐观 UI：先显示 success 态（真正的结果由后端登录接口统一反馈）
  verifyStatus.value = 'success'
  setTimeout(() => {
    emit('success', {
      captchaKey: captchaData.captcha_key,
      xOffset,
      trajectory,
      duration,
      fingerprint: fingerprint.value,
    })
  }, 360)
}

// 外部可在登录失败时调用此方法展示错误态并重置
function showError() {
  verifyStatus.value = 'error'
  emit('error')
  setTimeout(() => {
    resetSlider()
    loadCaptcha()
  }, 800)
}
defineExpose({ showError })

// ========================= Captcha IO =========================
async function loadCaptcha() {
  loading.value = true
  try {
    const response = await getCaptcha(fingerprint.value)
    if (response.data.code === 200) {
      Object.assign(captchaData, response.data.data)
      resetSlider()
    }
  } catch (error: any) {
    if (error?.response?.status === 429) {
      message.warning('请求过于频繁，请稍后再试')
      refreshDisabled.value = true
      setTimeout(() => (refreshDisabled.value = false), 60_000)
    } else {
      message.error('获取验证码失败')
    }
  } finally {
    loading.value = false
  }
}

function refreshCaptcha() {
  if (refreshDisabled.value || loading.value) return
  loadCaptcha()
}

function resetSlider() {
  sliderWidth.value = 0
  isSliding.value = false
  verifyStatus.value = null
  trackPoints.length = 0
  slideStartTime = 0
}

// ========================= Lifecycle =========================
onMounted(async () => {
  try {
    fingerprint.value = await generateFingerprint()
  } catch {
    fingerprint.value = ''
  }
  await loadCaptcha()
})

onUnmounted(() => {
  window.removeEventListener('pointermove', handlePointerMove)
  window.removeEventListener('pointerup', handlePointerUp)
  window.removeEventListener('pointercancel', handlePointerUp)
  if (rafId !== null) cancelAnimationFrame(rafId)
})
</script>

<style scoped>
/* ================= Container ================= */
.slide-verify {
  width: 280px;
  margin: 0 auto;
  user-select: none;
  -webkit-user-select: none;
  font-family: 'Fira Sans', system-ui, -apple-system, sans-serif;
}

/* ================= Image area ================= */
.image-container {
  position: relative;
  width: 280px;
  height: 155px;
  border-radius: 12px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
  margin-bottom: 14px;
}

.image-container.shake { animation: shake 0.45s cubic-bezier(0.36, 0.07, 0.19, 0.97); }

.bg-image {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  display: block;
  user-select: none;
  -webkit-user-drag: none;
}

.puzzle-image {
  position: absolute;
  top: 0; left: 0;
  width: 50px; height: 50px;
  user-select: none;
  -webkit-user-drag: none;
  filter: drop-shadow(0 2px 6px rgba(0, 0, 0, 0.35));
  will-change: transform;
  transform: translate3d(0, 0, 0);
  transition: filter 0.2s ease;
}
.puzzle-image.is-sliding { filter: drop-shadow(0 4px 10px rgba(99, 102, 241, 0.55)); }

/* Success light flash */
.success-flash {
  position: absolute; inset: 0;
  background: radial-gradient(circle at center, rgba(16, 185, 129, 0.25), transparent 65%);
  pointer-events: none;
  animation: flash 0.5s ease-out;
}

/* ================= Skeleton ================= */
.skeleton {
  position: absolute; inset: 0;
  background: linear-gradient(90deg, rgba(255,255,255,0.04) 0%, rgba(255,255,255,0.08) 50%, rgba(255,255,255,0.04) 100%);
  overflow: hidden;
}
.skeleton-shimmer {
  position: absolute; inset: 0;
  background: linear-gradient(100deg, transparent 0%, rgba(255,255,255,0.12) 50%, transparent 100%);
  transform: translateX(-100%);
  animation: shimmer 1.4s linear infinite;
}

/* ================= Refresh ================= */
.refresh-btn {
  position: absolute;
  top: 8px; right: 8px;
  width: 30px; height: 30px;
  display: inline-flex; align-items: center; justify-content: center;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 50%;
  background: rgba(15, 15, 20, 0.55);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  color: #c7d2fe;
  cursor: pointer;
  transition: transform 0.4s cubic-bezier(0.4, 0, 0.2, 1), background 0.2s ease, color 0.2s ease;
  padding: 0;
}
.refresh-btn svg { width: 16px; height: 16px; }
.refresh-btn:hover:not(.disabled) {
  transform: rotate(180deg);
  background: rgba(99, 102, 241, 0.25);
  color: #fff;
}
.refresh-btn.disabled { opacity: 0.45; cursor: not-allowed; }

/* ================= Slider track ================= */
.slider-track {
  position: relative;
  width: 280px;
  height: 42px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 21px;
  overflow: hidden;
  transition: border-color 0.3s ease, background 0.3s ease;
}
.slider-track.is-sliding { border-color: rgba(99, 102, 241, 0.4); }
.slider-track.success { border-color: rgba(16, 185, 129, 0.5); background: rgba(16, 185, 129, 0.06); }
.slider-track.error   { border-color: rgba(239, 68, 68, 0.5);  background: rgba(239, 68, 68, 0.06); }

.slider-bar {
  position: absolute;
  left: 0; top: 0; bottom: 0;
  background: linear-gradient(90deg, rgba(99, 102, 241, 0.35) 0%, rgba(139, 92, 246, 0.45) 100%);
  border-radius: 21px;
  transition: background 0.3s ease;
  will-change: width;
}
.slider-track.success .slider-bar { background: linear-gradient(90deg, rgba(16, 185, 129, 0.35), rgba(16, 185, 129, 0.55)); }
.slider-track.error   .slider-bar { background: linear-gradient(90deg, rgba(239, 68, 68, 0.35),  rgba(239, 68, 68, 0.55)); }

.slider-hint {
  position: absolute; inset: 0;
  display: flex; align-items: center; justify-content: center;
  font-size: 13px;
  pointer-events: none;
  letter-spacing: 0.02em;
}
.hint { color: #94A3B8; }
.hint.shine {
  background: linear-gradient(90deg, #475569 0%, #F1F5F9 50%, #475569 100%);
  background-size: 200% auto;
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  animation: text-shine 2.4s linear infinite;
}
.hint.sliding { color: #C7D2FE; }
.hint.success { color: #10B981; font-weight: 500; }
.hint.error   { color: #EF4444; font-weight: 500; }

/* ================= Slider handle ================= */
.slider-handle {
  position: absolute;
  left: 0; top: 0;
  width: 46px; height: 42px;
  display: flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
  border-radius: 21px;
  cursor: grab;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.35);
  color: #fff;
  will-change: transform;
  transition: box-shadow 0.2s ease, background 0.3s ease, transform 0s;
  touch-action: none;
}
.slider-handle:hover { box-shadow: 0 6px 16px rgba(99, 102, 241, 0.5); }
.slider-handle.active { cursor: grabbing; box-shadow: 0 6px 20px rgba(99, 102, 241, 0.65); }
.slider-handle.success {
  background: linear-gradient(135deg, #10B981 0%, #059669 100%);
  box-shadow: 0 6px 16px rgba(16, 185, 129, 0.5);
}
.slider-handle.error {
  background: linear-gradient(135deg, #EF4444 0%, #DC2626 100%);
  box-shadow: 0 6px 16px rgba(239, 68, 68, 0.5);
}
.slider-handle .icon { width: 20px; height: 20px; }

/* ================= Transitions ================= */
.fade-swap-enter-active, .fade-swap-leave-active { transition: opacity 0.2s ease, transform 0.2s ease; }
.fade-swap-enter-from { opacity: 0; transform: translateY(4px); }
.fade-swap-leave-to   { opacity: 0; transform: translateY(-4px); }

.icon-swap-enter-active, .icon-swap-leave-active { transition: opacity 0.18s ease, transform 0.18s ease; }
.icon-swap-enter-from { opacity: 0; transform: scale(0.6); }
.icon-swap-leave-to   { opacity: 0; transform: scale(0.6); }

/* ================= Keyframes ================= */
@keyframes shake {
  10%, 90% { transform: translate3d(-1px, 0, 0); }
  20%, 80% { transform: translate3d(2px, 0, 0); }
  30%, 50%, 70% { transform: translate3d(-4px, 0, 0); }
  40%, 60% { transform: translate3d(4px, 0, 0); }
}
@keyframes flash   { 0% { opacity: 0; } 30% { opacity: 1; } 100% { opacity: 0; } }
@keyframes shimmer { 100% { transform: translateX(100%); } }
@keyframes text-shine { 0% { background-position: 200% center; } 100% { background-position: -200% center; } }
</style>
