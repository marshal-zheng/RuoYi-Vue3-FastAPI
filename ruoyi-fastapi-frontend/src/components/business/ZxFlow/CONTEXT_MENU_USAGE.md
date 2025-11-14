# 右键菜单自定义使用指南

## 概述

`useContextMenu` 现在支持自定义菜单项的位置配置，允许将自定义菜单项放置在标准菜单项的顶部或底部。

## 基本用法

```javascript
import { useContextMenu } from './composables/useContextMenu.js'

const contextMenuOptions = {
  customItems: {
    // 空白区域右键菜单
    blank: [
      {
        id: 'custom-action-1',
        label: '自定义操作 1',
        icon: 'Plus',
        position: 'top', // 显示在顶部
        action: () => {
          console.log('执行自定义操作 1')
        }
      },
      {
        id: 'custom-action-2',
        label: '自定义操作 2',
        icon: 'Edit',
        position: 'bottom', // 显示在底部（默认）
        action: () => {
          console.log('执行自定义操作 2')
        }
      }
    ],

    // 节点右键菜单
    node: [
      {
        id: 'node-custom-1',
        label: '编辑指标',
        icon: 'Edit',
        position: 'top',
        action: () => {
          console.log('编辑指标')
        }
      },
      {
        id: 'node-custom-2',
        label: '复制指标',
        icon: 'DocumentCopy',
        position: 'top',
        action: () => {
          console.log('复制指标')
        }
      },
      {
        id: 'node-custom-3',
        label: '删除指标',
        icon: 'Delete',
        position: 'bottom',
        danger: true,
        action: () => {
          console.log('删除指标')
        }
      }
    ],

    // 边右键菜单
    edge: [
      {
        id: 'edge-custom-1',
        label: '编辑关系',
        icon: 'Edit',
        position: 'top',
        action: () => {
          console.log('编辑关系')
        }
      }
    ]
  }
}

const { contextMenu, showContextMenu, hideContextMenu, handleMenuClick, setupGraphEvents } =
  useContextMenu(graph, contextMenuOptions)
```

## 菜单项配置选项

### 基本属性

- `id` (string): 菜单项的唯一标识符
- `label` (string): 显示的文本
- `icon` (string): 图标名称（Element Plus 图标）
- `action` (function): 点击时执行的函数
- `position` (string): 显示位置，可选值：
  - `'top'`: 显示在标准菜单项顶部
  - `'bottom'`: 显示在标准菜单项底部（默认值）

### 可选属性

- `disabled` (boolean): 是否禁用菜单项
- `hidden` (boolean): 是否隐藏菜单项
- `danger` (boolean): 是否为危险操作（红色显示）
- `shortcut` (string): 快捷键提示文本

## 位置配置效果

### position: 'top'

自定义菜单项会显示在标准菜单项的上方：

```
[自定义菜单项 1]  ← position: 'top'
[自定义菜单项 2]  ← position: 'top'
─────────────────
[标准菜单项 1]
[标准菜单项 2]
[标准菜单项 3]
─────────────────
[自定义菜单项 3]  ← position: 'bottom' (默认)
```

### position: 'bottom' (默认)

自定义菜单项会显示在标准菜单项的下方（原有行为）。

## 实际使用示例

### 在指标系统中使用

```javascript
// 在指标管理页面中
const indicatorContextMenu = {
  customItems: {
    node: [
      {
        id: 'edit-indicator',
        label: '编辑指标',
        icon: 'Edit',
        position: 'top',
        action: () => openIndicatorEditor(node)
      },
      {
        id: 'duplicate-indicator',
        label: '复制指标',
        icon: 'DocumentCopy',
        position: 'top',
        action: () => duplicateIndicator(node)
      },
      {
        id: 'delete-indicator',
        label: '删除指标',
        icon: 'Delete',
        position: 'bottom',
        danger: true,
        action: () => deleteIndicator(node)
      }
    ],
    blank: [
      {
        id: 'add-indicator',
        label: '添加指标',
        icon: 'Plus',
        position: 'top',
        action: () => showAddIndicatorDialog()
      }
    ]
  }
}
```

## 注意事项

1. **分割线自动添加**: 系统会自动在顶部和底部的自定义菜单项之间添加分割线
2. **向后兼容**: 如果不指定 `position` 属性，默认为 `'bottom'`，保持原有行为
3. **图标支持**: 支持 Element Plus 的所有图标组件
4. **错误处理**: 菜单项的 `action` 函数如果出错，会在控制台输出错误信息

## 完整示例

```vue
<template>
  <div class="graph-container">
    <div ref="graphContainer"></div>
    <XFlowContextMenu :context-menu="contextMenu" @menu-click="handleMenuClick" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useContextMenu } from './composables/useContextMenu.js'
import XFlowContextMenu from './components/XFlowContextMenu.vue'

const graphContainer = ref()
const graph = ref()

const { contextMenu, handleMenuClick, setupGraphEvents } = useContextMenu(graph, {
  customItems: {
    node: [
      {
        id: 'edit-node',
        label: '编辑节点',
        icon: 'Edit',
        position: 'top',
        action: () => console.log('编辑节点')
      }
    ]
  }
})

onMounted(() => {
  // 初始化图形实例
  // graph.value = new Graph({ ... });

  // 设置事件监听
  setupGraphEvents()
})
</script>
```

这样就完成了自定义菜单项位置配置的功能，现在可以灵活地控制菜单项的显示位置。
