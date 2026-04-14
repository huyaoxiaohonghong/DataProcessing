# 实现计划：滑动验证码增强（防机器人 & 防爬虫）

## 概述

基于需求文档和设计文档，将滑动验证码安全增强拆分为后端核心模块实现、前端组件增强、接口集成三个阶段，逐步递增实现。后端使用 Python/Django，前端使用 TypeScript/Vue.js。

## 任务

- [x] 1. 实现后端速率限制器 RateLimiter
  - [x] 1.1 创建 `backend/apps/system/rate_limiter.py`，实现 `RateLimiter` 类
    - 实现 `get_client_ip(request)` 方法，从请求中提取客户端真实 IP（支持 X-Forwarded-For）
    - 实现 `is_rate_limited(key, max_requests, window_seconds)` 方法，使用 Redis Sorted Set 滑动窗口算法
    - 实现 `record_login_failure(ip)` 方法，记录登录失败到 `login:fail:{ip}` 键（Sorted Set，TTL 1800s）
    - 实现 `is_ip_blocked(ip)` 方法，检查 `login:block:{ip}` 键是否存在；若 `login:fail:{ip}` 中 30 分钟内记录 ≥ 15 条则设置封锁标记（TTL 1800s）
    - Redis 异常时降级为不限制（捕获异常返回 False）
    - _需求: 3.1, 3.2, 3.3, 4.1, 4.2, 4.3, 4.4_

  - [ ]* 1.2 编写 RateLimiter 属性测试 — Property 5: 滑动窗口速率限制
    - 创建 `backend/apps/system/tests/__init__.py` 和 `backend/apps/system/tests/test_captcha_properties.py`
    - **Property 5: 滑动窗口速率限制**
    - **验证: 需求 3.1, 3.3, 4.1**

  - [ ]* 1.3 编写 RateLimiter 属性测试 — Property 6: IP 封锁机制
    - **Property 6: IP 封锁机制**
    - **验证: 需求 4.3, 4.4**

- [x] 2. 实现后端行为分析器 BehaviorAnalyzer
  - [x] 2.1 在 `backend/apps/system/services/captcha.py` 中新增 `BehaviorAnalyzer` 类
    - 实现 `analyze(trajectory, duration)` 方法，依次调用以下检查，任一失败返回 `(False, "行为异常")`
    - 实现 `_check_duration(duration)`: 检查 200ms ≤ duration ≤ 10000ms
    - 实现 `_check_track_count(trajectory)`: 检查轨迹点数 ≥ 5
    - 实现 `_check_speed_variance(trajectory)`: 计算 X 方向速度标准差 > 0
    - 实现 `_check_y_fluctuation(trajectory)`: 检查 Y 坐标非完全恒定
    - _需求: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [ ]* 2.2 编写 BehaviorAnalyzer 属性测试 — Property 1: 拒绝异常耗时
    - **Property 1: 行为分析器拒绝异常耗时**
    - **验证: 需求 2.1, 2.5**

  - [ ]* 2.3 编写 BehaviorAnalyzer 属性测试 — Property 2: 拒绝轨迹点不足
    - **Property 2: 行为分析器拒绝轨迹点不足**
    - **验证: 需求 2.2, 2.5**

  - [ ]* 2.4 编写 BehaviorAnalyzer 属性测试 — Property 3: 拒绝匀速滑动
    - **Property 3: 行为分析器拒绝匀速滑动**
    - **验证: 需求 2.3, 2.5**

  - [ ]* 2.5 编写 BehaviorAnalyzer 属性测试 — Property 4: 拒绝 Y 轴恒定轨迹
    - **Property 4: 行为分析器拒绝 Y 轴恒定轨迹**
    - **验证: 需求 2.4, 2.5**

- [x] 3. 增强后端 CaptchaService
  - [x] 3.1 修改 `CaptchaService.CAPTCHA_EXPIRE` 从 300 改为 120
    - _需求: 5.2_

  - [x] 3.2 增强 `create_background()` 方法
    - 添加 3-6 条随机干扰线（随机颜色、起止坐标、线宽）
    - 将噪点数量从 100 增加到 200-400 个
    - 对背景图应用高斯模糊（半径 0.5-1.0 像素）
    - _需求: 7.1, 7.2, 7.3_

  - [x] 3.3 修改 `generate_captcha(ip, fingerprint)` 方法
    - 新增 `ip` 和 `fingerprint` 参数
    - 缓存数据结构改为 `{x, y, ip, fingerprint, created_at}`，其中 `created_at` 使用 `time.time()`
    - _需求: 5.3, 5.4, 6.3_

  - [x] 3.4 增强 `verify_captcha(key, x_offset, ip, fingerprint, trajectory, duration)` 方法
    - 无论验证成功或失败，都立即删除缓存（一次性使用）
    - 校验请求 IP 与生成时 IP 一致
    - 校验客户端指纹与生成时一致，不一致返回 `(False, "客户端环境异常")`
    - 校验从生成到提交的时间间隔 ≥ 1 秒
    - 调用 `BehaviorAnalyzer.analyze()` 进行行为分析
    - 轨迹数据解析异常时跳过行为分析，仅校验 X 坐标（降级策略）
    - _需求: 5.1, 5.3, 5.4, 6.3, 6.4, 2.1-2.5_

  - [ ]* 3.5 编写 CaptchaService 属性测试 — Property 7: 验证码一次性使用
    - **Property 7: 验证码一次性使用**
    - **验证: 需求 5.1**

  - [ ]* 3.6 编写 CaptchaService 属性测试 — Property 8: 验证码绑定校验
    - **Property 8: 验证码绑定校验**
    - **验证: 需求 5.3, 6.3, 6.4**

  - [ ]* 3.7 编写 CaptchaService 属性测试 — Property 9: 验证码最小提交时间间隔
    - **Property 9: 验证码最小提交时间间隔**
    - **验证: 需求 5.4**

