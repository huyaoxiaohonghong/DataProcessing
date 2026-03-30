<template>
  <a-config-provider :locale="zhCN" :theme="darkGlassTheme">
    <router-view />
  </a-config-provider>
</template>

<script setup lang="ts">
import zhCN from 'ant-design-vue/es/locale/zh_CN'
import { theme } from 'ant-design-vue'

const darkGlassTheme = {
  token: {
    colorPrimary: '#6366F1',
    colorBgBase: '#000000',
    colorBgContainer: 'rgba(255, 255, 255, 0.06)',
    colorBgElevated: '#0A0A0F',
    colorBgLayout: '#000000',
    colorBorder: 'rgba(255, 255, 255, 0.08)',
    colorBorderSecondary: 'rgba(255, 255, 255, 0.05)',
    colorText: '#F1F5F9',
    colorTextSecondary: '#94A3B8',
    colorTextTertiary: '#475569',
    colorTextQuaternary: '#334155',
    colorFill: 'rgba(255, 255, 255, 0.06)',
    colorFillSecondary: 'rgba(255, 255, 255, 0.04)',
    colorFillTertiary: 'rgba(255, 255, 255, 0.02)',
    borderRadius: 12,
    fontFamily: "'Fira Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
    fontFamilyCode: "'Fira Code', monospace",
    boxShadow: '0 8px 32px rgba(0, 0, 0, 0.4)',
  },
  algorithm: theme.darkAlgorithm,
}
</script>
