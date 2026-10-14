import type { VxeTableDefines } from 'vxe-table';

export type ValidationRow = Record<string, unknown>;

/**
 * VXE-Table 通用校验框架 - 类型定义
 * 设计理念：类似 Element Plus / async-validator 的规则配置方式
 */

/** 校验级别 */
export type ValidationLevel = 'error' | 'warning' | 'info';

/** 校验触发时机 */
export type ValidationTrigger = 'change' | 'blur' | 'manual';

/** 校验规则基础类型 */
export interface ValidationRule<Row extends object = ValidationRow> {
  /** 是否必填 */
  required?: boolean;
  /** 错误消息 */
  message?: string | ((value: unknown, row: Row) => string);
  /** 校验级别，默认 error */
  level?: ValidationLevel;
  /** 触发时机 */
  trigger?: ValidationTrigger | ValidationTrigger[];
  /** 数据类型校验 */
  type?:
    | 'string'
    | 'number'
    | 'integer'
    | 'float'
    | 'boolean'
    | 'array'
    | 'object'
    | 'date'
    | 'url'
    | 'email';
  /** 最小值（数字）或最小长度（字符串/数组） */
  min?: number;
  /** 最大值（数字）或最大长度（字符串/数组） */
  max?: number;
  /** 精确长度 */
  len?: number;
  /** 正则表达式 */
  pattern?: RegExp | string;
  /** 枚举值，值必须在列表中 */
  enum?: unknown[];
  /** 自定义校验器 */
  validator?: ValidatorFunction<Row>;
  /** 异步校验器 */
  asyncValidator?: AsyncValidatorFunction<Row>;
  /** 转换函数，校验前先转换值 */
  transform?: (value: unknown) => unknown;
  /** 条件校验：只在条件满足时才校验 */
  when?: (row: Row, index: number) => boolean;
}

/** 校验器函数 */
export type ValidatorFunction<Row extends object = ValidationRow> = (
  value: unknown,
  row: Row,
  index: number,
  field: string
) => boolean | string | void;

/** 异步校验器函数 */
export type AsyncValidatorFunction<Row extends object = ValidationRow> = (
  value: unknown,
  row: Row,
  index: number,
  field: string
) => Promise<boolean | string | void>;

/** 字段校验规则配置 */
export type FieldRules<Row extends object = ValidationRow> = Record<
  string,
  ValidationRule<Row> | ValidationRule<Row>[]
>;

/** 全局校验器（跨行/跨字段校验） */
export interface GlobalValidator<
  Row extends object = ValidationRow,
  Context extends object = ValidationContext,
> {
  /** 校验器名称 */
  name: string;
  /** 校验器函数 */
  validator: (
    data: Row[],
    context?: Partial<Context>
  ) => ValidationIssue | ValidationIssue[] | null;
  /** 校验级别 */
  level?: ValidationLevel;
}

/** 校验上下文 */
export interface ValidationContext {
  /** 额外数据，业务可自定义 */
  [key: string]: unknown;
}

/** 校验问题项 */
export interface ValidationIssue {
  /** 校验级别 */
  level: ValidationLevel;
  /** 行索引，-1 表示全局问题 */
  rowIndex: number;
  /** 字段名 */
  field: string;
  /** 字段显示名称 */
  fieldLabel?: string;
  /** 错误消息 */
  message: string;
  /** 原始值 */
  value?: unknown;
  /** 修复建议 */
  suggestion?: string;
  /** 规则名称（用于调试） */
  ruleName?: string;
}

/** 校验结果 */
export interface ValidationResult {
  /** 是否校验通过 */
  valid: boolean;
  /** 错误数量 */
  errorCount: number;
  /** 警告数量 */
  warningCount: number;
  /** 信息数量 */
  infoCount: number;
  /** 所有问题 */
  issues: ValidationIssue[];
  /** 按行索引分组的问题 */
  issuesByRow: Map<number, ValidationIssue[]>;
  /** 按字段分组的问题（key: rowIndex-field） */
  issuesByCell: Map<string, ValidationIssue[]>;
}

/** VXE-Table edit-rules 配置项 */
export type VxeEditRule<Row extends object = ValidationRow> = VxeTableDefines.ValidatorRule<Row>;

/** useVxeTableValidation 配置 */
export interface UseVxeTableValidationOptions<
  Row extends object = ValidationRow,
  Context extends object = ValidationContext,
> {
  /** 字段校验规则 */
  rules?: FieldRules<Row>;
  /** 全局校验器列表 */
  globalValidators?: GlobalValidator<Row, Context>[];
  /** 字段标签映射（用于显示友好名称） */
  fieldLabels?: Record<string, string>;
  /** 是否自动校验（编辑后自动触发） */
  autoValidate?: boolean;
  /** 自动校验防抖延迟（毫秒） */
  autoValidateDelay?: number;
  /** 校验上下文 */
  context?: Partial<Context>;
  /** 校验完成回调 */
  onValidated?: (result: ValidationResult) => void;
}

/** 字段列配置（用于从 VXE-Table 列配置中提取校验规则） */
export interface FieldColumnConfig {
  field: string;
  title?: string;
  editRender?: VxeTableDefines.ColumnOptions['editRender'];
  // 扩展：支持直接在列配置中定义校验规则
  validationRules?: ValidationRule | ValidationRule[];
}
