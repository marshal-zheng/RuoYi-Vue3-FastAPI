# DAG矩阵视图功能说明

## 功能概述

DAG矩阵视图是一个通用的图结构转表格视图的功能组件，支持将复杂的图形数据转换为易于编辑和管理的树形表格。该功能特别适用于指标体系、组织架构、流程图等具有层级关系的业务场景。

> 提示：通过新增的别名 `@Dag` 可以直接引用矩阵视图能力，例如 `import { DagMatrixView } from '@Dag'` 或 `import { transformGraphToMatrix } from '@Dag';`

## 核心特性

### 1. 通用性设计

- **数据转换器**：支持图结构 ↔ 树形表格的双向转换
- **自定义渲染**：通过外部渲染器函数定制业务特定的显示逻辑
- **灵活配置**：支持动态列配置、编辑表单组件等

### 2. 交互功能

- **视图切换**：图形视图与矩阵视图一键切换
- **层级展示**：清晰的树形结构展示，支持展开/收起
- **在线编辑**：支持行内编辑、新增、删除节点
- **数据同步**：矩阵视图的修改实时同步到图结构

### 3. 企业级特性

- **加载状态**：完整的加载状态管理
- **错误处理**：友好的错误提示和异常处理
- **操作反馈**：及时的操作成功/失败反馈
- **数据导出**：支持矩阵数据导出功能

## 使用方法

### 1. 基础使用

```vue
<template>
  <DAGPage
    :matrix-columns="matrixColumns"
    :matrix-node-renderer="nodeRenderer"
    :matrix-node-transformer="nodeTransformer"
    :default-view-mode="'matrix'"
    @matrix-node-update="handleNodeUpdate"
  />
</template>

<script setup>
import DAGPage from '@/components/business/Dag/index.vue'

// 列配置
const matrixColumns = [
  {
    prop: 'properties.content.label',
    label: '名称',
    width: 200
  },
  {
    prop: 'properties.content.description',
    label: '描述',
    minWidth: 250
  }
]

// 节点渲染器
const nodeRenderer = (originalNode, treeNode) => {
  return {
    displayName: originalNode.properties?.content?.label || '未命名'
    // 其他自定义字段...
  }
}

// 节点转换器
const nodeTransformer = (treeNode, nodeData) => {
  return {
    properties: {
      content: {
        label: treeNode.displayName
      }
    }
  }
}
</script>
```

### 2. 高级配置

#### 自定义列组件

```vue
<!-- WeightCell.vue -->
<template>
  <div class="weight-cell">
    <el-slider
      v-if="!readonly"
      v-model="currentValue"
      :min="0"
      :max="1"
      :step="0.01"
      @change="handleChange"
    />
    <el-tag v-else :type="getWeightType(currentValue)">
      {{ formatWeight(currentValue) }}
    </el-tag>
  </div>
</template>

<script setup>
const props = defineProps(['row', 'readonly'])
const emit = defineEmits(['update'])

const currentValue = computed({
  get: () => props.row.properties?.indicator?.weight || 0,
  set: (value) => {
    emit('update', {
      rowId: props.row.id,
      prop: 'properties.indicator.weight',
      value
    })
  }
})
</script>
```

#### 列配置使用组件

```javascript
const matrixColumns = [
  {
    prop: 'properties.indicator.weight',
    label: '权重',
    width: 150,
    component: 'WeightCell' // 使用自定义组件
  }
]
```

### 3. 自定义编辑表单

```vue
<!-- CustomEditForm.vue -->
<template>
  <el-form :model="nodeData" @submit.prevent="handleSubmit">
    <!-- 自定义表单项 -->
    <el-form-item label="节点名称">
      <el-input v-model="nodeData.properties.content.label" />
    </el-form-item>

    <div class="form-actions">
      <el-button @click="$emit('cancel')">取消</el-button>
      <el-button type="primary" @click="handleSubmit">确定</el-button>
    </div>
  </el-form>
</template>

<script setup>
const props = defineProps(['nodeData', 'isAdd', 'parentNode'])
const emit = defineEmits(['submit', 'cancel'])

const handleSubmit = () => {
  emit('submit', props.nodeData)
}
</script>
```

