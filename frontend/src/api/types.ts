/**
 * Shared API Types
 */

export interface ApiResponse<T = any> {
    code: number
    message: string
    data: T
}

export interface PaginationInfo {
    total: number
    page: number
    page_size: number
    total_pages: number
}

export interface PaginatedResponse<T = any> {
    code: number
    message: string
    data: {
        results: T[]
        pagination: PaginationInfo
    }
}
