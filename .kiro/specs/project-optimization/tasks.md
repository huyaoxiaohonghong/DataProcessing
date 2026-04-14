# 实施计划：项目分析与优化

## 概述

基于需求文档和设计文档，将 11 项优化需求转化为可执行的编码任务。任务按照依赖关系排序，从安全加固和基础设施改进开始，逐步推进到功能优化和前端改进。后端使用 Python (Django)，前端使用 TypeScript (Vue 3)。

## 任务

- [x] 1. 消除硬编码敏感信息与安全配置
  - [x] 1.1 修改 `backend/config/settings.py`，移除 `SECRET_KEY` 的默认值，未配置时抛出 `ImproperlyConfigured` 异常；添加生产环境 HTTPS 安全设置（`SECURE_SSL_REDIRECT`、`SECURE_HSTS_SECONDS`、`SESSION_COOKIE_SECURE`、`CSRF_COOKIE_SECURE`）
    - _需求: 1.3, 2.4_
  - [x] 1.2 修改 `backend/apps/users/serializers.py` 中 `UserAdminSerializer.create()` 方法，使用 `secrets.token_urlsafe(12)` 生成随机密码替代硬编码 `123456`
    - _需求: 1.2_
  - [x] 1.3 修改 `docker-compose.yml`，移除 MySQL 和 Redis 的默认明文密码，改为必须通过 `.env` 注入；移除 MySQL (`3306:3306`) 和 Redis (`6379:6379`) 的外部端口映射
    - _需求: 1.4, 9.1_
  - [x] 1.4 确保 `.env` 已加入 `.gitignore`，创建或更新 `.env.example` 模板文件
    - _需求: 1.1_
  - [ ]* 1.5 编写属性测试：随机密码生成不使用硬编码值
    - **Property 1: 随机密码生成不使用硬编码值**
    - **验证: 需求 1.2**

- [x] 2. 后端安全加固
  - [x] 2.1 修改 `backend/apps/files/serializers.py` 中 `FileUploadSerializer`，添加 `validate_file` 方法实现文件类型白名单校验（仅允许 xlsx/xls/csv）和文件大小限制（50MB）
    - _需求: 2.1, 2.2_
  - [x] 2.2 新建 `backend/utils/safe_eval.py`，实现基于 AST 的安全数学表达式解析器 `safe_eval_expr`，仅允许数字和四则运算
    - _需求: 2.3_
  - [x] 2.3 修改 `backend/apps/processing/services.py` 中 `_evaluate_expression` 方法，使用 `safe_eval_expr` 替代 `eval()`
    - _需求: 2.3_
  - [x] 2.4 修改 `backend/config/settings.py`，在 `REST_FRAMEWORK` 中添加 `DEFAULT_THROTTLE_CLASSES` 和 `DEFAULT_THROTTLE_RATES` 全局速率限制配置；为注册接口配置 `ScopedRateThrottle`（每 IP 每小时 10 次）
    - _需求: 2.5, 2.6_
  - [ ]* 2.5 编写属性测试：文件类型白名单校验
    - **Property 2: 文件类型白名单校验**
    - **验证: 需求 2.1**
  - [ ]* 2.6 编写属性测试：安全表达式解析器等价性
    - **Property 3: 安全表达式解析器等价性**
    - **验证: 需求 2.3**

- [x] 3. 检查点 - 确保安全加固相关改动正确
  - 确保所有测试通过，如有疑问请询问用户。

- [x] 4. 数据库索引优化与 N+1 查询修复
  - [x] 4.1 修改 `backend/apps/processing/models.py`，为 `ProcessingTask` 添加 `(status, created_by)` 和 `(created_at,)` 索引；为 `DataMapping` 添加 `(status, created_by)` 索引
    - _需求: 4.1, 4.2_
  - [x] 4.2 修改 `backend/apps/files/models.py`，为 `File` 添加 `(status, file_type)` 索引
    - _需求: 4.3_
  - [x] 4.3 修改 `backend/apps/system/models.py`，为 `LoginLog` 添加 `(created_at, status)` 复合索引；为 `OperationLog` 添加 `(created_at, module)` 复合索引
    - _需求: 4.5_
  - [x] 4.4 修改 `backend/apps/files/serializers.py` 中 `FileCategorySerializer`，将 `get_children_count` 和 `get_files_count` 改为读取 `annotate` 注解字段；修改 `backend/apps/files/views.py` 中 `FileCategoryViewSet.get_queryset()` 使用 `annotate` 聚合查询
    - _需求: 4.4_
  - [x] 4.5 生成数据库迁移文件 `python manage.py makemigrations`
    - _需求: 4.1, 4.2, 4.3, 4.5_
  - [ ]* 4.6 编写属性测试：分类聚合计数一致性
    - **Property 5: 分类聚合计数一致性**
    - **验证: 需求 4.4**

