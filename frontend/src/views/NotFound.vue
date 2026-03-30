<template>
  <div class="not-found">
    <div class="not-found-content">
      <div class="glitch-code">404</div>
      <p class="not-found-text">抱歉，您访问的页面不存在。</p>
      <a-button type="primary" size="large" @click="$router.push('/')">
        返回首页
      </a-button>
    </div>
  </div>
</template>

<style scoped>
.not-found {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
}

.not-found-content {
  text-align: center;
  padding: 48px;
  background: var(--glass-bg);
  backdrop-filter: blur(var(--glass-blur));
  -webkit-backdrop-filter: blur(var(--glass-blur));
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  box-shadow: var(--glass-shadow);
}

.glitch-code {
  font-family: 'Fira Code', monospace;
  font-size: 96px;
  font-weight: 700;
  background: linear-gradient(135deg, #6366F1, #8B5CF6);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1;
  margin-bottom: 16px;
  text-shadow: none;
}

.not-found-text {
  color: var(--color-text-muted);
  font-size: 16px;
  margin-bottom: 32px;
}
</style>