- [x] 4. 检查点 — 确保后端核心模块测试通过
  - 确保所有测试通过，如有问题请向用户确认。

- [x] 5. 增强后端视图层
  - [x] 5.1 修改 `backend/apps/system/views.py` 中的 `CaptchaView`
    - GET 请求中调用 `RateLimiter.is_rate_limited("rate:captcha:{ip}", 10, 60)` 进行频率限制
    - 超限时返回 HTTP 429 和 `{"code": 429, "message": "请求过于频繁，请稍后再试"}`
    - 从 query 参数获取 `fingerprint`，连同 IP 传入 `CaptchaService.generate_captcha(ip, fingerprint)`
    - _需求: 3.1, 3.2, 3.3_

  - [x] 5.2 修改 `backend/apps/users/views.py` 中的 `LoginView`
    - 在验证码校验前检查 `RateLimiter.is_ip_blocked(ip)`，被封锁返回 HTTP 429 和 "您的 IP 已被临时封锁，请 30 分钟后再试"
    - 检查 `RateLimiter.is_rate_limited("rate:login:{ip}", 5, 60)`，超限返回 HTTP 429 和 "登录尝试过于频繁，请 1 分钟后再试"
    - 从请求体获取 `trajectory`、`duration`、`fingerprint` 参数
    - 调用增强后的 `CaptchaService.verify_captcha(key, x_offset, ip, fingerprint, trajectory, duration)`
    - 登录失败时调用 `RateLimiter.record_login_failure(ip)`
    - _需求: 4.1, 4.2, 4.3, 4.4, 1.2, 2.1-2.5, 5.1-5.4, 6.3, 6.4_

- [x] 6. 增强前端 SlideVerify 组件
  - [x] 6.1 在 `frontend/src/components/SlideVerify/index.vue` 中添加客户端指纹采集
    - 组件挂载时采集 User-Agent、屏幕分辨率、时区偏移量
    - 使用 `SubtleCrypto` API 生成 SHA-256 指纹哈希
    - 获取验证码时将 fingerprint 作为 query 参数传递
    - _需求: 6.1, 6.2_

  - [x] 6.2 在 SlideVerify 组件中添加滑动轨迹采集
    - 在 `handleMouseDown`/`handleTouchStart` 中记录起始时间
    - 在 `handleMouseMove`/`handleTouchMove` 中以 ≤ 50ms 间隔记录轨迹点 `{x, y, t}`
    - 在 `verifySlider` 中计算滑动总耗时 `duration`
    - _需求: 1.1, 1.2, 1.3_

  - [x] 6.3 修改 SlideVerify 组件的验证逻辑和事件接口
    - 移除 `xOffset > 30` 的前端判断逻辑，所有验证结果交由后端判定
    - 对轨迹数据进行 Base64 编码 (`btoa(JSON.stringify(trackPoints))`)
    - 修改 `emit('success')` 事件，传递 `{captchaKey, xOffset, trajectory, duration, fingerprint}` 对象
    - _需求: 8.1, 8.2, 1.2_

  - [x] 6.4 添加 429 状态码处理
    - 验证码获取接口返回 429 时，显示"请求过于频繁，请稍后再试"提示
    - 禁用刷新按钮 60 秒，60 秒后自动恢复
    - _需求: 8.3_

  - [ ]* 6.5 编写前端属性测试 — Property 10: 客户端指纹确定性
    - **Property 10: 客户端指纹确定性**
    - **验证: 需求 6.1**

  - [ ]* 6.6 编写前端属性测试 — Property 11: 轨迹数据 Base64 编码往返
    - **Property 11: 轨迹数据 Base64 编码往返**
    - **验证: 需求 8.2**

  - [ ]* 6.7 编写前端属性测试 — Property 13: 轨迹点结构完整性
    - **Property 13: 轨迹点结构完整性**
    - **验证: 需求 1.1**

- [x] 7. 集成前端登录页和 API 层
  - [x] 7.1 修改 `frontend/src/api/system.ts` 中的 `getCaptcha` 函数
    - 接受 `fingerprint` 参数，作为 query 参数传递
    - _需求: 6.1_

  - [x] 7.2 修改 `frontend/src/api/user.ts` 中的 `LoginParams` 接口和 `login` 函数
    - `LoginParams` 新增 `captcha_key`、`x_offset`、`trajectory`、`duration`、`fingerprint` 字段
    - _需求: 1.2, 6.2, 8.2_

  - [x] 7.3 修改 `frontend/src/views/Login.vue` 登录页
    - 更新 `handleVerifySuccess` 接收增强后的验证数据对象（含 trajectory、duration、fingerprint）
    - 更新 `performLogin` 将所有增强字段传入登录 API
    - 处理登录接口 429 响应，显示对应错误消息
    - _需求: 1.2, 4.2, 4.4, 6.2, 8.2_

- [x] 8. 最终检查点 — 确保所有测试通过
  - 确保所有测试通过，如有问题请向用户确认。

## 备注

- 标记 `*` 的任务为可选任务，可跳过以加快 MVP 进度
- 每个任务引用了具体的需求编号以确保可追溯性
- 检查点任务确保增量验证
- 属性测试使用 `hypothesis` 库（Python 后端）验证正确性属性
- 前端属性测试可使用 `fast-check` 库（如项目引入 Vitest）
