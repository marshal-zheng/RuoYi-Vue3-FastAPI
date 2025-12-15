/**
 * VXE-Table 通用校验框架
 *
 * 提供类似 Element Plus 表单验证的统一校验方案
 *
 * @example 基础用法
 * ```ts
 * import {
 *   useVxeTableValidation,
 *   VxeValidationPanel,
 *   required,
 *   number,
 *   range,
 * } from '@/components/VxeTableValidation';
 *
 * const { validate, validateOrThrow, issues, getRowClassName, getCellClassName } = useVxeTableValidation({
 *   rules: {
 *     fieldName: [required('名称不能为空')],
 *     byteCount: [number(), range(1, 65535, '字节数范围 1-65535')],
 *   },
 *   fieldLabels: {
 *     fieldName: '信息名称',
 *     byteCount: '字节数',
 *   },
 * });
 * ```
 *
 * @example 阻断保存流程
 * ```ts
 * const handleSave = async () => {
 *   try {
 *     // 方式1：使用 validateOrThrow，校验失败自动抛出错误
 *     await validateOrThrow(tableData.value);
 *     await saveData();
 *   } catch (e) {
 *     if (e.isValidationError) {
 *       ElMessage.error(e.message);
 *       return;
 *     }
 *     throw e;
 *   }
 *
 *   // 方式2：使用 validate 手动判断
 *   const result = await validate(tableData.value);
 *   if (!result.valid) {
 *     ElMessage.error(`校验失败：${result.errorCount} 个错误`);
 *     return;
 *   }
 *   await saveData();
 *
 *   // 方式3：使用 isValid 简化判断
 *   if (!await isValid(tableData.value)) {
 *     ElMessage.error('请先修正错误');
 *     return;
 *   }
 *   await saveData();
 * };
 * ```
 */

// ==================== 核心导出 ====================

// Composable
export { useVxeTableValidation } from './useVxeTableValidation';
export type { UseVxeTableValidationReturn } from './useVxeTableValidation';

// 类型
export type {
  ValidationLevel,
  ValidationTrigger,
  ValidationRule,
  ValidatorFunction,
  AsyncValidatorFunction,
  FieldRules,
  GlobalValidator,
  ValidationContext,
  ValidationIssue,
  ValidationResult,
  UseVxeTableValidationOptions,
  VxeEditRule,
  FieldColumnConfig,
} from './types';

// ==================== 校验器导出 ====================

export {
  // 工具函数
  isEmpty,
  parseNumber,  // 解析数值
  getLength,
  validateByRule,

  // 预置规则工厂
  required,
  number,
  integer,
  positiveInteger,
  nonNegativeInteger,
  range,
  lengthRange,
  length,
  pattern,
  email,
  url,
  oneOf,
  custom,
  warning,
  info,

  // 业务校验器
  port,
  ipAddress,
  macAddress,
  byteCount,
  scale,

  // 全局校验器工厂
  createBandwidthValidator,
  createFrameLengthValidator,
  createValueRangeValidator,
  createUniqueValidator,
} from './validators';

// ==================== 组件导出 ====================

export { default as VxeValidationPanel } from './VxeValidationPanel.vue';

// ==================== 样式导出 ====================

// 在 main.ts 中引入：import '@/components/VxeTableValidation/validation.less';
