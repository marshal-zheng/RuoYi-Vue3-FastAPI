# ZxTag

增强型标签组件,基于Element Plus Tag封装。

## 基础用法

```vue
<!-- 基础标签 -->
<zx-tag>标签</zx-tag>

<!-- 不同主题 -->
<zx-tag theme="dark">深色</zx-tag>
<zx-tag theme="light">浅色</zx-tag>
<zx-tag theme="plain">朴素</zx-tag>

<!-- 不同类型(Element Plus原生) -->
<zx-tag type="success">成功</zx-tag>
<zx-tag type="warning">警告</zx-tag>
<zx-tag type="danger">危险</zx-tag>
<zx-tag type="info">信息</zx-tag>

<!-- 可关闭 -->
<zx-tag closable @close="handleClose">可关闭</zx-tag>
```

## 宽度控制与溢出

```vue
<!-- 固定最小宽度(字符数) -->
<zx-tag :width="10">固定宽度标签</zx-tag>

<!-- 最大宽度+tooltip -->
<zx-tag max-width="100px">很长的标签文本会自动省略</zx-tag>

<!-- 禁用tooltip -->
<zx-tag max-width="100px" tooltip-disabled>不显示tooltip</zx-tag>

<!-- 无右边距 -->
<zx-tag no-margin>无边距</zx-tag>
```

## Props

- `theme`: 主题 `'dark' | 'light' | 'plain'`,默认'light'
- `width`: 最小宽度(字符数)
- `max-width`: 最大宽度,默认'144px'
- `no-margin`: 无右边距,默认false
- `tooltip-disabled`: 禁用tooltip,默认false
- `self-style`: 自定义样式对象

其他Element Plus Tag的props直接使用:
- `type`: 类型 `'success'|'warning'|'danger'|'info'`
- `size`: 尺寸 `'large'|'default'|'small'`
- `effect`: 效果 `'dark'|'light'|'plain'`
- `closable`: 可关闭
- `color`: 自定义颜色

## 事件

- `@close`: 关闭事件
- `@click`: 点击事件

