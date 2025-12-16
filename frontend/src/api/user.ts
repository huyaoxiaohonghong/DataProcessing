/**
 * 用户相关 API
 * User authentication and profile APIs
 */
import apiClient from './client'

export interface LoginParams {
    username: string
    password: string
}

export interface RegisterParams {
    username: string
    email: string
    password: string
    password_confirm: string
    first_name?: string
    last_name?: string
    phone?: string
    department?: string
}

export interface UserInfo {
    id: number
    username: string
    email: string
    first_name: string
    last_name: string
    phone: string | null
    role: string
    role_display: string
    department: string | null
    avatar: string | null
    is_active: boolean
    date_joined: string
    last_login: string | null
    created_at: string
    updated_at: string
}

export interface AuthResponse {
    code: number
    message: string
    data: {
        user: UserInfo
        tokens: {
            access: string
            refresh: string
        }
    }
}

export interface ApiResponse<T = any> {
    code: number
    message: string
    data: T
}

// 用户登录
export const login = (params: LoginParams) => {
    return apiClient.post<AuthResponse>('/users/login/', params)
}

// 用户注册
export const register = (params: RegisterParams) => {
    return apiClient.post<AuthResponse>('/users/register/', params)
}

// 用户登出
export const logout = (refresh: string) => {
    return apiClient.post<ApiResponse>('/users/logout/', { refresh })
}

// 获取当前用户信息
export const getProfile = () => {
    return apiClient.get<ApiResponse<UserInfo>>('/users/profile/')
}

// 更新用户信息
export const updateProfile = (data: Partial<UserInfo>) => {
    return apiClient.put<ApiResponse<UserInfo>>('/users/profile/', data)
}

// 修改密码
export const changePassword = (data: {
    old_password: string
    new_password: string
    new_password_confirm: string
}) => {
    return apiClient.post<ApiResponse>('/users/change-password/', data)
}

// 刷新 Token
export const refreshToken = (refresh: string) => {
    return apiClient.post<{ access: string }>('/users/token/refresh/', { refresh })
}

// ============== 用户管理 (管理员) ==============

export interface UserManage {
    id: number
    username: string
    email: string
    first_name: string
    last_name: string
    phone: string | null
    role: string
    role_display: string
    department: number | null
    department_name: string | null
    is_active: boolean
    created_at: string
    updated_at: string
}

export interface RoleOption {
    value: string
    label: string
}

// 获取用户列表
export const getUsers = (params?: { page?: number; page_size?: number; search?: string; role?: string; department?: number }) => {
    return apiClient.get<any>('/users/manage/', { params })
}

// 获取用户详情
export const getUser = (id: number) => {
    return apiClient.get<any>(`/users/manage/${id}/`)
}

// 创建用户
export const createUser = (data: Partial<UserManage> & { password?: string }) => {
    return apiClient.post<any>('/users/manage/', data)
}

// 更新用户
export const updateUser = (id: number, data: Partial<UserManage> & { password?: string }) => {
    return apiClient.put<any>(`/users/manage/${id}/`, data)
}

// 删除用户
export const deleteUser = (id: number) => {
    return apiClient.delete<any>(`/users/manage/${id}/`)
}

// 获取角色列表
export const getRoles = () => {
    return apiClient.get<any>('/users/manage/roles/')
}
