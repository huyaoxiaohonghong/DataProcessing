/**
 * 环境配置工具
 * 统一管理和导出环境变量
 */

// 当前环境
export const ENV = import.meta.env.MODE

// 是否为开发环境
export const isDev = ENV === 'development'

// 是否为生产环境
export const isProd = ENV === 'production'

// 环境配置
export const config = {
    // 应用标题
    appTitle: import.meta.env.VITE_APP_TITLE || '数据处理系统',

    // 应用版本
    appVersion: import.meta.env.VITE_APP_VERSION || '1.0.0',

    // API 基础路径
    apiBaseUrl: import.meta.env.VITE_API_BASE_URL || '',

    // API 前缀
    apiPrefix: import.meta.env.VITE_API_PREFIX || '/api',

    // 是否开启调试模式
    debug: import.meta.env.VITE_DEBUG === 'true',
}

// 获取完整的 API 地址
export const getApiUrl = (path: string): string => {
    const baseUrl = config.apiBaseUrl
    const prefix = config.apiPrefix

    // 确保路径以 / 开头
    const normalizedPath = path.startsWith('/') ? path : `/${path}`

    if (baseUrl) {
        return `${baseUrl}${prefix}${normalizedPath}`
    }

    return `${prefix}${normalizedPath}`
}

// 调试日志（仅在调试模式下输出）
export const debugLog = (...args: unknown[]): void => {
    if (config.debug) {
        console.log('[DEBUG]', ...args)
    }
}

export default config
