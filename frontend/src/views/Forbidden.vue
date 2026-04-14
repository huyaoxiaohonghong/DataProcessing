<template>
  <div class="forbidden">
    <div class="forbidden-content">
      <div class="glitch-code">403</div>
      <p class="forbidden-text">权限不足，请联系管理员。</p>
      <div class="forbidden-actions">
        <a-button type="primary" size="large" @click="$router.push('/')">
          返回首页
        </a-button>
        <a-button size="large" @click="$router.back()">
          返回上页
        </a-button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.forbidden {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
}

.forbidden-content {
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
  background: linear-gradient(135deg, #F59E0B, #EF4444);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1;
  margin-bottom: 16px;
  text-shadow: none;
}

.forbidden-text {
  color: var(--color-text-muted);
  font-size: 16px;
  margin-bottom: 32px;
}

.forbidden-actions {
  display: flex;
  gap: 16px;
  justify-content: center;
}
</style>
