# ZxTabs

配置式标签页组件,基于Element Plus Tabs,支持懒加载、拖拽、URL同步等功能。

## 基础用法(配置式)

```vue
<zx-tabs v-model="activeTab" :items="tabItems" />

<script setup>
import UserPanel from './UserPanel.vue'
import OrderPanel from './OrderPanel.vue'

const activeTab = ref('user')

const tabItems = [
  {
    key: 'user',
    label: '用户管理',
    component: UserPanel,
    props: { userId: 123 }
  },
  {
    key: 'order',
    label: '订单管理',
    component: OrderPanel,
    disabled: false
  }
]
</script>
```

## 标签项配置

```ts
interface ZxTabsItem {
  key: string                    // 标签唯一标识(必需)
  label?: string                 // 标签文本
  labelSlot?: Component          // 自定义标签组件
  labelProps?: Record<string, any>
  component?: Component          // 内容组件
  props?: Record<string, any>    // 传给组件的props
  on?: Record<string, Function>  // 事件监听器
  disabled?: boolean             // 是否禁用
  closable?: boolean             // 是否可关闭
  content?: string               // 纯文本内容
}
```

## 懒加载

```vue
<!-- lazy默认为true,只渲染激活的标签页 -->
<zx-tabs :items="items" :lazy="true" />
```

## 拖拽排序

```vue
<zx-tabs :items="items" :draggable="true" />
```

## URL参数同步

```vue
<!-- 激活状态同步到URL参数 ?tab=user -->
<zx-tabs 
  :items="items" 
  :use-url-params="true" 
  param-name="tab" 
/>
```

## 内容过渡动画

```vue
<zx-tabs 
  :items="items" 
  content-transition="fade"  
/>
<!-- 可选: 'fade' | 'slide' | 'none' -->
```

## 关键Props

- `items`: (必需) 标签项配置数组
- `lazy`: 懒加载,默认true
- `draggable`: 可拖拽排序,默认false
- `track-tab-record`: 记录标签状态到sessionStorage,默认true
- `use-url-params`: 使用URL参数同步,默认false
- `param-name`: URL参数名,默认'tab'
- `content-transition`: 内容过渡动画,默认'fade'

## Element Plus Tabs原生Props

支持所有el-tabs的props,通过v-bind="$attrs"透传:
- `v-model`: 当前激活标签的key
- `type`: 标签类型 'card'|'border-card'
- `editable`: 是否可增删
- `tab-position`: 标签位置 'top'|'right'|'bottom'|'left'

