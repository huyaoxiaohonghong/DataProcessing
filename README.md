# 数据处理管理系统 (Data Processing System)

一个现代化的数据处理管理系统，基于 Django + Vue 3 构建。

## 技术栈

### 后端
- **Framework**: Django 6.0 + Django REST Framework
- **Database**: MySQL
- **Cache**: Redis
- **Authentication**: JWT (Simple JWT)

### 前端
- **Framework**: Vue 3 + TypeScript
- **UI Library**: Ant Design Vue
- **Build Tool**: Vite
- **State Management**: Pinia

## 功能特性

### 用户管理
- 用户注册、登录、登出
- 角色权限管理（超级管理员、管理员、普通用户）
- 用户信息管理

### 部门管理
- 部门层级结构
- 部门 CRUD 操作

### 文件管理
- 文件上传、下载
- 文件分类管理
- 文件权限控制

### 菜单管理
- 动态菜单配置
- 菜单权限关联

### 日志管理
- 登录日志
- 操作日志

### 缓存系统
- Redis 缓存集成
- 数据热更新

## 快速开始

### 后端

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 数据库迁移
python manage.py migrate

# 启动服务
python manage.py runserver 8000
```

### 前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

## 环境变量

创建 `.env` 文件配置以下变量：

```env
# Database
DB_HOST=localhost
DB_PORT=3306
DB_NAME=data_processing
DB_USER=root
DB_PASSWORD=your_password

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_password
```

## API 文档

启动后端服务后访问：
- API 根路径: `http://localhost:8000/api/`

## 项目结构

```
DataProcessing/
├── backend/                # Django 后端
│   ├── apps/
│   │   ├── users/         # 用户模块
│   │   ├── system/        # 系统模块（部门、菜单、日志）
│   │   └── files/         # 文件模块
│   ├── config/            # Django 配置
│   └── requirements.txt
│
└── frontend/              # Vue 前端
    ├── src/
    │   ├── api/           # API 接口
    │   ├── components/    # 组件
    │   ├── views/         # 页面
    │   ├── stores/        # 状态管理
    │   └── router/        # 路由配置
    └── package.json
```

## 许可证

MIT License