/**
 * 用户状态管理
 * Pinia store for user authentication state
 * Token 存储在内存中（通过 tokenStore 模块），页面刷新后需重新登录
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login, logout, getProfile, type UserInfo, type LoginParams } from '@/api/user'
import router from '@/router'
import {
    accessToken,
    refreshToken,
    setTokens as setTokensInternal,
    clearTokens,
} from './tokenStore'

export const useUserStore = defineStore('user', () => {
    // State - Token 通过 tokenStore 模块存储在内存中
    const userInfo = ref<UserInfo | null>(null)

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

            // 保存 token 到内存
            setTokensInternal(data.tokens.access, data.tokens.refresh)

            // 保存用户信息
            userInfo.value = data.user

            return { success: true, message: '登录成功' }
        } catch (error: any) {
            return {
                success: false,
                message: error.response?.data?.message || '登录失败',
                status: error.response?.status || 0
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
            // 清除内存中的状态
            userInfo.value = null
            clearTokens()

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
        setTokensInternal(access, refresh)
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