- [x] 5. Celery 异步任务集成
  - [x] 5.1 在 `backend/requirements.txt` 中添加 `celery[redis]>=5.3,<6.0` 依赖；在 `backend/config/settings.py` 中添加 Celery 配置
    - _需求: 3.1_
  - [x] 5.2 新建 `backend/config/celery.py`，配置 Celery 应用；修改 `backend/config/__init__.py` 导入 Celery app
    - _需求: 3.1_
  - [x] 5.3 修改 `backend/apps/processing/models.py`，为 `ProcessingTask` 添加 `celery_task_id` 字段并生成迁移
    - _需求: 3.5_
  - [x] 5.4 新建 `backend/apps/processing/tasks.py`，实现 `execute_processing_task` Celery 任务
    - _需求: 3.1, 3.2, 3.4_
  - [x] 5.5 修改 `backend/apps/processing/views.py` 中 `ProcessingTaskViewSet.execute` 方法，改为提交 Celery 异步任务；修改 `terminate` 方法使用 `app.control.revoke` 终止任务
    - _需求: 3.1, 3.5_
  - [ ]* 5.6 编写属性测试：任务异常处理完整性
    - **Property 4: 任务异常处理完整性**
    - **验证: 需求 3.4**

- [x] 6. 检查点 - 确保后端核心改动正确
  - 确保所有测试通过，如有疑问请询问用户。

- [x] 7. 统一 API 响应格式
  - [x] 7.1 修改 `backend/apps/users/views.py`，将 `RegisterView.create`、`LoginView.post`、`LogoutView.post`、`UserProfileView`、`ChangePasswordView` 全部改用 `ApiResponse` 方法返回响应
    - _需求: 6.1, 6.3_
  - [x] 7.2 修改 `backend/apps/users/views.py` 中 `UserViewSet` 的 `list`、`create`、`update`、`destroy`、`roles` 方法，使用 `ApiResponse` 替代手动构造 `Response`
    - _需求: 6.2_
  - [x] 7.3 移除 `backend/apps/users/views.py` 中的 `UserListView` 类，并更新 `backend/apps/users/urls.py` 中对应的路由
    - _需求: 6.4_
  - [ ]* 7.4 编写单元测试验证所有用户相关端点返回统一 `ApiResponse` 格式
    - _需求: 6.1, 6.2_

- [x] 8. 日志与监控优化
  - [x] 8.1 在 `backend/requirements.txt` 中添加 `python-json-logger>=2.0,<3.0`；修改 `backend/config/settings.py` 中 `LOGGING` 配置，添加 JSON 格式化器
    - _需求: 10.4_
  - [x] 8.2 修改 `backend/apps/processing/services.py`，在 `execute_task` 和 `_process_row` 中添加结构化日志（包含 task_id、mapping_id、row_index、duration 等字段）
    - _需求: 10.1, 10.2_
  - [x] 8.3 修改 `backend/apps/system/middleware.py` 中 `OperationLogMiddleware`，扩展为同时记录 GET 请求中响应时间 > 3s 的慢查询警告日志
    - _需求: 10.3_
  - [x] 8.4 修改 `backend/apps/system/cache.py` 中 `CacheService` 的 `get`/`set` 方法，添加 try-except 实现 Redis 降级容错
    - _需求: 10.5_
  - [ ]* 8.5 编写属性测试：Redis 降级容错
    - **Property 6: Redis 降级容错**
    - **验证: 需求 10.5**

- [x] 9. 检查点 - 确保后端所有改动正确
  - 确保所有测试通过，如有疑问请询问用户。

