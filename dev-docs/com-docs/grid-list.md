# ZxGridList

表格列表组件,集成分页、搜索、加载状态管理。

## 核心用法

```vue
<zx-grid-list :load-data="loadData">
  <template #form="{ query, updateState, refresh }">
    <el-input v-model="query.keyword" @input="updateState('query.keyword', $event)" />
    <el-button @click="refresh()">搜索</el-button>
  </template>
  
  <template #table="{ grid }">
    <el-table :data="grid.list">
      <el-table-column prop="name" label="名称" />
    </el-table>
  </template>
</zx-grid-list>
```

## loadData Promise模式(重点)

```ts
// loadData函数签名
async function loadData(params: {
  query: Record<string, any>,  // 查询条件
  page: number,                // 当前页码
  size: number                 // 每页条数
}): Promise<{
  list: any[],                 // 数据列表
  total: number                // 总条数
}>

// 示例实现
const loadData = async (params) => {
  const res = await api.getList({
    ...params.query,
    page: params.page,
    size: params.size
  })
  return {
    list: res.data,
    total: res.total
  }
}
```

## 关键Props

- `load-data`: (必需) Promise函数,接收{query, page, size},返回{list, total}
- `initial-state`: 初始状态 `{ query: {...}, pager: {page, size} }`
- `show-pagination`: 是否显示分页,默认true
- `load-on-mounted`: 挂载时自动加载,默认true
- `page-from-0`: 页码从0开始,默认false
- `auto-refresh`: 自动刷新配置,默认false

## Slots

- `form`: 搜索表单区域 `{ query, updateState, refresh, data }`
- `table`: 表格区域 `{ grid, loading, refresh, hasData }`
- `empty`: 空状态 `{ refresh }`

## 常用方法(通过ref访问)

```ts
const gridRef = ref()
gridRef.value.refresh()              // 刷新数据
gridRef.value.updateState(key, val)  // 更新状态
gridRef.value.clearTableSelection()  // 清空选择
```

## State结构

```ts
grid.query: Record<string, any>  // 查询条件
grid.pager: { page, size, total } // 分页信息
grid.list: any[]                  // 数据列表
grid.loading: boolean             // 加载状态
```

