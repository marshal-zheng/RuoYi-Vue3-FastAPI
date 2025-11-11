```markdown
# 目标
在 **Vue 3 + Vite + Element Plus + Tailwind CSS v4**（CSS-first，无 SCSS/无 PostCSS-tw 插件）中，实现：
- **单一主题源**（CSS 变量 + `@theme`）
- **Tailwind 与 Element Plus 完全同源一致**
- **多主题**（默认/暗黑，可扩展品牌主题）
- **零回归**（保留现有类名与功能）

> 若仓库中仍留有旧的 `.scss` 文件或 `tokens.js`，按本文“迁移与清理”步骤处理。

---

## 一、依赖与 Vite 插件
- 确保安装：`tailwindcss@^4`、`@tailwindcss/vite`、`element-plus`
- `vite.config.ts` 启用 vite 插件（**不要**在 PostCSS 使用 Tailwind 插件）

```ts
// vite.config.ts
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [vue(), tailwindcss()],
})
```

## 二、核心文件：`src/assets/styles/theme.css`

这是唯一事实源：在 `@theme` 中声明 Tailwind 颜色变量，`@layer theme` 里为默认/暗黑赋值，并一次性映射到 Element Plus 的 `--el-*` 变量。Tailwind 会自动生成 `bg-primary-500`、`text-gray-800` 等实用类。

```css
@import "tailwindcss";

/* 1) Tailwind v4 主题变量：自动生成同名颜色类 */
@theme {
  /* 主色 */
  --color-primary-50:  #e3f2fd;
  --color-primary-100: #bbdefb;
  --color-primary-200: #90caf9;
  --color-primary-300: #64b5f6;
  --color-primary-400: #42a5f5;
  --color-primary-500: #409eff;
  --color-primary-600: #2196f3;
  --color-primary-700: #1976d2;
  --color-primary-800: #1565c0;
  --color-primary-900: #0d47a1;

  /* 功能色 */
  --color-success-500: #67c23a;
  --color-warning-500: #e6a23c;
  --color-danger-500:  #f56c6c;
  --color-info-500:    #909399;

  /* 灰阶（对齐 EP 的文本/边框语义） */
  --color-gray-50:  #fafafa;
  --color-gray-100: #f5f5f5;
  --color-gray-200: #ebeef5;
  --color-gray-300: #dcdfe6;
  --color-gray-400: #c0c4cc;
  --color-gray-500: #909399;
  --color-gray-600: #606266;
  --color-gray-700: #464c5b;
  --color-gray-800: #303133;
  --color-gray-900: #1d1e1f;

  /* 表面/背景 */
  --color-surface:   #ffffff;
  --color-surface-2: #f8f9fa;
  --color-overlay:   #ffffff;
}

/* 2) 默认/暗黑主题赋值 + 一次性映射到 Element Plus */
@layer theme {
  :root {
    /* Element Plus 变量映射：与 Tailwind 同源 */
    --el-color-primary: var(--color-primary-500);
    --el-color-success: var(--color-success-500);
    --el-color-warning: var(--color-warning-500);
    --el-color-danger:  var(--color-danger-500);
    --el-color-info:    var(--color-info-500);

    --el-bg-color:          var(--color-surface);
    --el-bg-color-page:     var(--color-surface-2);
    --el-bg-color-overlay:  var(--color-overlay);

    --el-text-color-primary:    var(--color-gray-800);
    --el-text-color-regular:    var(--color-gray-700);
    --el-text-color-secondary:  var(--color-gray-600);
    --el-text-color-placeholder:var(--color-gray-500);

    --el-border-color:           var(--color-gray-300);
    --el-border-color-light:     var(--color-gray-300);
    --el-border-color-lighter:   var(--color-gray-200);
    --el-border-color-extra-light: var(--color-gray-200);

    /* 可选：圆角/阴影 */
    --el-border-radius-base: 4px;
    --el-box-shadow-light: 0 1px 3px rgba(0,0,0,.1), 0 1px 2px rgba(0,0,0,.06);
  }

  /* 暗黑主题覆盖（class 或 data-attr 任选其一或同时支持） */
  html.dark,
  [data-theme="dark"] {
    --color-surface:   #141414;
    --color-surface-2: #1d1e1f;
    --color-overlay:   #1d1e1f;

    /* 灰阶反转/加强 */
    --color-gray-900: #ffffff;
    --color-gray-800: #d0d0d0;
    --color-gray-700: #909399;
    --color-gray-600: #a8abb2;
    --color-gray-500: #434343;
    --color-gray-400: #434343;
    --color-gray-300: #434343;
  }
}

