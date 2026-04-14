# 需求文档：滑动验证码增强（防机器人 & 防爬虫）

## 简介

本功能旨在增强现有滑动验证码系统的安全性，防止机器人自动化攻击和恶意爬虫绕过验证。当前实现存在以下安全薄弱点：

1. **后端验证过于简单**：仅校验 X 坐标偏移量，容差 5px，机器人可通过暴力枚举或图像识别轻松破解
2. **无行为轨迹分析**：不采集也不校验用户滑动过程中的鼠标/触摸轨迹数据，无法区分人类与自动化脚本
3. **无频率限制**：验证码获取和验证接口均无速率限制，可被无限刷取
4. **验证码可重复尝试**：验证失败后不删除缓存，同一验证码可被反复尝试直到猜中
5. **前端校验薄弱**：前端仅判断 `xOffset > 30` 即视为成功，无实质性防护
6. **无客户端指纹**：不采集浏览器环境信息，无法识别异常客户端

本增强方案将从行为轨迹分析、频率限制、验证码安全加固、客户端指纹采集四个维度全面提升防护能力。

## 术语表

- **Captcha_Service**：后端滑动验证码服务，负责生成验证码图片、存储正确答案、校验用户提交的验证结果
- **SlideVerify_Component**：前端滑动验证码 Vue 组件，负责展示验证码图片、采集用户滑动行为、提交验证数据
- **Rate_Limiter**：速率限制器，基于 Redis 实现，按 IP 或客户端指纹限制接口调用频率
- **Behavior_Analyzer**：行为分析器，后端模块，分析用户滑动轨迹数据以判断是否为人类操作
- **Client_Fingerprint**：客户端指纹，由浏览器环境信息（User-Agent、屏幕分辨率、时区等）生成的哈希值
- **Trajectory**：滑动轨迹，用户从按下滑块到释放过程中记录的坐标和时间戳序列
- **Login_View**：后端登录视图，处理用户登录请求并集成验证码校验

## 需求

### 需求 1：滑动轨迹采集

**用户故事：** 作为系统安全管理员，我希望前端采集用户滑动过程中的行为轨迹数据，以便后端能够分析并区分人类操作与自动化脚本。

#### 验收标准

1. WHEN 用户按下滑块开始滑动, THE SlideVerify_Component SHALL 以不超过 50 毫秒的间隔记录滑动轨迹点，每个轨迹点包含 X 坐标、Y 坐标和相对起始时间的时间戳
2. WHEN 用户释放滑块完成滑动, THE SlideVerify_Component SHALL 将完整的轨迹数据数组连同 captcha_key 和 x_offset 一起提交给父组件
3. THE SlideVerify_Component SHALL 记录滑动总耗时（从按下到释放的毫秒数）并包含在提交数据中

### 需求 2：滑动行为分析

**用户故事：** 作为系统安全管理员，我希望后端能够分析滑动轨迹数据，识别出非人类的自动化操作行为。

#### 验收标准

1. WHEN 验证请求包含轨迹数据, THE Behavior_Analyzer SHALL 检查滑动总耗时是否在 200 毫秒至 10000 毫秒的合理范围内
2. WHEN 验证请求包含轨迹数据, THE Behavior_Analyzer SHALL 检查轨迹点数量是否不少于 5 个
3. WHEN 验证请求包含轨迹数据, THE Behavior_Analyzer SHALL 计算 X 坐标的速度标准差，验证滑动过程存在加速和减速变化（标准差大于 0）
4. WHEN 验证请求包含轨迹数据, THE Behavior_Analyzer SHALL 检查 Y 坐标是否存在微小波动（非完全恒定的 Y 值），因为人类滑动不可能保持 Y 坐标完全不变
5. IF 轨迹数据未通过任一行为分析检查, THEN THE Behavior_Analyzer SHALL 返回验证失败并附带"行为异常"的错误提示

### 需求 3：验证码获取频率限制

**用户故事：** 作为系统安全管理员，我希望限制验证码获取接口的调用频率，防止恶意刷取验证码消耗服务器资源。

#### 验收标准