### 4. 工具栏与操作列扩展

#### 自定义工具栏

```vue
<DagMatrixView
  :graph-data="graphData"
  :toolbar-actions="{
    primary: [
      { key: 'import', label: '导入', icon: Upload, handler: onImport },
      { key: 'refresh', label: '重新计算', icon: Refresh }
    ],
    toggles: [],
    right: [
      { key: 'custom-tip', label: ({ totalNodes }) => `已选 ${totalNodes} 项`, type: 'success' }
    ]
  }"
  @toolbar-action="({ action, context }) => console.log(action.key, context)"
/>
```

#### 自定义操作列

```vue
<DagMatrixView
  :graph-data="graphData"
  :operation-actions="[
    {
      key: 'duplicate',
      label: '复制',
      icon: CopyDocument,
      handler: ({ row }) => duplicateNode(row)
    },
    {
      key: 'audit',
      label: '送审',
      type: 'warning',
      disabled: ({ row }) => row.status !== 'draft',
      handler: ({ row }) => emit('submit-audit', row)
    }
  ]"
  @operation-action="({ action, context }) => console.log(action.key, context.row)"
>
  <template #operation="{ row, execute }">
    <el-link type="primary" @click="execute({ key: 'view', handler: () => openPreview(row) })">
      查看
    </el-link>
  </template>
</DagMatrixView>
```

#### 自定义节点工厂

```js
const nodeFactories = {
  createRootNode: () => ({
    type: 'root-node',
    properties: { content: { label: '新的维度' } }
  }),
  createChildNode: ({ parent }) => ({
    type: parent.type,
    properties: { content: { label: `${parent.properties.content.label}-子项` } }
  })
}
```

```vue
<DagMatrixView :node-factories="nodeFactories" />
```

工具栏提供 `toolbar` 插槽、操作列提供 `operation` 插槽，两者都会透出 `actions` 列表和 `execute(action)` 方法，便于在默认能力基础上进行自由拼装。

## API 参考

### DAGPage Props

| 属性 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `matrixColumns` | Array | `[]` | 矩阵视图列配置 |
| `matrixNodeRenderer` | Function | `null` | 节点数据渲染器 |
| `matrixNodeTransformer` | Function | `null` | 节点数据转换器 |
| `matrixEditFormComponent` | String/Object | `null` | 编辑表单组件 |
| `defaultViewMode` | String | `'graph'` | 默认视图模式 |
| `matrixToolbarActions` | Object | `{}` | 透传工具栏配置，等同于 `DagMatrixView` 的 `toolbar-actions` |
| `matrixOperationActions` | Array | `null` | 自定义操作列动作，等同于 `DagMatrixView` 的 `operation-actions` |
| `matrixNodeFactories` | Object | `{}` | 自定义节点工厂，等同于 `DagMatrixView` 的 `node-factories` |

### DagMatrixView Props

| 属性 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `toolbarActions` | Object | `{ primary: [...], toggles: [...], right: [...] }` | 自定义工具栏按钮、分组与统计信息 |
| `operationActions` | Array \| null | `null` | 操作列按钮定义，`null` 时使用默认增删改 |
| `nodeFactories` | Object | `{}` | 自定义 `createRootNode`/`createChildNode` 逻辑 |
| `nodeTypeIcons` | Object | `{ root-node: Folder, sub-node: Connection, leaf-node: Document }` | 自定义类型与图标映射 |
| `levelColumnLabel` | String | `'层级结构'` | 层级列标题 |
| `levelColumnMinWidth` | Number | `200` | 层级列最小宽度 |
| `operationColumnLabel` | String | `'操作'` | 操作列标题 |
| `operationColumnWidth` | Number \| null | `200` | 操作列基础宽度（会根据动作数量自动放大） |

### 列配置 (Column Config)

```javascript
{
  prop: 'properties.content.label',    // 数据属性路径
  label: '列标题',                      // 列标题
  width: 200,                          // 固定宽度
  minWidth: 150,                       // 最小宽度
  fixed: 'left',                       // 固定列位置
  sortable: true,                      // 是否可排序
  component: 'CustomComponent',        // 自定义组件
  render: (row, column, index) => {},  // 自定义渲染函数
  showOverflowTooltip: true           // 是否显示溢出提示
}
```

