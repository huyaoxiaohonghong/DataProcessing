/**
 * Axios 实例配置
 * API client configuration with interceptors
 * 使用 sessionStorage 支持同一浏览器多标签页独立登录
 */
import axios, { type AxiosInstance, type InternalAxiosRequestConfig, type AxiosResponse } from 'axios'
import { config } from '@/config/env'

// 创建 axios 实例
const apiClient: AxiosInstance = axios.create({
  baseURL: config.apiBaseUrl ? `${config.apiBaseUrl}${config.apiPrefix}` : config.apiPrefix,
  timeout: 30000,  // 增加超时时间支持大文件
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器 - 添加 Token
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // 使用 sessionStorage，每个标签页独立
    const token = sessionStorage.getItem('access_token')
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器 - 处理 Token 过期
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    return response
  },
  async (error) => {
    const originalRequest = error.config

    // Token 过期，尝试刷新
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      const refreshToken = sessionStorage.getItem('refresh_token')
      if (refreshToken) {
        try {
          const response = await axios.post(
            `${apiClient.defaults.baseURL}/users/token/refresh/`,
            { refresh: refreshToken }
          )
          const { access } = response.data
          sessionStorage.setItem('access_token', access)
          originalRequest.headers.Authorization = `Bearer ${access}`
          return apiClient(originalRequest)
        } catch (refreshError) {
          // 刷新失败，清除 token 并跳转登录
          sessionStorage.removeItem('access_token')
          sessionStorage.removeItem('refresh_token')
          window.location.href = '/login'
          return Promise.reject(refreshError)
        }
      }
    }

    return Promise.reject(error)
  }
)

export default apiClient

