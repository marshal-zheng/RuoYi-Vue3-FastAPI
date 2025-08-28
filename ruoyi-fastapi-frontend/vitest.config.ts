/// <reference types="vitest" />
import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue() as any],
  resolve: {
    alias: {
      '@': resolve(__dirname, './src')
    }
  },
  test: {
    // 全局测试配置
    globals: true,
    
    // 测试环境配置
    environment: 'jsdom',
    
    // 测试文件匹配模式
    include: [
      'src/**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}',
      'tests/**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}'
    ],
    
    // 排除文件
    exclude: [
      'node_modules',
      'dist',
      '.idea',
      '.git',
      '.cache'
    ],
    
    // 测试设置文件
    setupFiles: ['./tests/setup.ts'],
    
    // 类型声明文件
    typecheck: {
      include: ['**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}']
    },
    
    // 覆盖率配置
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'tests/',
        'dist/',
        '**/*.d.ts',
        '**/*.config.{js,ts}',
        '**/vite.config.ts',
        '**/vitest.config.ts'
      ]
    },
    
    // 浏览器测试配置
    browser: {
      enabled: true,
      provider: 'webdriverio',
      headless: false,
      name: 'chrome'
    },
    
    // 测试超时配置
    testTimeout: 10000,
    hookTimeout: 10000,
    
    // 并发配置
    pool: 'threads',
    poolOptions: {
      threads: {
        singleThread: false,
        minThreads: 1,
        maxThreads: 4
      }
    },
    
    // 监听模式配置
    watch: true,
    
    // 报告器配置
    reporters: ['verbose', 'html'],
    outputFile: {
      html: './tests/reports/index.html'
    },
    
    // 模拟配置
    clearMocks: true,
    restoreMocks: true,
    
    // 环境变量
    env: {
      NODE_ENV: 'test'
    }
  }
})