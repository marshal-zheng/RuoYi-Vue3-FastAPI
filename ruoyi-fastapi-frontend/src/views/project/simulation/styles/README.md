# 仿真模块样式系统

## 概述

仿真模块采用"航空暗黑系"设计风格，使用统一的CSS变量系统管理主题。

## 文件结构

```
styles/
├── variables.css           # 核心：统一的CSS变量定义
├── simulation-theme.css    # Element Plus组件主题覆盖（导入variables.css）
├── global-popper-dark.css  # 全局Popper深色样式（Teleport到body的元素）
├── simulation-dialog-theme.less  # 对话框/抽屉样式混入
├── aviation-dark-theme.less      # 浮动面板/统计卡片样式
├── fault-injection-mode.less     # 故障注入模式特殊样式
├── chart-tooltip.less      # 图表tooltip样式
└── animation.css           # 动画相关样式
```

## CSS变量说明

所有CSS变量在 `.simulation-dark` 容器内生效。

### 背景色系

| 变量名 | 用途 | 示例值 |
|--------|------|--------|
| `--sim-bg-base` | 最深背景，页面底层 | `#020617` |
| `--sim-bg-main` | 主背景色，主容器 | `#0b1220` |
| `--sim-bg-panel` | 面板背景，卡片/面板 | `#0f172a` |
| `--sim-bg-elevated` | 浮层背景，下拉框/弹窗 | `#1e293b` |
| `--sim-bg-hover` | 悬停背景 | `#334155` |
| `--sim-bg-active` | 激活背景 | `rgba(34, 211, 238, 0.1)` |

### 文字色系

| 变量名 | 用途 | 示例值 |
|--------|------|--------|
| `--sim-text-primary` | 主要文字，标题/重要内容 | `#f1f5f9` |
| `--sim-text-regular` | 常规文字，正文内容 | `#e2e8f0` |
| `--sim-text-secondary` | 次要文字，辅助说明 | `#cbd5e1` |
| `--sim-text-tertiary` | 三级文字，提示/占位符 | `#94a3b8` |
| `--sim-text-disabled` | 禁用文字 | `#64748b` |

### 边框色系

| 变量名 | 用途 | 示例值 |
|--------|------|--------|
| `--sim-border-base` | 基础边框 | `rgba(51, 65, 85, 0.5)` |
| `--sim-border-light` | 浅边框 | `rgba(51, 65, 85, 0.3)` |
| `--sim-border-hover` | 悬停边框 | `rgba(71, 85, 105, 0.8)` |
| `--sim-border-focus` | 聚焦边框 | `rgba(34, 211, 238, 0.5)` |
| `--sim-border-accent` | 强调边框 | `rgba(34, 211, 238, 0.25)` |

### 主题强调色

| 变量名 | 用途 | 示例值 |
|--------|------|--------|
| `--sim-accent` | 主强调色（航空青色） | `#22d3ee` |
| `--sim-accent-light` | 浅强调色 | `rgba(34, 211, 238, 0.6)` |
| `--sim-accent-dim` | 暗强调色 | `rgba(34, 211, 238, 0.3)` |
| `--sim-accent-bg` | 强调背景 | `rgba(34, 211, 238, 0.1)` |

### 状态色系

| 变量名 | 用途 | 示例值 |
|--------|------|--------|
| `--sim-success` | 成功/正常 | `#22c55e` |
| `--sim-warning` | 警告 | `#fbbf24` |
| `--sim-danger` | 错误/危险 | `#ef4444` |
| `--sim-info` | 信息 | `#3b82f6` |

## 使用方式

### 1. 在Vue组件中使用CSS变量

```vue
<style scoped>
.my-component {
  background: var(--sim-bg-panel);
  color: var(--sim-text-primary);
  border: 1px solid var(--sim-border-base);
}
</style>
```

### 2. 使用预定义的类名

```html
<!-- 专业级卡片 -->
<div class="pro-card">
  <div class="pro-card-header">标题</div>
  <div>内容</div>
</div>

<!-- 对话框应用主题 -->
<el-dialog class="simulation-dialog">...</el-dialog>

<!-- 抽屉应用主题 -->
<el-drawer class="simulation-drawer">...</el-drawer>
```

### 3. Select/Popover 深色样式

由于 Select 的下拉框是通过 Teleport 挂载到 body 的，不在 `.simulation-dark` 容器内，
需要通过 `popper-class` 属性指定深色样式：

```html
<el-select
  v-model="value"
  popper-class="sim-popper-dark"
>
  <el-option ... />
</el-select>
```

可用的 popper-class：
- `sim-popper-dark` - 通用深色下拉框样式
- `sim-popover-dark` - 深色 Popover 样式
- `sim-tooltip-dark` - 深色 Tooltip 样式
- `sim-dropdown-dark` - 深色 Dropdown 菜单样式
- `sim-picker-popper-dark` - 深色日期/时间选择器样式

### 4. 使用Less混入

在 `.vue` 文件的 `<style lang="less">` 中：

```less
@import '../styles/simulation-dialog-theme.less';

.my-card {
  .sim-dialog-card();  // 应用卡片样式
}
```

可用的混入：
- `.sim-dialog-container()` - 对话框容器样式
- `.sim-dialog-card()` - 卡片样式
- `.sim-dialog-table()` - 表格样式
- `.sim-dialog-collapse()` - 折叠面板样式
- `.sim-dialog-tag()` - 标签样式
- `.sim-dialog-button()` - 按钮样式
- `.sim-dialog-scrollbar()` - 滚动条样式
- `.sim-drawer-container()` - 抽屉容器样式
- `.sim-dialog-input()` - 输入框样式
- `.sim-dialog-select()` - 选择框样式

## 主题切换支持

后续系统支持主题切换时，只需：

1. 修改 `variables.css` 中的CSS变量值
2. 或者在系统主题切换时动态修改 `.simulation-dark` 下的变量值

示例：

```css
/* 浅色主题 */
.simulation-light {
  --sim-bg-base: #ffffff;
  --sim-bg-main: #f8fafc;
  --sim-text-primary: #1e293b;
  /* ... 其他变量 */
}
```

## 组件专用样式类

### 输入框/选择框深色样式

```html
<el-select class="sim-select-dark" ... />
<el-input class="sim-input-dark" ... />
<el-button class="sim-btn-dark" ... />
```

### 浮动面板

```html
<zx-floating-panel class="simbus-floating-panel" theme="dark">
  ...
</zx-floating-panel>
```

## 注意事项

1. 所有仿真相关页面需要在根元素添加 `simulation-dark` 类
2. 优先使用CSS变量，保持样式统一
3. Less变量现已映射到CSS变量，保持向后兼容
4. 避免使用硬编码的颜色值，使用变量代替
