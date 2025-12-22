/// <reference types="vite/client" />

interface ImportMetaEnv {
    /** 应用标题 */
    readonly VITE_APP_TITLE: string
    /** API 基础路径 */
    readonly VITE_API_BASE_URL: string
    /** API 前缀 */
    readonly VITE_API_PREFIX: string
    /** 是否开启调试模式 */
    readonly VITE_DEBUG: string
    /** 应用版本号 */
    readonly VITE_APP_VERSION: string
}

interface ImportMeta {
    readonly env: ImportMetaEnv
}
