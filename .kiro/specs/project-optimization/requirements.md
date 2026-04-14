# 需求文档：项目分析与优化

## 简介

本文档基于对数据处理系统（Data Processing System）前后端代码的深入分析，识别出安全性、性能、代码质量、测试覆盖、部署配置等方面的问题，并提出系统性的优化需求。该系统采用 Django REST Framework 后端 + Vue 3 前端的前后端分离架构，使用 MySQL + Redis 作为数据存储，Docker Compose 进行部署。

## 术语表

- **DPS**: Data Processing System，数据处理系统
- **Backend**: Django REST Framework 后端应用
- **Frontend**: Vue 3 + TypeScript + Vite 前端应用
- **ExcelService**: 后端 Excel 文件解析与处理服务
- **DataProcessingService**: 后端数据映射与转换执行服务
- **CacheService**: 基于 Redis 的缓存服务
- **RateLimiter**: 基于 Redis 滑动窗口的速率限制器
- **ApiClient**: 前端 Axios HTTP 客户端实例
- **CaptchaService**: 滑动验证码生成与验证服务

## 需求

### 需求 1：消除硬编码敏感信息

**用户故事：** 作为运维人员，我希望所有敏感信息从代码和版本控制中移除，以防止凭据泄露。

#### 验收标准

1. WHEN `.env` 文件包含真实数据库密码、Redis 密码或 S3 密钥时，THE Backend SHALL 将 `.env` 文件加入 `.gitignore` 并仅保留 `.env.example` 作为模板
2. WHEN 用户通过管理员接口创建新用户且未指定密码时，THE Backend SHALL 生成符合密码策略的随机密码，而非使用硬编码默认密码 `123456`
3. THE Backend SHALL 将 `DJANGO_SECRET_KEY` 的默认值替换为强制要求环境变量配置，在未配置时启动失败并输出明确错误提示
4. WHEN Docker Compose 配置中引用数据库密码时，THE DPS SHALL 通过环境变量或 Docker Secrets 注入，而非在 `docker-compose.yml` 中使用默认明文密码

### 需求 2：加固后端安全防护

**用户故事：** 作为安全工程师，我希望后端 API 具备完善的安全防护机制，以抵御常见的 Web 攻击。

#### 验收标准

1. THE Backend SHALL 对文件上传接口实施文件类型白名单校验，仅允许 `.xlsx`、`.xls`、`.csv` 格式的文件上传
2. THE Backend SHALL 对上传文件大小实施限制，单个文件上传大小上限为 50MB
3. WHEN `DataProcessingService._evaluate_expression` 计算用户提供的表达式时，THE Backend SHALL 使用安全的数学表达式解析器替代 `eval()` 函数
4. THE Backend SHALL 在生产环境中启用 HTTPS 相关安全设置，包括 `SECURE_SSL_REDIRECT`、`SECURE_HSTS_SECONDS`、`SESSION_COOKIE_SECURE` 和 `CSRF_COOKIE_SECURE`
5. WHEN 注册接口 `/api/users/register/` 被调用时，THE Backend SHALL 对该接口实施速率限制，每个 IP 每小时最多允许 10 次注册请求
6. THE Backend SHALL 在 REST_FRAMEWORK 配置中启用 `DEFAULT_THROTTLE_CLASSES` 和 `DEFAULT_THROTTLE_RATES`，对匿名用户和认证用户分别设置全局请求频率限制

### 需求 3：优化数据处理任务执行机制

**用户故事：** 作为数据处理人员，我希望大文件处理任务不会阻塞 API 响应，以便在处理过程中继续使用系统。

#### 验收标准

