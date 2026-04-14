/**
 * Token 内存存储
 * 独立模块，避免 api/client.ts 与 stores/user.ts 之间的循环依赖
 * Token 仅存储在内存中，页面刷新后丢失（安全设计）
 */
import { ref } from 'vue'

export const accessToken = ref<string | null>(null)
export const refreshToken = ref<string | null>(null)

export function setTokens(access: string, refresh: string) {
  accessToken.value = access
  refreshToken.value = refresh
}

export function clearTokens() {
  accessToken.value = null
  refreshToken.value = null
}
