/**
 * 文件相关 API
 * File management APIs
 */
import apiClient from './client'
import type { ApiResponse, PaginatedResponse } from './types'

export interface FileCategory {
    id: number
    name: string
    description: string | null
    parent: number | null
    children_count: number
    files_count: number
    created_at: string
    updated_at: string
}

export interface FileInfo {
    id: number
    name: string
    original_name: string
    description: string | null
    file: string
    file_size: number
    file_size_display: string
    file_type: string
    mime_type: string
    category: number | null
    category_name: string | null
    tags: string
    status: 'active' | 'archived' | 'deleted'
    status_display: string
    is_public: boolean
    uploaded_by: number | null
    uploaded_by_name: string | null
    department: number | null
    department_name: string | null
    download_count: number
    created_at: string
    updated_at: string
}

export interface FileUploadParams {
    name?: string
    description?: string
    file: File
    category?: number
    department?: number
    tags?: string
    is_public?: boolean
}

export interface FileUpdateParams {
    name?: string
    description?: string
    category?: number | null
    department?: number | null
    tags?: string
    is_public?: boolean
    status?: 'active' | 'archived' | 'deleted'
}

export interface FileStatistics {
    total_files: number
    total_size: number
    total_downloads: number
    type_stats: Record<string, { count: number; size: number }>
}



// 文件分类 API
export const getCategories = () => {
    return apiClient.get<ApiResponse<FileCategory[]>>('/files/categories/')
}

export const createCategory = (data: { name: string; description?: string; parent?: number }) => {
    return apiClient.post<ApiResponse<FileCategory>>('/files/categories/', data)
}

export const updateCategory = (id: number, data: Partial<FileCategory>) => {
    return apiClient.patch<ApiResponse<FileCategory>>(`/files/categories/${id}/`, data)
}

export const deleteCategory = (id: number) => {
    return apiClient.delete<ApiResponse>(`/files/categories/${id}/`)
}

// 文件 API
export const getFiles = (params?: {
    page?: number
    page_size?: number
    search?: string
    category?: number
    file_type?: string
    ordering?: string
}) => {
    return apiClient.get<PaginatedResponse<FileInfo>>('/files/', { params })
}

export const getFile = (id: number) => {
    return apiClient.get<ApiResponse<FileInfo>>(`/files/${id}/`)
}

export const uploadFile = (data: FormData) => {
    return apiClient.post<ApiResponse<FileInfo>>('/files/', data, {
        headers: {
            'Content-Type': 'multipart/form-data',
        },
    })
}

export const updateFile = (id: number, data: FileUpdateParams) => {
    return apiClient.patch<ApiResponse<FileInfo>>(`/files/${id}/`, data)
}

export const deleteFile = (id: number) => {
    return apiClient.delete<ApiResponse>(`/files/${id}/`)
}

export const downloadFile = (id: number) => {
    return apiClient.get(`/files/${id}/download/`, {
        responseType: 'blob',
    })
}

export const getFileStatistics = () => {
    return apiClient.get<ApiResponse<FileStatistics>>('/files/statistics/')
}
