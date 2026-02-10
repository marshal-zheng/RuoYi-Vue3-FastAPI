# VXE-Table 通用校验框架

一个类似 Element Plus 表单验证的 VXE-Table 校验方案，提供统一、可复用的校验能力。

## 特性

- ✅ 类似 Element Plus / async-validator 的规则配置方式
- ✅ 支持字段级别校验（单元格）
- ✅ 支持全局校验器（跨行/跨字段）
- ✅ 支持错误/警告/信息三种级别
- ✅ 内置常用校验器（必填、数字、范围、正则等）
- ✅ 业务校验器（端口、IP、MAC、字节数等）
- ✅ 校验结果可视化（行/单元格高亮）
- ✅ 校验面板组件（展示所有问题）
- ✅ 支持阻断保存流程

## 安装

在 `main.ts` 中全局引入样式：

```ts
import '@/components/VxeTableValidation/validation.less';
```

## 基础用法

```vue
<template>
  <vxe-table
    :data="tableData"
    :row-class-name="getRowClassName"
    :cell-class-name="getCellClassName"
  >
    <!-- 列定义 -->
  </vxe-table>

  <VxeValidationPanel :issues="issues" @issue-click="handleIssueClick" />
</template>

<script setup lang="ts">
import {
  useVxeTableValidation,
  VxeValidationPanel,
  required,
  number,
  range,
} from '@/components/VxeTableValidation';

const tableData = ref([...]);

const {
  validate,
  issues,
  getRowClassName,
  getCellClassName,
} = useVxeTableValidation({
  rules: {
    fieldName: [required('名称不能为空')],
    byteCount: [number(), range(1, 65535, '字节数范围 1-65535')],
  },
  fieldLabels: {
    fieldName: '信息名称',
    byteCount: '字节数',
  },
});

// 保存前校验
const handleSave = async () => {
  const result = await validate(tableData.value);
  if (!result.valid) {
    ElMessage.error(`校验失败：${result.errorCount} 个错误`);
    return;
  }
  // 继续保存...
};
</script>
```

## 阻断保存流程

```ts
// 方式1：使用 validateOrThrow
const handleSave = async () => {
  const result = await validateOrThrow(tableData.value);
  // 如果校验失败会抛出错误，不会执行到这里
  await saveData();
};

// 方式2：使用 validate 手动判断
const handleSave = async () => {
  const result = await validate(tableData.value);
  if (!result.valid) {
    ElMessage.error(`校验失败：${result.errorCount} 个错误`);
    return;
  }
  await saveData();
};

// 方式3：使用 isValid 简化判断
const handleSave = async () => {
  if (!await isValid(tableData.value)) {
    ElMessage.error('请先修正错误');
    return;
  }
  await saveData();
};
```

## 预置规则

```ts
import {
  required,      // 必填
  number,        // 数字类型
  integer,       // 整数
  positiveInteger, // 正整数
  nonNegativeInteger, // 非负整数
  range,         // 数值范围
  lengthRange,   // 长度范围
  length,        // 精确长度
  pattern,       // 正则匹配
  email,         // 邮箱格式
  url,           // URL格式
  oneOf,         // 枚举值
  custom,        // 自定义校验
  warning,       // 警告级别包装
  info,          // 信息级别包装
} from '@/components/VxeTableValidation';
```

## 业务校验器

```ts
import {
  port,          // 端口号 0-65535
  ipAddress,     // IP地址
  macAddress,    // MAC地址
  byteCount,     // 字节数
  scale,         // 比例尺（非零）
} from '@/components/VxeTableValidation';
```

## 全局校验器

```ts
import {
  createBandwidthValidator,    // 带宽校验
  createFrameLengthValidator,  // 帧长度校验
  createValueRangeValidator,   // 数值范围溢出校验
  createUniqueValidator,       // 唯一性校验
} from '@/components/VxeTableValidation';

const { validate, addGlobalValidator } = useVxeTableValidation({...});

// 添加唯一性校验
addGlobalValidator(createUniqueValidator({
  field: 'fieldName',
  fieldLabel: '名称',
}));
```

## API

### useVxeTableValidation(options)

#### Options

| 参数 | 说明 | 类型 | 默认值 |
|------|------|------|--------|
| rules | 字段校验规则 | FieldRules | {} |
| globalValidators | 全局校验器列表 | GlobalValidator[] | [] |
| fieldLabels | 字段标签映射 | Record<string, string> | {} |
| autoValidate | 是否自动校验 | boolean | false |
| autoValidateDelay | 自动校验防抖延迟 | number | 300 |
| context | 校验上下文 | object | {} |
| onValidated | 校验完成回调 | function | - |

#### Returns

| 属性/方法 | 说明 | 类型 |
|-----------|------|------|
| issues | 校验问题列表 | Ref<ValidationIssue[]> |
| errorCount | 错误数量 | ComputedRef<number> |
| warningCount | 警告数量 | ComputedRef<number> |
| hasErrors | 是否有错误 | ComputedRef<boolean> |
| validate | 执行校验 | (data) => Promise<ValidationResult> |
| validateOrThrow | 校验失败抛错误 | (data) => Promise<ValidationResult> |
| isValid | 校验是否通过 | (data) => Promise<boolean> |
| clearValidation | 清除校验结果 | () => void |
| getRowClassName | 行样式类函数 | function |
| getCellClassName | 单元格样式类函数 | function |
| vxeValidConfig | VXE valid-config | object |

### VxeValidationPanel

校验结果面板组件。

#### Props

| 参数 | 说明 | 类型 | 默认值 |
|------|------|------|--------|
| issues | 校验问题列表 | ValidationIssue[] | 必填 |
| title | 面板标题 | string | - |
| alwaysShow | 始终显示 | boolean | false |
| autoExpand | 有问题时自动展开 | boolean | true |
| showSuggestion | 显示修复建议 | boolean | true |
| maxHeight | 最大高度 | string \| number | 240 |

#### Events

| 事件名 | 说明 | 参数 |
|--------|------|------|
| issue-click | 点击问题项 | issue: ValidationIssue |
