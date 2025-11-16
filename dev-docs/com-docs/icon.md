# ZxIcon

统一图标组件,支持多种图标类型。

## 基础用法

```vue
<!-- Element Plus图标 -->
<zx-icon icon="Edit" :size="20" color="#409EFF" />

<!-- Iconify图标 -->
<zx-icon icon="mdi:home" :size="20" />

<!-- 本地SVG图标 -->
<zx-icon icon="svg-icon:custom-icon" :size="20" />

<!-- iconfont图标 -->
<zx-icon icon="icon-user" :size="20" />
```

## 带Tooltip

```vue
<!-- 简单文本 -->
<zx-icon icon="Edit" tooltip="编辑" />

<!-- 完整配置 -->
<zx-icon 
  icon="Edit" 
  :tooltip="{ 
    content: '编辑项目', 
    placement: 'top',
    trigger: 'hover'
  }" 
/>
```

## Props

- `icon`: (必需) 图标名称或组件对象
- `size`: 图标大小,默认16
- `color`: 图标颜色
- `hover-color`: hover时颜色
- `tooltip`: 提示文本或配置对象
- `disabled`: 是否禁用

## 图标类型识别

1. Element Plus: 直接用组件名 `"Edit"`, `"Delete"`
2. Iconify: 格式 `"prefix:name"` 如 `"mdi:home"`
3. 本地SVG: 格式 `"svg-icon:name"`
4. Iconfont: 格式 `"icon-name"` 或 `"iconfont icon-name"`

## 事件

- `@click`: 点击事件

