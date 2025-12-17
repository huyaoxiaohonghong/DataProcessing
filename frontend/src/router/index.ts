/**
 * Vue Router 配置
 * Router configuration with authentication guards
 */
import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
    {
        path: '/login',
        name: 'Login',
        component: () => import('@/views/Login.vue'),
        meta: { requiresAuth: false, title: '登录' }
    },
    {
        path: '/',
        name: 'Layout',
        component: () => import('@/layouts/MainLayout.vue'),
        redirect: '/dashboard',
        meta: { requiresAuth: true },
        children: [
            {
                path: 'dashboard',
                name: 'Dashboard',
                component: () => import('@/views/Dashboard.vue'),
                meta: { title: '仪表盘', icon: 'dashboard' }
            },
            {
                path: 'files',
                name: 'Files',
                component: () => import('@/views/files/FileList.vue'),
                meta: { title: '文件管理', icon: 'folder' }
            },
            {
                path: 'users',
                name: 'Users',
                component: () => import('@/views/users/UserList.vue'),
                meta: { title: '用户管理', icon: 'team', roles: ['admin'] }
            },
            {
                path: 'profile',
                name: 'Profile',
                component: () => import('@/views/Profile.vue'),
                meta: { title: '个人中心', icon: 'user' }
            },
            {
                path: 'logs/login',
                name: 'LoginLogs',
                component: () => import('@/views/system/LoginLogs.vue'),
                meta: { title: '登录日志', icon: 'file-protect', roles: ['admin'] }
            },
            {
                path: 'logs/operation',
                name: 'OperationLogs',
                component: () => import('@/views/system/OperationLogs.vue'),
                meta: { title: '操作日志', icon: 'file-search', roles: ['admin'] }
            },
            {
                path: 'departments',
                name: 'Departments',
                component: () => import('@/views/system/DepartmentList.vue'),
                meta: { title: '部门管理', icon: 'apartment', roles: ['admin'] }
            },
            {
                path: 'menus',
                name: 'Menus',
                component: () => import('@/views/system/MenuList.vue'),
                meta: { title: '菜单管理', icon: 'menu', roles: ['admin'] }
            },
            // 数据处理模块
            {
                path: 'processing/mappings',
                name: 'MappingList',
                component: () => import('@/views/processing/MappingList.vue'),
                meta: { title: '映射配置', icon: 'swap' }
            },
            {
                path: 'processing/mappings/create',
                name: 'MappingCreate',
                component: () => import('@/views/processing/MappingEdit.vue'),
                meta: { title: '新建映射配置', icon: 'swap' }
            },
            {
                path: 'processing/mappings/:id',
                name: 'MappingEdit',
                component: () => import('@/views/processing/MappingEdit.vue'),
                meta: { title: '编辑映射配置', icon: 'swap' }
            },
            {
                path: 'processing/tasks',
                name: 'TaskList',
                component: () => import('@/views/processing/TaskList.vue'),
                meta: { title: '处理任务', icon: 'thunderbolt' }
            }
        ]
    },
    {
        path: '/:pathMatch(.*)*',
        name: 'NotFound',
        component: () => import('@/views/NotFound.vue'),
        meta: { title: '404' }
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

// 路由守卫 - 认证检查
router.beforeEach((to, _from, next) => {
    // 设置页面标题
    document.title = `${to.meta.title || '数据处理系统'} - DPS`

    // 使用 sessionStorage 支持多标签页独立登录
    const token = sessionStorage.getItem('access_token')
    const requiresAuth = to.meta.requiresAuth !== false

    if (requiresAuth && !token) {
        // 需要认证但未登录，跳转登录页
        next({ name: 'Login', query: { redirect: to.fullPath } })
    } else if (to.name === 'Login' && token) {
        // 已登录但访问登录页，跳转首页
        next({ name: 'Dashboard' })
    } else {
        next()
    }
})

export default router
