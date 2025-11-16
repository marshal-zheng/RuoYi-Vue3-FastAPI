# ZxMoreAction

更多操作下拉菜单组件。

## 基础用法

```vue
<zx-more-action :list="actions" @select="handleSelect" />

<script setup>
const actions = [
  { label: '编辑', eventTag: 'edit', icon: Edit },
  { label: '删除', eventTag: 'delete', icon: Delete, danger: true },
  { isDivider: true },  // 分割线
  { label: '详情', eventTag: 'detail', disabled: false }
]

function handleSelect(item) {
  switch(item.eventTag) {
    case 'edit': // 编辑逻辑
    case 'delete': // 删除逻辑
  }
}
</script>
```

## ActionItem结构

```ts
interface ActionItem {
  label: string        // 显示文本
  eventTag: string     // 事件标识
  icon?: Component     // 图标组件
  disabled?: boolean   // 禁用状态
  danger?: boolean     // 危险样式
  isDivider?: boolean  // 是否为分割线
}
```

## Props

- `list`: 操作列表数组
- `trigger`: 触发方式,默认'hover'
- `size`: 尺寸 'small'|'default'|'large'

## 事件

- `@select`: 选择操作 `(item: ActionItem) => void`
- `@open`: 下拉打开
- `@close`: 下拉关闭

## 自定义触发器

```vue
<zx-more-action :list="actions">
  <el-button>更多操作</el-button>
</zx-more-action>
```

