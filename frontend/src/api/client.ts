/**
 * Axios 实例配置
 * API client with token refresh queue to prevent race conditions
 * Token 从 tokenStore 内存模块读取，不再使用 sessionStorage
 */
import axios, { type AxiosInstance, type InternalAxiosRequestConfig, type AxiosResponse } from 'axios'
import { message } from 'ant-design-vue'
import { config } from '@/config/env'
import { accessToken, refreshToken, setTokens, clearTokens } from '@/stores/tokenStore'

const apiClient: AxiosInstance = axios.create({
  baseURL: config.apiBaseUrl ? `${config.apiBaseUrl}${config.apiPrefix}` : config.apiPrefix,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Token 刷新状态管理，防止并发请求重复刷新
let isRefreshing = false
let refreshSubscribers: ((token: string) => void)[] = []

function onTokenRefreshed(token: string) {
  refreshSubscribers.forEach(cb => cb(token))
  refreshSubscribers = []
}

function addRefreshSubscriber(cb: (token: string) => void) {
  refreshSubscribers.push(cb)
}

// 请求拦截器
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = accessToken.value
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器
apiClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error) => {
    // 网络超时或无响应
    if (error.code === 'ECONNABORTED' || !error.response) {
      message.error('网络连接超时，请检查网络后重试')
      return Promise.reject(error)
    }

    const status = error.response?.status

    // 错误分类提示
    switch (status) {
      case 403:
        message.error('权限不足，请联系管理员')
        break
      case 500:
        message.error('服务器异常，请稍后重试')
        break
    }

    const originalRequest = error.config

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      const refreshTokenValue = refreshToken.value
      if (!refreshTokenValue) {
        clearTokens()
        window.location.href = '/login'
        return Promise.reject(error)
      }

      // 如果已经在刷新，排队等待
      if (isRefreshing) {
        return new Promise((resolve) => {
          addRefreshSubscriber((newToken: string) => {
            originalRequest.headers.Authorization = `Bearer ${newToken}`
            resolve(apiClient(originalRequest))
          })
        })
      }

      isRefreshing = true

      try {
        const response = await axios.post(
          `${apiClient.defaults.baseURL}/users/token/refresh/`,
          { refresh: refreshTokenValue }
        )
        const { access } = response.data
        setTokens(access, refreshTokenValue)
        originalRequest.headers.Authorization = `Bearer ${access}`

        // 通知所有排队的请求
        onTokenRefreshed(access)

        return apiClient(originalRequest)
      } catch (refreshError) {
        clearTokens()
        refreshSubscribers = []
        window.location.href = '/login'
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    return Promise.reject(error)
  }
)

export default apiClient