- [x] 10. Docker 部署优化
  - [x] 10.1 修改 `backend/Dockerfile`，添加非 root 用户 `appuser` 并使用 `USER appuser` 运行 Gunicorn
    - _需求: 9.2_
  - [x] 10.2 修改 `docker-compose.yml`，为 Backend 添加 `healthcheck` 配置；为所有服务添加 `deploy.resources.limits` 资源限制
    - _需求: 9.4, 9.5_
  - [x] 10.3 修改 `frontend/nginx.conf`，为 `/admin/` 路径添加 IP 白名单限制；添加 `Content-Security-Policy` 响应头
    - _需求: 9.3, 8.3_

- [x] 11. 前端错误处理与安全改进
  - [x] 11.1 找到前端 ApiClient 响应拦截器文件，增强错误分类处理：网络超时提示、403 提示、500 提示
    - _需求: 7.1, 7.2, 7.3_
  - [x] 11.2 新建 `frontend/src/views/Forbidden.vue` 403 权限不足页面；修改 `frontend/src/router/index.ts`，添加 `/403` 路由并将权限不足时的跳转目标改为 403 页面
    - _需求: 7.5_
  - [x] 11.3 修改 `frontend/src/stores/user.ts`，将 Token 存储从 `sessionStorage` 迁移到 Pinia 内存变量；移除 `sessionStorage` 中的 token 读写
    - _需求: 8.1_
  - [x] 11.4 修改 `frontend/src/router/index.ts` 中路由守卫的 token 检查逻辑，适配内存存储方案
    - _需求: 8.1, 8.2_

- [x] 12. 前端构建优化与代码组织
  - [x] 12.1 修改 `frontend/vite.config.ts`，添加 `xlsx` 到 `manualChunks` 分包配置；设置 `chunkSizeWarningLimit: 500`
    - _需求: 11.4_
  - [x] 12.2 在数据处理相关页面中将 `import * as XLSX from 'xlsx'` 改为动态导入 `const XLSX = await import('xlsx')`
    - _需求: 11.1_
  - [x] 12.3 新建 `frontend/src/composables/useTable.ts`，提取通用表格分页、加载状态等可复用逻辑
    - _需求: 11.3_
  - [ ]* 12.4 为 API 请求层添加统一的 TypeScript 泛型响应类型定义
    - _需求: 11.2_

- [ ] 13. 建立后端自动化测试体系
  - [x] 13.1 在 `backend/requirements.txt` 中添加 `pytest>=8.0,<9.0`、`pytest-django>=4.8,<5.0`、`pytest-cov>=5.0,<6.0`、`hypothesis>=6.100,<7.0`；新建 `backend/pytest.ini` 配置文件
    - _需求: 5.6_
  - [x] 13.2 新建 `backend/tests/conftest.py`，定义共享 fixtures（测试用户、测试文件、测试映射配置等）
    - _需求: 5.1, 5.2, 5.3_
  - [ ]* 13.3 新建 `backend/tests/test_excel_service.py`，编写 ExcelService 单元测试（空文件、单/多 Sheet、无表头）
    - _需求: 5.1_
  - [ ]* 13.4 新建 `backend/tests/test_expression_eval.py`，编写表达式计算单元测试（正常计算、字段引用、除零、非法字符）
    - _需求: 5.2_
  - [ ]* 13.5 新建 `backend/tests/test_process_row.py`，编写行处理单元测试（direct/lookup/computed/default 映射、多值展开）
    - _需求: 5.3_
  - [ ]* 13.6 新建 `backend/tests/test_auth_flow.py`，编写用户认证集成测试（登录、登出、Token 刷新）
    - _需求: 5.4_
  - [ ]* 13.7 新建 `backend/tests/test_file_upload.py`，编写文件上传下载集成测试
    - _需求: 5.5_

- [x] 14. 前端任务进度展示
  - [x] 14.1 在任务执行页面添加轮询任务进度接口，显示进度条和已处理行数信息
    - _需求: 7.4_

- [x] 15. 最终检查点 - 确保所有改动正确
  - 确保所有测试通过，如有疑问请询问用户。

## 备注

- 标记 `*` 的任务为可选任务，可跳过以加速 MVP 交付
- 每个任务引用了对应的需求编号以确保可追溯性
- 检查点任务用于阶段性验证，确保增量开发的正确性
- 属性测试验证设计文档中定义的通用正确性属性
- 单元测试验证具体示例和边界条件
