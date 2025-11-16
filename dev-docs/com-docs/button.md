# ZxButton

## 核心用法
```vue
<zx-button @click="handleClick">按钮</zx-button>
<zx-button :debounce="300" @click="handleClick">防抖</zx-button>
<zx-button :throttle="1000" @click="handleClick">节流</zx-button>
<zx-button @click="asyncHandler">自动 Loading</zx-button>
<zx-button :tooltip="{ content: '提示' }">带提示</zx-button>
```

## Promise 自动 Loading
```typescript
// 返回 Promise 时自动管理 loading 状态
const asyncHandler = async () => {
  await api.save()
  // 成功后自动隐藏 loading
}
```

## 增强 Props
- `debounce` (Number): 防抖延迟(ms)
- `throttle` (Number): 节流延迟(ms)
- `enableLoading` (Boolean, default: true): 启用 Promise 自动 loading
- `tooltip` (Object): 提示配置
- `iconRight` (String): 右侧图标名称
- `iconRightProps` (Object): 右侧图标配置

## Events
- `startLoading`: Promise 开始
- `endLoading`: Promise 结束
- `success`: Promise 成功
- `error(error)`: Promise 失败

## 说明
- 继承 Element Plus Button 所有原生 props: `type`, `size`, `plain`, `loading`, `disabled`, `icon` 等
- click 返回 Promise 时自动显示 loading
- 所有原生 events 透传
