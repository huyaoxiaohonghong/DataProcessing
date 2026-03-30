/**
 * Axios 实例配置
 * API client with token refresh queue to prevent race conditions
 */
import axios, { type AxiosInstance, type InternalAxiosRequestConfig, type AxiosResponse } from 'axios'
import { config } from '@/config/env'

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
    const token = sessionStorage.getItem('access_token')
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
    const originalRequest = error.config

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      const refreshToken = sessionStorage.getItem('refresh_token')
      if (!refreshToken) {
        sessionStorage.removeItem('access_token')
        sessionStorage.removeItem('refresh_token')
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
          { refresh: refreshToken }
        )
        const { access } = response.data
        sessionStorage.setItem('access_token', access)
        originalRequest.headers.Authorization = `Bearer ${access}`

        // 通知所有排队的请求
        onTokenRefreshed(access)

        return apiClient(originalRequest)
      } catch (refreshError) {
        sessionStorage.removeItem('access_token')
        sessionStorage.removeItem('refresh_token')
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
