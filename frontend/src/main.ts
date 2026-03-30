/**
 * 应用入口
 * Main entry point with plugins initialization
 */
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import Antd from 'ant-design-vue'

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

// 图标按需在各组件中 import 使用，不再全局注册以减小打包体积

app.mount('#app')
