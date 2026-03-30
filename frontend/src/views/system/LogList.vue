<template>
  <div class="logs-page">
    <h2 class="page-title">操作日志</h2>
    <div class="glass-panel">
      <a-empty description="操作日志功能开发中..." />
    </div>
  </div>
</template>

<style scoped>
.page-title {
  margin: 0 0 24px;
  font-size: 24px;
  font-weight: 700;
  font-family: 'Fira Code', monospace;
  color: var(--color-text);
}

.glass-panel {
  padding: 48px 24px;
  background: var(--glass-bg);
  backdrop-filter: blur(var(--glass-blur));
  -webkit-backdrop-filter: blur(var(--glass-blur));
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--glass-shadow);
}
</style>