1. WHEN 用户触发数据处理任务执行时，THE Backend SHALL 将任务提交到 Celery 异步任务队列，并立即返回任务 ID 和状态
2. WHILE 异步任务正在执行时，THE Backend SHALL 每处理 100 行数据更新一次任务进度到数据库
3. WHEN 用户查询任务状态时，THE Backend SHALL 返回包含 `progress`、`processed_rows`、`total_rows`、`status` 的实时进度信息
4. IF 异步任务执行过程中发生未捕获异常，THEN THE Backend SHALL 将任务状态标记为 `failed`，记录完整错误堆栈到 `error_message` 字段，并释放所有已占用资源
5. WHEN 用户请求终止正在运行的任务时，THE Backend SHALL 通过 Celery 的 `revoke` 机制在 10 秒内终止任务执行

### 需求 4：提升数据库查询性能

**用户故事：** 作为系统管理员，我希望系统在数据量增长后仍能保持快速响应，以确保用户体验。

#### 验收标准

1. THE Backend SHALL 为 `ProcessingTask` 模型的 `status` 和 `created_by` 字段添加数据库索引
2. THE Backend SHALL 为 `DataMapping` 模型的 `status` 和 `created_by` 字段添加数据库索引
3. THE Backend SHALL 为 `File` 模型的 `status` 和 `file_type` 字段添加数据库索引
4. WHEN `FileCategorySerializer` 计算 `children_count` 和 `files_count` 时，THE Backend SHALL 使用数据库聚合注解（`annotate`）替代逐条 `count()` 查询，消除 N+1 查询问题
5. WHEN 日志查询接口返回大量数据时，THE Backend SHALL 对 `LoginLog` 和 `OperationLog` 的 `created_at` 字段建立复合索引以优化时间范围查询

### 需求 5：建立后端自动化测试体系

**用户故事：** 作为开发人员，我希望项目具备完善的自动化测试，以便在修改代码后快速验证功能正确性。

#### 验收标准

1. THE Backend SHALL 为 `ExcelService.parse_file_fields` 方法编写单元测试，覆盖空文件、单 Sheet、多 Sheet、无表头等场景
2. THE Backend SHALL 为 `DataProcessingService._evaluate_expression` 方法编写单元测试，覆盖正常计算、字段引用、除零错误、非法字符等场景
3. THE Backend SHALL 为 `DataProcessingService._process_row` 方法编写单元测试，覆盖 direct 映射、lookup 映射、computed 映射、default 映射和多值展开等场景
4. THE Backend SHALL 为用户认证流程（登录、登出、Token 刷新）编写集成测试
5. THE Backend SHALL 为文件上传和下载流程编写集成测试
6. THE Backend SHALL 配置 `pytest-cov` 并在 CI 中要求核心模块（`services.py`、`views.py`）测试覆盖率达到 70% 以上

### 需求 6：统一后端 API 响应格式

**用户故事：** 作为前端开发人员，我希望所有 API 接口返回统一格式的响应，以简化前端数据处理逻辑。

#### 验收标准

1. THE Backend SHALL 确保所有视图方法使用 `ApiResponse` 工具类返回响应，而非直接构造 `Response` 对象
2. WHEN `UserViewSet` 的 CRUD 方法返回响应时，THE Backend SHALL 使用 `ApiResponse.success`、`ApiResponse.created`、`ApiResponse.error` 等方法，与 `FileViewSet` 和 `ProcessingTaskViewSet` 保持一致
3. WHEN `RegisterView` 返回注册成功响应时，THE Backend SHALL 使用 `ApiResponse.created` 方法替代手动构造响应字典
4. THE Backend SHALL 移除 `UserListView` 兼容旧接口，将其功能合并到 `UserViewSet` 中

### 需求 7：优化前端错误处理与用户体验

**用户故事：** 作为终端用户，我希望在操作失败时看到清晰的错误提示，以便了解问题原因并采取正确操作。

#### 验收标准

