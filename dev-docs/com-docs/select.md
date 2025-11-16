# ZxSelect

## 核心用法
```vue
<zx-select v-model="value" :options="options" />
<zx-select v-model="value" :options="loadOptions" remote />
<zx-select v-model="value" v-model:entity="selectedEntity" :options="options" />
```

## Options 配置
```typescript
// 静态数组
const options = [
  { label: '选项1', value: 1 },
  { label: '选项2', value: 2, disabled: true }
]

// 动态加载函数
const loadOptions = async (keyword?: string) => {
  const { data } = await api.search(keyword)
  return data.map(item => ({ label: item.name, value: item.id }))
}
```

## 关键 Props
- `modelValue`: 绑定值
- `entity`: 绑定选中的完整对象（支持 v-model:entity）
- `options` (Array | Function): 选项数据或加载函数
- `remote` (Boolean): 是否远程搜索
- `valueKey` (String, default: 'value'): 值字段名
- `labelKey` (String, default: 'label'): 标签字段名
- `objectValue` (Boolean): 值是否为对象
- `hasAllSelect` (Boolean): 显示"全选"选项
- `defaultFirst` (Boolean): 默认选择第一项
- `searchKeys` (Array, default: ['label']): 搜索字段
- `transform` (Function): 数据转换函数
- `tooltip` (Object): 提示配置 `{ content, placement }`

## Events
- `change`: 值变化
- `select`: 选中
- `options-loaded`: 选项加载完成
- `visible-change`: 下拉框显示变化
- `remove`: 移除标签(多选)
- `clear`: 清空