### 事件

| 事件名               | 参数                     | 说明                                      |
| -------------------- | ------------------------ | ----------------------------------------- |
| `matrix-node-add`    | `nodeData`               | 添加节点                                  |
| `matrix-node-update` | `nodeData`               | 更新节点                                  |
| `matrix-node-delete` | `nodeData`               | 删除节点                                  |
| `matrix-row-click`   | `{ row, column, event }` | 行点击                                    |
| `view-mode-change`   | `mode`                   | 视图模式切换                              |
| `toolbar-action`     | `{ action, context }`    | 工具栏按钮回调（未提供 `handler` 时触发） |
| `operation-action`   | `{ action, context }`    | 操作列按钮回调（未提供 `handler` 时触发） |

### 插槽

| 名称 | 作用 | 说明 |
| --- | --- | --- |
| `toolbar` | 替换工具栏 | 透出 `actions`、`execute(action)`、`context`、`total` |
| `operation` | 重绘操作列 | 透出 `row`、`column`、`index`、`actions`、`execute(action)`、`context` |

## 业务示例

### 指标体系管理

```vue
<template>
  <DAGPage
    :matrix-columns="indicatorColumns"
    :matrix-node-renderer="indicatorRenderer"
    :matrix-edit-form-component="IndicatorEditForm"
    @matrix-node-update="saveIndicator"
  />
</template>

<script setup>
// 指标专用列配置
const indicatorColumns = [
  { prop: 'properties.content.label', label: '指标名称', width: 200 },
  { prop: 'properties.indicator.weight', label: '权重', width: 100, component: 'WeightSlider' },
  { prop: 'properties.indicator.unit', label: '单位', width: 80 },
  { prop: 'properties.indicator.formula', label: '计算公式', minWidth: 200 },
  { prop: 'properties.indicator.dataSource', label: '数据来源', width: 120 }
]

// 指标数据渲染
const indicatorRenderer = (node, treeNode) => ({
  weightPercent: `${(node.properties?.indicator?.weight * 100).toFixed(1)}%`,
  status: getIndicatorStatus(node),
  isKey: node.properties?.indicator?.weight > 0.5
})
</script>
```

### 组织架构管理

```vue
<template>
  <DAGPage
    :matrix-columns="orgColumns"
    :matrix-node-renderer="orgRenderer"
    :matrix-edit-form-component="OrgEditForm"
  />
</template>

<script setup>
const orgColumns = [
  { prop: 'properties.content.label', label: '部门名称', width: 200 },
  { prop: 'properties.org.manager', label: '负责人', width: 120 },
  { prop: 'properties.org.employeeCount', label: '人员数量', width: 100 },
  { prop: 'properties.org.location', label: '办公地点', width: 150 }
]
</script>
```

## 最佳实践

### 1. 性能优化

- 大数据量时建议使用虚拟滚动
- 合理使用 `showOverflowTooltip` 避免内容溢出
- 自定义组件应该做好防抖处理

### 2. 用户体验

- 提供清晰的层级视觉指示
- 重要操作添加确认对话框
- 加载状态和错误提示要及时准确

### 3. 数据管理

- 确保数据转换的一致性
- 做好数据验证和异常处理
- 重要数据变更要有操作日志

## 扩展开发

如需扩展功能，可以：

1. **自定义列组件**：实现 `props: ['row', 'readonly']` 和 `emits: ['update']`
2. **自定义编辑表单**：实现 `props: ['nodeData', 'isAdd', 'parentNode']` 和 `emits: ['submit', 'cancel']`
3. **数据转换器**：根据业务需求实现节点数据的双向转换逻辑
4. **样式定制**：通过CSS变量或深度选择器定制视觉效果

## 技术实现

- **数据转换**：`utils/matrixDataTransform.js`
- **矩阵视图**：`components/DagMatrixView.vue`
- **主组件集成**：`index.vue`
- **示例代码**：`examples/` 目录

这个矩阵视图功能充分体现了通用性与业务特定性的平衡，既提供了强大的基础能力，又允许业务方根据具体需求进行灵活定制。
