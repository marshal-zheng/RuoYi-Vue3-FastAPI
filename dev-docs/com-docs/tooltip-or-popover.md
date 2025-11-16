# ZxTooltipOrPopover

智能Tooltip/Popover组件,根据是否有title自动切换。

## 基础用法

```vue
<!-- 无title时显示为Tooltip -->
<zx-tooltip-or-popover content="这是提示文本">
  <zx-button>Hover me</zx-button>
</zx-tooltip-or-popover>

<!-- 有title时显示为Popover -->
<zx-tooltip-or-popover 
  title="提示标题" 
  content="这是详细内容"
>
  <zx-button>Hover me</zx-button>
</zx-tooltip-or-popover>
```

## 使用content插槽

```vue
<zx-tooltip-or-popover title="自定义内容">
  <template #reference>
    <zx-button>按钮</zx-button>
  </template>
  <template #content>
    <div>自定义HTML内容</div>
    <ul>
      <li>选项1</li>
      <li>选项2</li>
    </ul>
  </template>
</zx-tooltip-or-popover>
```

## 触发方式

```vue
<!-- hover触发(默认) -->
<zx-tooltip-or-popover content="内容" trigger="hover">
  <span>Hover</span>
</zx-tooltip-or-popover>

<!-- click触发 -->
<zx-tooltip-or-popover content="内容" trigger="click">
  <span>Click</span>
</zx-tooltip-or-popover>

<!-- focus触发 -->
<zx-tooltip-or-popover content="内容" trigger="focus">
  <el-input placeholder="Focus me" />
</zx-tooltip-or-popover>
```

## 位置

```vue
<zx-tooltip-or-popover 
  content="内容" 
  placement="top"
>
  <span>Top</span>
</zx-tooltip-or-popover>
<!-- 
placement可选值:
top, top-start, top-end,
bottom, bottom-start, bottom-end,
left, left-start, left-end,
right, right-start, right-end
-->
```

## 控制显示

```vue
<zx-tooltip-or-popover 
  :visible="visible"
  content="内容"
  :persistent="true"
>
  <zx-button @click="visible = !visible">
    Toggle
  </zx-button>
</zx-tooltip-or-popover>

<script setup>
const visible = ref(false)
</script>
```

## Popover宽度

```vue
<!-- 只在Popover模式(有title)时生效 -->
<zx-tooltip-or-popover 
  title="标题"
  content="内容"
  :width="300"
>
  <span>Hover</span>
</zx-tooltip-or-popover>
```

## Props

- `title`: 标题(有title时显示为Popover)
- `content`: 内容文本
- `trigger`: 触发方式 'hover'|'click'|'focus'|'contextmenu',默认'hover'
- `placement`: 位置,默认'top'
- `visible`: 控制显示
- `offset`: 偏移量,默认12
- `hide-after`: 隐藏延迟(ms),默认300
- `show-after`: 显示延迟(ms),默认150
- `width`: Popover宽度(仅Popover模式)
- `enterable`: 鼠标可进入,默认true
- `persistent`: 持久化(仅点击外部关闭),默认false
- `disabled`: 禁用,默认false
- `popper-class`: 自定义popper类名
- `content-class`: 自定义content类名

## Events

- `@show`: 显示时触发
- `@hide`: 隐藏时触发
- `@before-show`: 显示前触发
- `@before-hide`: 隐藏前触发

## Slots

- `default`: 触发元素(无title模式)
- `reference`: 触发元素(有title模式)
- `content`: 自定义内容

## 判断规则

- 无`title`或`title`为空 → Tooltip
- 有`title` → Popover

