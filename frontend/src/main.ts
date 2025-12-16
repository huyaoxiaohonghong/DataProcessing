/**
 * 应用入口
 * Main entry point with plugins initialization
 */
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import Antd from 'ant-design-vue'
import * as Icons from '@ant-design/icons-vue'

import App from './App.vue'
import router from './router'

import 'ant-design-vue/dist/reset.css'
import './style.css'

const app = createApp(App)

// 注册 Pinia
const pinia = createPinia()
app.use(pinia)

// 注册 Router
app.use(router)

// 注册 Ant Design Vue
app.use(Antd)

// 全局注册图标组件
for (const [key, component] of Object.entries(Icons)) {
    if (key !== 'default' && typeof component === 'object') {
        app.component(key, component as any)
    }
}

app.mount('#app')
