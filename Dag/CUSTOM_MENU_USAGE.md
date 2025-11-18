# DAG 组件自定义菜单使用指南

## 概述

DAG 组件现在支持更灵活的自定义菜单机制，允许用户完全控制右键菜单的内容和顺序。

## 新的自定义菜单机制

### 基本用法

```vue
<template>
  <DAGPage
    :operators="operators"
    :custom-menu-handler="customMenuHandler"
    @edit-node="handleEditNode"
  />
</template>

<script setup>
// 自定义菜单处理器
const customMenuHandler = (standardItems, type, target) => {
  // standardItems: 标准菜单项数组
  // type: 'blank' | 'node' | 'edge'
  // target: 当前目标对象（节点或边）

  return customizedMenuItems
}
</script>
```

### 完整示例（来自 detail.vue）

```javascript
// 自定义菜单处理器 - 将自定义菜单放在上面，通用菜单放在下面
const customMenuHandler = (standardItems, type, target) => {
  const customItems = []

  if (type === 'node') {
    // 自定义菜单项（放在上面）
    customItems.push(
      {
        id: 'edit-indicator',
        label: '编辑指标',
        icon: 'Edit',
        action: () => handleEditNode(target)
      },
      {
        id: 'copy-indicator',
        label: '复制指标',
        icon: 'DocumentCopy',
        action: () => handleCopyNode(target)
      },
      {
        id: 'delete-indicator',
        label: '删除指标',
        icon: 'Delete',
        action: () => handleDeleteNode(target),
        danger: true
      }
    )

    // 添加分隔线
    customItems.push({ type: 'divider' })

    // 然后添加通用菜单项（过滤掉不需要的）
    const filteredStandardItems = standardItems.filter(
      (item) => item.type === 'divider' || !['delete'].includes(item.id)
    )
    customItems.push(...filteredStandardItems)
  } else if (type === 'blank') {
    // 空白区域的自定义菜单项
    customItems.push({
      id: 'add-indicator',
      label: '添加指标',
      icon: 'Plus',
      action: () => handleAddNode(target)
    })

    // 添加分隔线
    customItems.push({ type: 'divider' })

    // 然后添加通用菜单项
    customItems.push(...standardItems)
  } else {
    // 其他类型（如边）使用标准菜单
    return standardItems
  }

  return customItems
}
```

## 菜单项数据结构

```javascript
const menuItem = {
  id: 'unique-id', // 必填：唯一标识
  label: '菜单文本', // 必填：显示文本
  icon: 'IconName', // 可选：图标名称
  action: () => {}, // 必填：点击回调函数
  shortcut: 'Ctrl+C', // 可选：快捷键提示
  disabled: false, // 可选：是否禁用
  hidden: false, // 可选：是否隐藏
  danger: false // 可选：是否为危险操作（红色显示）
}

// 分割线
const divider = { type: 'divider' }
```

## 标准菜单项 ID 参考

### 空白区域菜单 (type: 'blank')

- `select-all`: 全选
- `paste`: 粘贴
- `zoom-to-fit`: 适应画布
- `zoom-to-actual`: 实际大小
- `clear-canvas`: 清空画布

### 节点菜单 (type: 'node')

- `copy`: 复制
- `delete`: 删除
- `lock`: 锁定/解锁

### 边菜单 (type: 'edge')

- `edit-label`: 编辑标签
- `delete`: 删除连接

## 使用模式

### 1. 完全自定义菜单

```javascript
const customMenuHandler = (standardItems, type, target) => {
  if (type === 'node') {
    return [
      { id: 'custom-1', label: '自定义功能1', action: () => {} },
      { id: 'custom-2', label: '自定义功能2', action: () => {} }
    ]
  }
  return standardItems
}
```

### 2. 自定义菜单 + 过滤标准菜单

```javascript
const customMenuHandler = (standardItems, type, target) => {
  if (type === 'node') {
    const customItems = [{ id: 'edit', label: '编辑', action: () => editNode(target) }]

    // 过滤掉不需要的标准菜单
    const filteredStandard = standardItems.filter((item) => !['delete', 'lock'].includes(item.id))

    return [...customItems, { type: 'divider' }, ...filteredStandard]
  }
  return standardItems
}
```

### 3. 标准菜单 + 自定义菜单

```javascript
const customMenuHandler = (standardItems, type, target) => {
  if (type === 'node') {
    return [
      ...standardItems,
      { type: 'divider' },
      { id: 'info', label: '节点信息', action: () => showNodeInfo(target) }
    ]
  }
  return standardItems
}
```

### 4. 根据节点类型动态菜单

```javascript
const customMenuHandler = (standardItems, type, target) => {
  if (type === 'node') {
    const nodeType = target.getData()?.type

    switch (nodeType) {
      case 'start':
        return [
          { id: 'config-start', label: '配置启动', action: () => {} },
          { type: 'divider' },
          ...standardItems.filter((item) => item.id !== 'delete')
        ]
      case 'end':
        return [
          { id: 'set-output', label: '设置输出', action: () => {} },
          { type: 'divider' },
          ...standardItems
        ]
      default:
        return standardItems
    }
  }
  return standardItems
}
```

## 事件处理

在 `customMenuHandler` 中，你可以直接调用组件方法或发射事件：

```javascript
// 直接调用方法
const handleEditNode = (node) => {
  // 编辑逻辑
}

// 或者发射事件（如果需要）
const emit = defineEmits(['edit-node', 'delete-node'])

const customMenuHandler = (standardItems, type, target) => {
  if (type === 'node') {
    return [
      {
        id: 'edit',
        label: '编辑',
        action: () => {
          handleEditNode(target) // 直接调用
          emit('edit-node', target) // 或发射事件
        }
      }
    ]
  }
  return standardItems
}
```

## 迁移指南

### 从旧的 customMenuItems 迁移

**旧方式：**

```javascript
const customMenuItems = {
  node: [
    {
      id: 'edit',
      label: '编辑',
      position: 'top',
      action: (node) => editNode(node)
    }
  ]
}
```

**新方式：**

```javascript
const customMenuHandler = (standardItems, type, target) => {
  if (type === 'node') {
    return [
      {
        id: 'edit',
        label: '编辑',
        action: () => editNode(target)
      },
      { type: 'divider' },
      ...standardItems
    ]
  }
  return standardItems
}
```

新方式的优势：

- ✅ 完全控制菜单顺序
- ✅ 可以过滤标准菜单项
- ✅ 可以根据目标对象动态生成菜单
- ✅ 更灵活的插入位置控制
- ✅ 更好的类型安全和错误处理
