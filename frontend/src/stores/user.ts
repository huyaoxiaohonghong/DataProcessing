/**
 * 用户状态管理
 * Pinia store for user authentication state
 * 使用 sessionStorage 支持同一浏览器多标签页独立登录
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login, logout, getProfile, type UserInfo, type LoginParams } from '@/api/user'
import router from '@/router'

export const useUserStore = defineStore('user', () => {
    // State - 使用 sessionStorage 支持多标签页独立登录
    const userInfo = ref<UserInfo | null>(null)
    const accessToken = ref<string | null>(sessionStorage.getItem('access_token'))
    const refreshToken = ref<string | null>(sessionStorage.getItem('refresh_token'))

    // Getters
    const isLoggedIn = computed(() => !!accessToken.value)
    const username = computed(() => userInfo.value?.username || '')
    const role = computed(() => userInfo.value?.role || '')
    const isSuperAdmin = computed(() => userInfo.value?.role === 'super_admin')
    const isAdmin = computed(() => ['super_admin', 'admin'].includes(userInfo.value?.role || ''))

    // Actions
    async function loginAction(params: LoginParams) {
        try {
            const response = await login(params)
            const { data } = response.data

            // 保存 token 到 sessionStorage（每个标签页独立）
            accessToken.value = data.tokens.access
            refreshToken.value = data.tokens.refresh
            sessionStorage.setItem('access_token', data.tokens.access)
            sessionStorage.setItem('refresh_token', data.tokens.refresh)

            // 保存用户信息
            userInfo.value = data.user

            return { success: true, message: '登录成功' }
        } catch (error: any) {
            return {
                success: false,
                message: error.response?.data?.message || '登录失败'
            }
        }
    }

    async function logoutAction() {
        try {
            if (refreshToken.value) {
                await logout(refreshToken.value)
            }
        } catch (error) {
            console.error('Logout error:', error)
        } finally {
            // 清除状态
            userInfo.value = null
            accessToken.value = null
            refreshToken.value = null
            sessionStorage.removeItem('access_token')
            sessionStorage.removeItem('refresh_token')

            // 跳转登录页
            router.push('/login')
        }
    }

    async function fetchUserInfo() {
        try {
            const response = await getProfile()
            userInfo.value = response.data.data
            return true
        } catch (error) {
            console.error('Fetch user info error:', error)
            return false
        }
    }

    function setTokens(access: string, refresh: string) {
        accessToken.value = access
        refreshToken.value = refresh
        sessionStorage.setItem('access_token', access)
        sessionStorage.setItem('refresh_token', refresh)
    }

    // 初始化时尝试恢复用户信息
    async function initializeAuth() {
        if (accessToken.value && !userInfo.value) {
            await fetchUserInfo()
        }
    }

    return {
        // State
        userInfo,
        accessToken,
        refreshToken,
        // Getters
        isLoggedIn,
        username,
        role,
        isSuperAdmin,
        isAdmin,
        // Actions
        loginAction,
        logoutAction,
        fetchUserInfo,
        setTokens,
        initializeAuth,
    }
})

