---
title: Grid List 自动高度计算
lang: zh-CN
---

# Grid List 自动高度计算

Grid List 组件提供了智能的自动高度计算功能，能够根据页面实际可用空间自动调整组件和表格的高度，确保在不同屏幕尺寸下都有良好的显示效果。

## 工作原理

Grid List 的自动高度计算包含两个层面：

### 1. 页面布局高度计算

当组件包含特定的 class（`zx-grid-list--page`、`grid-list--page` 或 `is-page`）时，会自动计算整个组件应占用的高度。

```vue
<zx-grid-list class="is-page">
  <!-- 组件内容 -->
</zx-grid-list>
```

**计算公式：**

```
可用高度 = 视口高度 - 元素距顶部距离 - 底部预留空间
```

其中：

- **视口高度**：浏览器窗口的内部高度
- **元素距顶部距离**：通过 `getBoundingClientRect().top` 自动测量
- **底部预留空间**：包括页脚高度、内容边距、父元素底部边距等

### 2. 表格高度自适应

当 `autoFitTableHeight` 属性为 `true` 时，表格会自动填充容器的可用高度：

```vue
<zx-grid-list class="is-page" :auto-fit-table-height="true">
  <template #table="{ grid }">
    <el-table :data="grid.list">
      <!-- 表格列定义 -->
    </el-table>
  </template>
</zx-grid-list>
```

## 高度检测机制

### 自动感知上方内容

组件通过浏览器的 `getBoundingClientRect()` API 实时测量自身距离视口顶部的距离。这个距离**自动包含了**上方所有内容的高度，无需手动配置。

**示例场景：**

```
┌─────────────────────────┐  ← 视口顶部 (0px)
│   导航栏 (60px)          │
├─────────────────────────┤
│   面包屑 (40px)          │
├─────────────────────────┤
│   标题区 (50px)          │
├─────────────────────────┤  ← grid-list 组件在这里
│   <grid-list />         │     自动测得 top = 150px
│                         │
└─────────────────────────┘
```

组件不需要知道上方具体有什么元素，只需要测量到自己距离顶部的实际距离即可。

### 底部空间配置

对于底部的固定元素（如页脚），组件提供了三种配置方式：

#### 方式 1：全局 CSS 变量（推荐）

在全局样式中定义：

```css
:root {
  --app-footer-height: 60px; /* 底部页脚高度 */
  --app-content-padding: 20px; /* 内容区域边距 */
}
```

#### 方式 2：组件 Props

通过属性传入偏移量：

```vue
<zx-grid-list class="is-page" :page-viewport-offset="{ top: 10, bottom: 20 }" />
```

- `top`: 顶部额外偏移（很少使用）
- `bottom`: 底部预留空间

#### 方式 3：组件级 CSS 变量

针对特定组件设置：

```css
.my-grid-list {
  --zx-grid-list-page-offset-top: 10px;
  --zx-grid-list-page-offset-bottom: 20px;
}
```

## 触发时机

自动高度计算会在以下情况触发：

1. **组件挂载时** - 初始化布局
2. **窗口大小改变时** - 响应式调整
3. **容器尺寸变化时** - 通过 `ResizeObserver` 监听
4. **相关属性变化时** - 如 `autoFitTableHeight`、`pageViewportOffset` 等

## 常见问题

### 底部空白过大

如果发现底部预留空间过大，按以下步骤排查：

#### 1. 检查全局 CSS 变量

在浏览器控制台执行：

```javascript
getComputedStyle(document.documentElement).getPropertyValue(
  '--app-footer-height'
)
getComputedStyle(document.documentElement).getPropertyValue(
  '--app-content-padding'
)
```

#### 2. 检查组件 CSS 变量

```javascript
const gridEl = document.querySelector('.zx-grid-list-wrapper')
getComputedStyle(gridEl).getPropertyValue('--zx-grid-list-page-offset-bottom')
```

#### 3. 检查父元素和自身样式

```javascript
const gridEl = document.querySelector('.zx-grid-list-wrapper')
getComputedStyle(gridEl.parentElement).paddingBottom // 父元素底部边距
getComputedStyle(gridEl).marginBottom // 组件底部边距
```

#### 解决方案

**方案 1：覆盖 CSS 变量**

```css
:root {
  --app-footer-height: 0px;
  --app-content-padding: 0px;
}
```

**方案 2：调整 Props**

```vue
<zx-grid-list class="is-page" :page-viewport-offset="{ bottom: 0 }" />
```

**方案 3：移除父元素 padding**

```css
.grid-list-container {
  padding-bottom: 0 !important;
}
```

### 高度计算不准确

确保满足以下条件：

1. 组件添加了 `is-page` 或相关 class
2. 组件在 DOM 中已正确渲染
3. 父容器没有 `display: none` 等影响测量的样式

### 禁用自动高度

如果不需要自动高度功能：

```vue
<!-- 不添加 page 相关 class -->
<zx-grid-list>
  <!-- 组件将使用 100% 高度，相对于父容器 -->
</zx-grid-list>
```

或者设置固定高度：

```css
.my-grid-list {
  height: 600px !important;
}
```

## 最佳实践

### 1. 全页面列表场景

```vue
<template>
  <div class="page-container">
    <zx-grid-list
      class="is-page"
      :auto-fit-table-height="true"
      :request="loadData"
    >
      <template #table="{ grid }">
        <el-table :data="grid.list">
          <el-table-column prop="name" label="名称" />
          <el-table-column prop="value" label="值" />
        </el-table>
      </template>
    </zx-grid-list>
  </div>
</template>
```

### 2. 配合固定页脚

```css
/* 全局样式 */
:root {
  --app-footer-height: 60px;
}
```

```vue
<template>
  <div class="app">
    <header>顶部导航</header>
    <main>
      <zx-grid-list class="is-page" />
    </main>
    <footer style="height: 60px;">底部页脚</footer>
  </div>
</template>
```

### 3. 微调偏移量

```vue
<zx-grid-list
  class="is-page"
  :page-viewport-offset="{
    top: 0, // 顶部不额外偏移
    bottom: 80, // 底部预留 80px（页脚 60px + 边距 20px）
  }"
/>
```

## 技术细节

### 核心实现

自动高度计算的核心逻辑位于 `useGridLayout` 组合式函数中：

- **`measurePageLayoutHeight`** - 测量并设置页面布局高度
- **`applyAutoTableHeight`** - 应用表格自适应高度
- **`setupAutoHeightTracking`** - 设置自动高度追踪（使用 ResizeObserver）

### CSS 变量

组件使用以下 CSS 变量：

- `--zx-grid-list-page-height` - 计算出的页面高度（由 JS 动态设置）
- `--zx-grid-list-page-offset-top` - 顶部偏移量
- `--zx-grid-list-page-offset-bottom` - 底部偏移量
- `--app-footer-height` - 全局页脚高度
- `--app-content-padding` - 全局内容边距

### 浏览器兼容性

- `getBoundingClientRect()` - 所有现代浏览器支持
- `ResizeObserver` - 现代浏览器支持，旧版浏览器降级为 `window.resize` 监听
- `requestAnimationFrame` - 用于性能优化，不支持时同步执行

## 总结

Grid List 的自动高度计算功能通过智能测量和灵活配置，能够适应各种复杂的页面布局需求。核心原理是利用浏览器 API 实时测量元素位置，结合配置的底部预留空间，计算出最优的组件高度。

对于大多数场景，只需添加 `is-page` class 并配置全局的页脚高度即可获得良好的自适应效果。
