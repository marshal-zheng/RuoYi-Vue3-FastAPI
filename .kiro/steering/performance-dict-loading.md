---
title: 字典数据加载性能规范
category: performance
tags: [frontend, vue3, optimization, dict, lazy-loading]
inclusion: fileMatch
fileMatchPattern: "**/*.vue"
priority: high
---

# 字典数据加载性能规范

## 概述

本规范定义了在 Vue 3 组件中使用 `useDict` 加载字典数据的最佳实践，避免不必要的 API 请求，提升应用性能和用户体验。

## 核心原则

### 1. 延迟加载原则（Lazy Loading）

**规则**: 字典数据应该在真正需要时才加载，而不是在组件定义时立即加载。

**原因**:
- 避免页面加载时发起大量不必要的 API 请求
- 减少首屏加载时间
- 降低服务器压力
- 提升用户体验

### 2. 条件渲染组件的字典加载

**适用场景**: Dialog、Drawer、Popover 等条件渲染的组件

**错误示例** ❌:
```vue
<script setup>
import { useDict } from '@/utils/dict'

// ❌ 错误：组件定义时立即调用，即使 Dialog 未打开
const { sys_normal_disable } = useDict('sys_normal_disable')
</script>
```

**正确示例** ✅:
```vue
<script setup>
import { ref } from 'vue'
import { useDialog } from '@zxio/zxui'
import { useDict } from '@/utils/dict'

// ✅ 正确：声明响应式变量
const sysNormalDisable = ref([])
let dictLoaded = false

const dialog = useDialog({
  onOpen: () => {
    // ✅ 正确：在 Dialog 打开时加载字典
    if (!dictLoaded) {
      const dict = useDict('sys_normal_disable')
      sysNormalDisable.value = dict.sys_normal_disable?.value || []
      dictLoaded = true
    }
  }
})
</script>
```

## 实施指南

### 步骤 1: 识别需要优化的组件

检查以下类型的组件：
- ✅ Dialog 组件（使用 `useDialog`）
- ✅ Drawer 组件（使用 `useDrawer`）
- ✅ Popover/Tooltip 等弹出层组件
- ✅ 条件渲染的表单组件（`v-if` 控制显示）
- ⚠️ 动态组件（`<component :is="...">`）- 需要评估是否真正延迟加载

### 步骤 2: 重构模式

#### 模式 A: 单个字典加载

```vue
<script setup>
import { ref } from 'vue'
import { useDialog } from '@zxio/zxui'
import { useDict } from '@/utils/dict'

// 1. 声明响应式变量
const sysNormalDisable = ref([])
let dictLoaded = false

// 2. 在 onOpen 回调中加载
const dialog = useDialog({
  onOpen: () => {
    if (!dictLoaded) {
      const dict = useDict('sys_normal_disable')
      // 注意：使用原始字典类型名（下划线格式），不是 camelCase
      sysNormalDisable.value = dict.sys_normal_disable?.value || []
      dictLoaded = true
    }
  }
})
</script>

<template>
  <ZxDialog v-bind="dialog.dialogProps.value">
    <el-select v-model="formData.status">
      <el-option
        v-for="item in sysNormalDisable"
        :key="item.value"
        :label="item.label"
        :value="item.value"
      />
    </el-select>
  </ZxDialog>
</template>
```

#### 模式 B: 多个字典加载

```vue
<script setup>
import { ref } from 'vue'
import { useDialog } from '@zxio/zxui'
import { useDict } from '@/utils/dict'

// 1. 声明多个响应式变量
const sysNoticeStatus = ref([])
const sysNoticeType = ref([])
let dictLoaded = false

// 2. 在 onOpen 回调中批量加载
const dialog = useDialog({
  onOpen: () => {
    if (!dictLoaded) {
      const dict = useDict('sys_notice_status', 'sys_notice_type')
      sysNoticeStatus.value = dict.sys_notice_status?.value || []
      sysNoticeType.value = dict.sys_notice_type?.value || []
      dictLoaded = true
    }
  }
})
</script>
```

#### 模式 C: 合并已有 onOpen 逻辑

```vue
<script setup>
import { ref } from 'vue'
import { useDrawer } from '@zxio/zxui'
import { useDict } from '@/utils/dict'

const sysNormalDisable = ref([])
let dictLoaded = false

const drawer = useDrawer({
  onOpen: (data) => {
    // 加载字典（只加载一次）
    if (!dictLoaded) {
      const dict = useDict('sys_normal_disable')
      sysNormalDisable.value = dict.sys_normal_disable?.value || []
      dictLoaded = true
    }
    
    // 其他已有的 onOpen 逻辑
    if (data?.id) {
      loadDetailData(data.id)
    }
  }
})
</script>
```

### 步骤 3: 关键注意事项

#### ⚠️ 字典键名格式

`useDict` 返回的对象使用**原始字典类型名**（下划线格式），不是 camelCase：

```typescript
// ✅ 正确
const dict = useDict('sys_normal_disable')
const data = dict.sys_normal_disable?.value || []

// ❌ 错误
const data = dict.sysNormalDisable?.value || []  // undefined!
```

#### ⚠️ 可选链和默认值

始终使用可选链和默认值，防止运行时错误：

```typescript
// ✅ 正确：使用可选链和默认值
sysNormalDisable.value = dict.sys_normal_disable?.value || []

// ❌ 错误：可能导致运行时错误
sysNormalDisable.value = dict.sys_normal_disable.value
```

