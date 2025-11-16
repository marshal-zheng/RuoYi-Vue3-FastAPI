# ZxSearch

搜索框组件。

## 基础用法

```vue
<!-- 点击搜索模式 -->
<zx-search 
  v-model="keyword"
  placeholder="请输入关键词"
  @search="handleSearch"
/>

<!-- 输入搜索模式(实时搜索) -->
<zx-search 
  v-model="keyword"
  search-mode="input"
  :search-delay="300"
  @search="handleSearch"
/>

<script setup>
function handleSearch({ value, mode }) {
  console.log('搜索:', value, '模式:', mode)
}
</script>
```

## Props

- `model-value`: v-model绑定值
- `placeholder`: 占位文本
- `search-mode`: 搜索模式 `'click' | 'input'`, 默认'click'
- `search-delay`: 输入搜索延迟(ms),默认300
- `show-search-button`: 显示搜索按钮,默认true
- `show-prefix-icon`: 显示前缀图标,默认true
- `clearable`: 可清空,默认true
- `loading`: 加载状态
- `disabled`: 禁用状态
- `size`: 尺寸

## 事件

- `@search`: 搜索事件 `({ value, mode }) => void`
- `@clear`: 清空事件
- `@input`: 输入事件 `(value) => void`
- `@update:model-value`: 值变化

## 搜索模式说明

- `click`: 点击按钮或回车触发搜索
- `input`: 输入时自动触发搜索(带防抖)