1. THE Rate_Limiter SHALL 基于客户端 IP 地址限制验证码获取接口（GET /api/system/captcha/）的调用频率为每分钟 10 次
2. IF 客户端超过频率限制, THEN THE Captcha_Service SHALL 返回 HTTP 429 状态码和"请求过于频繁，请稍后再试"的错误消息
3. THE Rate_Limiter SHALL 使用 Redis 的滑动窗口算法实现频率计数，窗口大小为 60 秒

### 需求 4：登录验证频率限制

**用户故事：** 作为系统安全管理员，我希望限制登录接口的调用频率，防止暴力破解攻击。

#### 验收标准

1. THE Rate_Limiter SHALL 基于客户端 IP 地址限制登录接口（POST /api/users/login/）的调用频率为每分钟 5 次
2. IF 客户端超过登录频率限制, THEN THE Login_View SHALL 返回 HTTP 429 状态码和"登录尝试过于频繁，请 1 分钟后再试"的错误消息
3. WHEN 同一 IP 地址在 30 分钟内累计登录失败达到 15 次, THE Rate_Limiter SHALL 封锁该 IP 地址 30 分钟
4. WHILE IP 地址处于封锁状态, THE Login_View SHALL 拒绝该 IP 的所有登录请求并返回"您的 IP 已被临时封锁，请 30 分钟后再试"的错误消息

### 需求 5：验证码安全加固

**用户故事：** 作为系统安全管理员，我希望加固验证码的生成和校验机制，增加机器人破解的难度。

#### 验收标准

1. THE Captcha_Service SHALL 在验证失败后立即删除该验证码的缓存数据，确保每个验证码只能尝试验证 1 次
2. THE Captcha_Service SHALL 将验证码有效期从 300 秒缩短至 120 秒
3. THE Captcha_Service SHALL 在生成验证码时将客户端 IP 地址与 captcha_key 绑定存储，验证时校验请求 IP 与生成时的 IP 一致
4. THE Captcha_Service SHALL 在缓存中存储验证码的生成时间戳，验证时检查从生成到提交的时间间隔不少于 1 秒（过快提交视为机器人行为）

### 需求 6：客户端指纹采集

**用户故事：** 作为系统安全管理员，我希望采集客户端环境指纹信息，辅助识别异常请求来源。

#### 验收标准

1. WHEN 用户打开滑动验证码组件, THE SlideVerify_Component SHALL 采集浏览器 User-Agent、屏幕分辨率、时区偏移量，并生成一个客户端指纹哈希值
2. WHEN 用户提交验证结果, THE SlideVerify_Component SHALL 将客户端指纹哈希值包含在提交数据中
3. THE Captcha_Service SHALL 在生成验证码时将客户端指纹与 captcha_key 绑定存储，验证时校验提交的指纹与生成时的指纹一致
4. IF 验证时提交的客户端指纹与生成时不一致, THEN THE Captcha_Service SHALL 返回验证失败并附带"客户端环境异常"的错误提示

### 需求 7：验证码图片增强

**用户故事：** 作为系统安全管理员，我希望增强验证码背景图片的复杂度，增加图像识别破解的难度。

#### 验收标准

1. THE Captcha_Service SHALL 在背景图上绘制 3 至 6 条随机干扰线，每条线的颜色、起止坐标和线宽随机生成
2. THE Captcha_Service SHALL 在背景图上添加 200 至 400 个随机噪点（当前为 100 个）
3. THE Captcha_Service SHALL 对背景图应用轻微的高斯模糊（半径 0.5 至 1.0 像素），增加图像识别难度

### 需求 8：前端安全增强

**用户故事：** 作为系统安全管理员，我希望前端验证组件具备基本的反调试和防篡改能力。

#### 验收标准

1. WHEN 用户完成滑动验证, THE SlideVerify_Component SHALL 移除前端 `xOffset > 30` 的简单判断逻辑，将所有验证结果交由后端判定
2. THE SlideVerify_Component SHALL 在提交验证数据前对轨迹数据进行 Base64 编码，避免明文传输
3. IF 验证码获取接口返回 HTTP 429 状态码, THEN THE SlideVerify_Component SHALL 显示"请求过于频繁，请稍后再试"的提示信息并禁用刷新按钮 60 秒
