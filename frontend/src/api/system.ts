/**
 * 系统相关 API
 * System management APIs (Logs)
 */
import apiClient from './client'
import { type PaginatedResponse } from './types'

export interface LoginLog {
    id: number
    username: string
    ip: string | null
    user_agent: string | null
    status: boolean
    message: string | null
    created_at: string
}

export interface OperationLog {
    id: number
    username: string
    module: string | null
    action: string | null
    method: string | null
    path: string | null
    params: string | null
    ip: string | null
    user_agent: string | null
    response_code: number | null
    response_time: number
    created_at: string
}

export const getLoginLogs = (params?: { page?: number; page_size?: number; search?: string }) => {
    return apiClient.get<PaginatedResponse<LoginLog>>('/system/login-logs/', { params })
}

export const getOperationLogs = (params?: { page?: number; page_size?: number; search?: string }) => {
    return apiClient.get<PaginatedResponse<OperationLog>>('/system/operation-logs/', { params })
}

// ============== 滑动验证码 ==============

export interface CaptchaData {
    captcha_key: string
    background: string  // Base64 图片
    puzzle: string      // Base64 图片
    y: number          // 拼图 Y 坐标
}

export const getCaptcha = (fingerprint?: string) => {
    return apiClient.get<{ code: number; message: string; data: CaptchaData }>('/system/captcha/', {
        params: fingerprint ? { fingerprint } : undefined
    })
}

// ============== 部门管理 ==============

export interface Department {
    id: number
    name: string
    code: string
    parent: number | null
    parent_name: string | null
    leader: string | null
    phone: string | null
    email: string | null
    sort: number
    status: boolean
    remark: string | null
    created_at: string
    updated_at: string
    children?: Department[]
}

export interface DepartmentSimple {
    id: number
    name: string
    code: string
}

export const getDepartments = (params?: { page?: number; page_size?: number; search?: string; tree?: string }) => {
    return apiClient.get<any>('/system/departments/', { params })
}

export const getDepartmentTree = () => {
    return apiClient.get<any>('/system/departments/', { params: { tree: 'true' } })
}

export const getDepartmentSimple = () => {
    return apiClient.get<any>('/system/departments/simple/')
}

export const createDepartment = (data: Partial<Department>) => {
    return apiClient.post<any>('/system/departments/', data)
}

export const updateDepartment = (id: number, data: Partial<Department>) => {
    return apiClient.put<any>(`/system/departments/${id}/`, data)
}

export const deleteDepartment = (id: number) => {
    return apiClient.delete<any>(`/system/departments/${id}/`)
}

// ============== 菜单管理 ==============

export interface Menu {
    id: number
    name: string
    parent: number | null
    parent_name: string | null
    path: string | null
    component: string | null
    icon: string | null
    menu_type: string
    menu_type_display: string
    permission: string | null
    sort: number
    status: boolean
    visible: boolean
    cache: boolean
    remark: string | null
    created_at: string
    updated_at: string
    children?: Menu[]
}

export interface MenuType {
    value: string
    label: string
}

export const getMenus = (params?: { tree?: string; search?: string }) => {
    return apiClient.get<any>('/system/menus/', { params })
}

export const getMenuTree = () => {
    return apiClient.get<any>('/system/menus/', { params: { tree: 'true' } })
}

export const getMenuSimple = () => {
    return apiClient.get<any>('/system/menus/simple/')
}

export const getMenuTypes = () => {
    return apiClient.get<any>('/system/menus/types/')
}

export const createMenu = (data: Partial<Menu>) => {
    return apiClient.post<any>('/system/menus/', data)
}

export const updateMenu = (id: number, data: Partial<Menu>) => {
    return apiClient.put<any>(`/system/menus/${id}/`, data)
}

export const deleteMenu = (id: number) => {
    return apiClient.delete<any>(`/system/menus/${id}/`)
}

// ============== 角色权限管理 ==============

export interface RolePermission {
    id: number
    role: string
    menu: number
    menu_name: string
    data_scope: string
    data_scope_display: string
    department_ids: number[]
    created_at: string
}

export interface DataScope {
    value: string
    label: string
}

export const getPermissions = (params?: { role?: string }) => {
    return apiClient.get<any>('/system/permissions/', { params })
}

export const getDataScopes = () => {
    return apiClient.get<any>('/system/permissions/scopes/')
}

export const createPermission = (data: Partial<RolePermission>) => {
    return apiClient.post<any>('/system/permissions/', data)
}

export const deletePermission = (id: number) => {
    return apiClient.delete<any>(`/system/permissions/${id}/`)
}

export const batchSetPermissions = (role: string, menu_ids: number[]) => {
    return apiClient.post<any>('/system/permissions/batch/', { role, menu_ids })
}
