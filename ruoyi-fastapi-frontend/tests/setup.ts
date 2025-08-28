import { vi } from 'vitest'
import '@testing-library/jest-dom'

// 全局模拟配置
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // deprecated
    removeListener: vi.fn(), // deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

// 模拟 ResizeObserver
if (!globalThis.ResizeObserver) {
  globalThis.ResizeObserver = vi.fn().mockImplementation(() => ({
    observe: vi.fn(),
    unobserve: vi.fn(),
    disconnect: vi.fn(),
  }))
}

// 模拟 IntersectionObserver
if (!globalThis.IntersectionObserver) {
  globalThis.IntersectionObserver = vi.fn().mockImplementation(() => ({
    observe: vi.fn(),
    unobserve: vi.fn(),
    disconnect: vi.fn(),
  }))
}

// 模拟 localStorage
const localStorageMock: Storage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
  length: 0,
  key: vi.fn(),
}

if (!globalThis.localStorage) {
  Object.defineProperty(globalThis, 'localStorage', {
    value: localStorageMock,
    writable: true,
    configurable: true,
  })
}

// 模拟 sessionStorage
const sessionStorageMock: Storage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
  length: 0,
  key: vi.fn(),
}

if (!globalThis.sessionStorage) {
  Object.defineProperty(globalThis, 'sessionStorage', {
    value: sessionStorageMock,
    writable: true,
    configurable: true,
  })
}

// 模拟 URL.createObjectURL
if (globalThis.URL && !globalThis.URL.createObjectURL) {
  globalThis.URL.createObjectURL = vi.fn(() => 'mocked-url')
  globalThis.URL.revokeObjectURL = vi.fn()
}

// 模拟 fetch
if (!globalThis.fetch) {
  globalThis.fetch = vi.fn()
}

// 模拟 console 方法（可选，用于测试时减少日志输出）
// global.console = {
//   ...console,
//   log: vi.fn(),
//   warn: vi.fn(),
//   error: vi.fn(),
// }

// 设置测试环境变量
if (typeof process !== 'undefined' && process.env) {
  process.env.NODE_ENV = 'test'
} else {
  // 在浏览器环境中模拟 process.env
  ;(globalThis as any).process = {
    env: {
      NODE_ENV: 'test'
    }
  }
}