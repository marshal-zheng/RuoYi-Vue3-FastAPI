# 测试框架使用指南

本项目集成了 Vitest 测试框架，支持单元测试、组件测试和 E2E 测试。

## 🚀 快速开始

### 安装依赖

项目已经预装了以下测试相关依赖：

- `vitest` - 现代化的测试框架
- `@testing-library/vue` - Vue 组件测试工具
- `@testing-library/jest-dom` - DOM 断言扩展
- `@testing-library/user-event` - 用户交互模拟
- `@vitest/browser` - 浏览器模式支持
- `@vitest/ui` - 测试 UI 界面
- `webdriverio` - E2E 测试驱动
- `jsdom` 和 `happy-dom` - DOM 环境模拟

### 运行测试

```bash
# 运行所有测试
yarn test

# 运行测试（一次性）
yarn test:run

# 启动测试 UI 界面
yarn test:ui

# 运行浏览器模式测试
yarn test:browser

# 运行浏览器模式测试（一次性）
yarn test:browser:run

# 生成测试覆盖率报告
yarn test:coverage

# 监听模式运行测试
yarn test:watch
```

## 📁 目录结构

```
tests/
├── unit/           # 单元测试
│   ├── components/ # 组件测试
│   └── utils/      # 工具函数测试
├── e2e/            # E2E 测试
├── reports/        # 测试报告
├── setup.ts        # 测试环境设置
├── types.d.ts      # 类型声明
└── README.md       # 本文档
```

## 🧪 编写测试

### 单元测试示例

```typescript
import { describe, it, expect } from 'vitest'
import { mount } from '@testing-library/vue'
import MyComponent from '@/components/MyComponent.vue'

describe('MyComponent', () => {
  it('should render correctly', () => {
    const wrapper = mount(MyComponent, {
      props: {
        title: 'Test Title'
      }
    })
    
    expect(wrapper.getByText('Test Title')).toBeTruthy()
  })

  it('should handle click events', async () => {
    const wrapper = mount(MyComponent)
    const button = wrapper.getByRole('button')
    
    await button.click()
    
    expect(wrapper.emitted().click).toBeTruthy()
  })
})
```

### 工具函数测试示例

```typescript
import { describe, it, expect } from 'vitest'
import { parseTime } from '@/utils/ruoyi'

describe('parseTime', () => {
  it('should format date correctly', () => {
    const date = new Date('2023-01-01 12:00:00')
    const result = parseTime(date, '{y}-{m}-{d}')
    expect(result).toBe('2023-01-01')
  })
})
```

### E2E 测试示例

```typescript
import { describe, it, expect } from 'vitest'

describe('Login Page E2E Tests', () => {
  it('should display login form', async () => {
    if (typeof document !== 'undefined') {
      // 等待页面加载
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      // 检查登录表单
      const loginForm = document.querySelector('form')
      expect(loginForm).toBeTruthy()
    }
  })
})
```

## ⚙️ 配置说明

### vitest.config.ts

主要配置项：

- **测试环境**: 使用 `jsdom` 模拟浏览器环境
- **文件匹配**: `**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}`
- **覆盖率**: 支持多种格式的覆盖率报告
- **浏览器模式**: 支持 Chrome + WebDriverIO
- **全局设置**: 自动加载 `tests/setup.ts`

### 测试环境设置 (tests/setup.ts)

自动模拟以下浏览器 API：

- `matchMedia`
- `ResizeObserver`
- `IntersectionObserver`
- `localStorage` / `sessionStorage`
- `URL.createObjectURL`
- `fetch`

## 📊 测试报告

### HTML 报告

运行测试后会在 `tests/reports` 目录生成 HTML 报告：

```bash
# 查看测试报告
npx vite preview --outDir tests/reports
```

### 覆盖率报告

```bash
# 生成覆盖率报告
yarn test:coverage

# 报告将生成在 coverage/ 目录
```

## 🔧 最佳实践

### 1. 测试文件命名

- 单元测试：`ComponentName.test.ts`
- E2E 测试：`feature-name.test.ts`
- 工具函数测试：`utils/function-name.test.ts`

### 2. 测试结构

```typescript
describe('组件/功能名称', () => {
  describe('具体功能点', () => {
    it('should 具体行为描述', () => {
      // 测试代码
    })
  })
})
```

### 3. 断言建议

- 使用语义化的断言方法
- 优先使用 `@testing-library` 的查询方法
- 避免测试实现细节，专注于用户行为

### 4. 模拟和存根

```typescript
import { vi } from 'vitest'

// 模拟函数
const mockFn = vi.fn()

// 模拟模块
vi.mock('@/api/user', () => ({
  getUserInfo: vi.fn().mockResolvedValue({ name: 'Test User' })
}))
```

## 🐛 常见问题

### 1. 模块导入问题

如果遇到模块导入错误，检查：
- `vite.config.ts` 中的别名配置
- `tests/types.d.ts` 中的类型声明

### 2. DOM 相关测试失败

确保：
- 使用 `jsdom` 环境
- 在测试中等待 DOM 更新
- 使用 `@testing-library` 的异步查询方法

### 3. 浏览器模式问题

如果浏览器模式测试失败：
- 确保已安装 Chrome 浏览器
- 检查 WebDriverIO 配置
- 考虑使用 headless 模式

## 📚 参考资源

- [Vitest 官方文档](https://vitest.dev/)
- [Vue Testing Library](https://testing-library.com/docs/vue-testing-library/intro/)
- [Testing Library 最佳实践](https://testing-library.com/docs/guiding-principles/)
- [WebDriverIO 文档](https://webdriver.io/)

---

**注意**: 本测试框架已经配置完成，可以直接使用。如有问题，请参考上述文档或查看示例测试文件。