#### ⚠️ 加载标志位

使用 `dictLoaded` 标志位确保字典只加载一次：

```typescript
let dictLoaded = false

const dialog = useDialog({
  onOpen: () => {
    if (!dictLoaded) {  // ✅ 防止重复加载
      const dict = useDict('sys_normal_disable')
      sysNormalDisable.value = dict.sys_normal_disable?.value || []
      dictLoaded = true
    }
  }
})
```

## 不需要优化的场景

### 场景 1: 页面级组件

如果组件本身就是页面级别，会立即渲染，可以在顶层调用：

```vue
<script setup>
// ✅ 可以接受：页面组件立即渲染
const { sys_normal_disable } = useDict('sys_normal_disable')
</script>
```

### 场景 2: 真正的条件渲染保护

如果组件通过 `v-if` 条件渲染，且条件依赖运行时数据：

```vue
<template>
  <!-- ✅ 可以接受：组件不会立即挂载 -->
  <ProtocolTemplate
    v-if="currentProtocolType"
    :protocol-type="currentProtocolType"
  />
</template>

<script setup>
// 在 ProtocolTemplate 组件内部
const { sys_protocol_type } = useDict('sys_protocol_type')
// 因为父组件的 v-if 保护，这个组件不会立即挂载
</script>
```

### 场景 3: 小型选择器组件

对于小型、频繁使用的选择器组件（如 `DictSelect`），可以在顶层加载：

```vue
<script setup>
// ✅ 可以接受：这是一个通用选择器组件，会被频繁使用
const { [props.dictType]: dictData } = useDict(props.dictType)
</script>
```

## 检查清单

在提交代码前，检查以下项目：

- [ ] 所有 Dialog 组件的 `useDict` 调用已移至 `onOpen` 回调
- [ ] 所有 Drawer 组件的 `useDict` 调用已移至 `onOpen` 回调
- [ ] 使用了正确的字典键名格式（下划线格式）
- [ ] 使用了可选链和默认值（`?.value || []`）
- [ ] 添加了 `dictLoaded` 标志位防止重复加载
- [ ] 在浏览器 Network 面板验证了优化效果

## 验证方法

### 开发环境验证

1. 打开浏览器开发者工具 → Network 面板
2. 过滤 XHR/Fetch 请求
3. 刷新页面
4. **预期结果**: 不应该看到字典相关的 API 请求（如 `/system/dict/data/type/*`）
5. 打开 Dialog/Drawer
6. **预期结果**: 此时才应该看到字典 API 请求

### 性能指标

优化前后对比：
- **首屏请求数**: 减少 N 个字典请求（N = 优化的组件数 × 每个组件的字典数）
- **首屏加载时间**: 减少 50-200ms（取决于网络延迟）
- **用户体验**: 页面响应更快，无不必要的网络活动

## 已完成的优化案例

以下组件已按此规范完成优化（参考 `DICT_LOADING_FIX.md`）：

1. ✅ `DictDlg.vue` - 字典类型对话框
2. ✅ `NoticeDlg.vue` - 通知对话框
3. ✅ `DeptDlg.vue` - 部门对话框
4. ✅ `PostDlg.vue` - 岗位对话框
5. ✅ `ConfigDlg.vue` - 配置对话框
6. ✅ `OperlogDetailDialog.vue` - 操作日志详情对话框

## 相关文档

- [DICT_LOADING_FIX.md](../../../DICT_LOADING_FIX.md) - 优化实施记录
- [useDict 工具函数](../../../ruoyi-fastapi-frontend/src/utils/dict.ts)
- [ZXUI Dialog 文档](https://zxui.example.com/components/dialog)
- [ZXUI Drawer 文档](https://zxui.example.com/components/drawer)

## 常见问题

### Q1: 为什么不在 `watch` 中加载字典？

**A**: `watch` 会在每次依赖变化时触发，可能导致重复加载。`onOpen` 回调配合 `dictLoaded` 标志位更可控。

### Q2: 如果字典数据需要根据表单数据动态变化怎么办？

**A**: 这种情况下可以使用 `watch`，但要注意防抖和去重：

```typescript
watch(() => formData.category, (newCategory) => {
  if (newCategory) {
    const dict = useDict(`sys_${newCategory}_type`)
    categoryTypes.value = dict[`sys_${newCategory}_type`]?.value || []
  }
}, { immediate: false })
```

### Q3: 动态组件（`<component :is="...">`）需要优化吗？

**A**: 需要评估。如果动态组件的 `is` 属性依赖运行时数据（如用户选择），则组件不会立即挂载，可以不优化。如果 `is` 属性在组件定义时就确定，则需要优化。

### Q4: 如何处理多个 Dialog 共享同一个字典？

**A**: 可以考虑在父组件加载字典，通过 props 传递：

```vue
<!-- 父组件 -->
<script setup>
const { sys_normal_disable } = useDict('sys_normal_disable')
</script>

<template>
  <Dialog1 :status-options="sys_normal_disable" />
  <Dialog2 :status-options="sys_normal_disable" />
</template>
```

## 总结

遵循本规范可以：
- ✅ 减少不必要的 API 请求
- ✅ 提升页面加载性能
- ✅ 改善用户体验
- ✅ 降低服务器负载
- ✅ 保持代码一致性和可维护性

**记住**: 延迟加载不是过度优化，而是性能优化的基本原则。在条件渲染的组件中，始终在 `onOpen` 回调中加载字典数据。
