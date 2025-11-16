# ZxInput

增强的输入框组件,基于Element Plus Input,增加Tooltip等功能。

## 基础用法

```vue
<!-- 所有Element Plus Input的props都支持 -->
<zx-input v-model="value" placeholder="请输入" />
```

## 带Tooltip

```vue
<!-- 简单文本 -->
<zx-input 
  v-model="value" 
  tooltip="请输入用户名" 
/>

<!-- 完整配置 -->
<zx-input 
  v-model="value"
  :tooltip="{
    content: '用户名长度为3-20个字符',
    title: '用户名规则'
  }"
  tooltip-placement="right"
  tooltip-trigger="focus"
/>
```

## Tooltip配置

```ts
interface InputTooltipConfig {
  content?: string   // 提示内容
  title?: string     // 提示标题(有title时显示为popover)
  trigger?: string   // 触发方式
}
```

## 关键Props

- `v-model`: 绑定值
- `type`: 输入框类型,默认'text'
- `tooltip`: 提示内容,字符串或配置对象
- `tooltip-placement`: 提示位置,默认'right'
- `tooltip-trigger`: 触发方式,默认'hover'

## Element Plus Input原生Props

支持所有el-input的props,通过v-bind="$attrs"透传:
- `placeholder`: 占位文本
- `clearable`: 可清空
- `show-password`: 显示密码切换按钮
- `disabled`: 禁用
- `size`: 尺寸 'large'|'default'|'small'
- `prefix-icon/suffix-icon`: 前后缀图标
- `rows`: 文本域行数
- `autosize`: 自适应高度
- `maxlength`: 最大长度
- `show-word-limit`: 显示字数统计
