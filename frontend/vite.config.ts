import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  // 加载环境变量
  const env = loadEnv(mode, process.cwd())

  return {
    plugins: [vue()],
    resolve: {
      alias: {
        '@': resolve(__dirname, 'src'),
      },
    },
    // 定义全局常量
    define: {
      __APP_ENV__: JSON.stringify(mode),
    },
    server: {
      host: '0.0.0.0',
      port: 5173,
      proxy: {
        '/api': {
          target: env.VITE_API_BASE_URL || 'http://127.0.0.1:8000',
          changeOrigin: true,
        },
      },
    },
    build: {
      // 生产环境配置
      sourcemap: mode !== 'production',
      rollupOptions: {
        output: {
          // 分包策略：将大型依赖拆分为独立 chunk
          manualChunks: {
            'ant-design-vue': ['ant-design-vue', '@ant-design/icons-vue'],
            'vue-vendor': ['vue', 'vue-router', 'pinia'],
          },
        },
      },
    },
  }
})