1. WHEN `ApiClient` 收到网络超时错误时，THE Frontend SHALL 显示"网络连接超时，请检查网络后重试"的提示消息
2. WHEN `ApiClient` 收到 403 状态码时，THE Frontend SHALL 显示"权限不足，请联系管理员"的提示消息
3. WHEN `ApiClient` 收到 500 状态码时，THE Frontend SHALL 显示"服务器异常，请稍后重试"的提示消息
4. WHEN 用户在数据处理任务执行页面等待时，THE Frontend SHALL 显示任务进度条和已处理行数信息
5. WHEN 前端路由守卫检测到用户无权限访问某页面时，THE Frontend SHALL 跳转到 403 权限不足页面，而非静默重定向到仪表盘

### 需求 8：加固前端安全机制

**用户故事：** 作为安全工程师，我希望前端应用具备基本的安全防护，以防止 Token 泄露和 XSS 攻击。

#### 验收标准

1. THE Frontend SHALL 将 JWT Token 存储从 `sessionStorage` 迁移到 HttpOnly Cookie 或内存中，防止 XSS 攻击窃取 Token
2. WHEN `ApiClient` 的 Token 刷新失败时，THE Frontend SHALL 清除所有本地存储的认证信息并跳转到登录页面，同时显示"登录已过期，请重新登录"的提示
3. THE Frontend SHALL 在 Nginx 配置中添加 `Content-Security-Policy` 响应头，限制脚本和样式的加载来源

### 需求 9：优化 Docker 部署配置

**用户故事：** 作为运维人员，我希望 Docker 部署配置更加安全和高效，以降低生产环境风险。

#### 验收标准

1. THE DPS SHALL 在 `docker-compose.yml` 中为 MySQL 和 Redis 服务移除外部端口映射（`3306:3306` 和 `6379:6379`），仅允许内部网络访问
2. THE Backend SHALL 在 Dockerfile 中使用非 root 用户运行 Gunicorn 进程
3. THE Frontend SHALL 在 Nginx 配置中为 `/admin/` 路径添加 IP 白名单限制或基本认证
4. THE DPS SHALL 在 `docker-compose.yml` 中为 Backend 服务添加健康检查配置
5. THE DPS SHALL 在 `docker-compose.yml` 中为所有服务配置资源限制（`deploy.resources.limits`），防止单个服务耗尽主机资源

### 需求 10：完善日志与监控体系

**用户故事：** 作为运维人员，我希望系统具备完善的日志记录和监控能力，以便快速定位和排查生产问题。

#### 验收标准

1. THE Backend SHALL 为数据处理任务的执行过程添加结构化日志，包含 `task_id`、`mapping_id`、`row_index`、`duration` 等字段
2. WHEN 数据处理任务完成时，THE Backend SHALL 记录包含 `total_rows`、`success_rows`、`error_rows`、`duration_seconds` 的任务摘要日志
3. THE Backend SHALL 为操作日志中间件添加 GET 请求的慢查询记录，WHEN 响应时间超过 3 秒时记录警告日志
4. THE Backend SHALL 配置日志输出为 JSON 格式，便于日志收集系统（如 ELK）解析
5. IF Redis 连接失败，THEN THE Backend SHALL 记录错误日志并降级为无缓存模式继续运行，而非抛出未处理异常

### 需求 11：优化前端构建与代码组织

**用户故事：** 作为前端开发人员，我希望前端项目具备更好的代码组织和构建优化，以提升开发效率和页面加载速度。

#### 验收标准

1. THE Frontend SHALL 为 `xlsx` 依赖配置动态导入（`import()`），仅在数据处理页面按需加载，减少首屏 bundle 体积
2. THE Frontend SHALL 为 API 请求层添加统一的 TypeScript 泛型响应类型，确保所有 API 调用具备完整的类型推导
3. THE Frontend SHALL 将重复使用的表格列配置、分页配置等提取为可复用的 composable 函数
4. THE Frontend SHALL 在 `vite.config.ts` 中配置 `build.chunkSizeWarningLimit` 并确保单个 chunk 不超过 500KB