/* 3) 语义组件类（可留在这里，或迁到 tailwind.config.ts 的 addUtilities） */
@layer components {
  .theme-card {
    /* 使用 CSS 变量 + 任意值语法，确保两端一致 */
    @apply bg-[--el-bg-color] border border-[--el-border-color-light] rounded-[4px] shadow-[var(--el-box-shadow-light)] transition;
  }
  .theme-button {
    @apply rounded-[4px] font-medium transition border;
  }
  .theme-input {
    @apply px-3 py-2 border border-[--el-border-color] rounded-[4px] bg-[--el-bg-color] text-[--el-text-color-primary] transition;
  }
}
```

## 三、入口引入

保证在应用入口引入主题（位置靠前）

```ts
// main.ts / main.js
import '@/assets/styles/theme.css'
```

## 四、`tailwind.config.ts`（精简）

v4 推荐 CSS-first：只保留扫描范围、`darkMode`、必要的自定义 utilities；不要在 config 里再做颜色表注入（避免双来源）。

```ts
// tailwind.config.ts
import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  darkMode: 'class', // 支持 'class' (html.dark) 或 'media' (系统偏好)
  theme: {
    extend: {
      // 如需：自定义 keyframes/animation/spacing ……
    },
  },
  plugins: [
    // 你原有的 .el-card / .el-button-* 等 utilities 如需保留，放这里
    function ({ addUtilities }) {
      addUtilities({
        '.el-card': {
          '@apply bg-[--el-bg-color] border border-[--el-border-color-light] rounded-[4px] shadow-[var(--el-box-shadow-light)]': {},
        },
        '.el-button-primary': {
          '@apply bg-primary-500 hover:bg-primary-600 text-white border-primary-500 hover:border-primary-600': {},
        },
        // ... 其余保持不变
      })
    },
  ],
} satisfies Config
```

## 五、可选：品牌主题扩展

新增主题 = 在 `@layer theme` 增加一个作用域覆盖几个核心 `--color-*` 即可

```css
@layer theme {
  [data-theme="ocean"] {
    --color-primary-500: #00bcd4;
    --color-surface:   #f5fbfd;
    --color-surface-2: #e6f7fb;
    /* 按需继续覆盖 */
  }
}
```

切换方式：

```html
<html data-theme="ocean">...</html>
<!-- 或 -->
<html class="dark">...</html>
```

## 六、迁移与清理（避免“双来源”）

- **若仓库仍有 SCSS 文件**：全部移除或改为普通 CSS（v4 无需 SCSS）。
- **若有 `src/theme/tokens.js`**：
  - **无运行时 JS 取色需求** → **直接删除**，避免与 CSS 变量“双来源漂移”；
  - **有运行时需求** → 改造成“读取 CSS 变量的 runtime 适配层”，而不是写死颜色：

  ```ts
  // src/theme/theme-runtime.ts
  const readVar = (name: string, el: HTMLElement = document.documentElement) =>
    getComputedStyle(el).getPropertyValue(name).trim()

  export const themeRuntime = {
    color: (name: string) => readVar(name),          // 例如：'--color-primary-500'
    el:    (name: string) => readVar(name),          // 例如：'--el-color-primary'
  }
  ```
- **删除旧的 `theme-integration.scss`**（如仍存在）：其中的变量/暗黑覆盖已由 `theme.css` 接管；仅保留你确实需要的复杂选择器修补（也可迁入 `@layer components`）。

## 七、验收清单（零回归）

✅ `bg-primary-500` / `text-gray-800` / `border-gray-300` 等类工作正常
✅ Element Plus 组件（Button/Input/Card/Dialog…）颜色、边框、背景与 Tailwind 一致
✅ 切换 `.dark` 或 `data-theme="ocean"`，两端样式同步变化
✅ 既有自定义 utilities（如 `.el-card`）仍可用；表层布局/动画未破坏
✅ 仓库里无多余的 SCSS/旧 token 双来源
```