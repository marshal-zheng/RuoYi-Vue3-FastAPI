/**
 * VXE-Table 通用校验框架 - 核心 Composable
 *
 * 使用方式类似 Element Plus 表单验证：
 *
 * ```ts
 * const { validate, issues, getRowClassName, getCellClassName } = useVxeTableValidation({
 *   rules: {
 *     fieldName: [{ required: true, message: '名称不能为空' }],
 *     byteCount: [{ type: 'integer', min: 1, message: '必须是正整数' }]
 *   },
 *   fieldLabels: {
 *     fieldName: '信息名称',
 *     byteCount: '字节数'
 *   }
 * });
 * ```
 */

import { ref, computed, watch, shallowRef, type Ref, type ComputedRef } from 'vue';
import type {
  ValidationRule,
  FieldRules,
  GlobalValidator,
  ValidationIssue,
  ValidationResult,
  ValidationContext,
  UseVxeTableValidationOptions,
  VxeEditRule,
  ValidationLevel,
} from './types';
import { validateByRule, isEmpty } from './validators';

/** 防抖函数 */
const debounce = <T extends (...args: any[]) => any>(fn: T, delay: number) => {
  let timer: ReturnType<typeof setTimeout> | null = null;
  return (...args: Parameters<T>) => {
    if (timer) clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
};

/**
 * VXE-Table 校验 Composable
 */
export function useVxeTableValidation<T = any>(options: UseVxeTableValidationOptions = {}) {
  const {
    rules = {},
    globalValidators = [],
    fieldLabels = {},
    autoValidate = false,
    autoValidateDelay = 300,
    context: initialContext = {},
    onValidated,
  } = options;

  // ==================== 状态 ====================

  /** 校验问题列表 */
  const issues = ref<ValidationIssue[]>([]);

  /** 当前校验规则 */
  const currentRules = shallowRef<FieldRules>(rules);

  /** 当前全局校验器 */
  const currentGlobalValidators = shallowRef<GlobalValidator[]>(globalValidators);

  /** 校验上下文 */
  const validationContext = ref<ValidationContext>(initialContext);

  /** 是否正在校验 */
  const validating = ref(false);

  // ==================== 计算属性 ====================

  /** 错误数量 */
  const errorCount = computed(() => issues.value.filter((i) => i.level === 'error').length);

  /** 警告数量 */
  const warningCount = computed(() => issues.value.filter((i) => i.level === 'warning').length);

  /** 信息数量 */
  const infoCount = computed(() => issues.value.filter((i) => i.level === 'info').length);

  /** 是否有问题 */
  const hasIssues = computed(() => issues.value.length > 0);

  /** 是否有错误 */
  const hasErrors = computed(() => errorCount.value > 0);

  /** 按行索引分组的问题 */
  const issuesByRow = computed(() => {
    const map = new Map<number, ValidationIssue[]>();
    issues.value.forEach((issue) => {
      if (issue.rowIndex >= 0) {
        const list = map.get(issue.rowIndex) || [];
        list.push(issue);
        map.set(issue.rowIndex, list);
      }
    });
    return map;
  });

  /** 按单元格分组的问题（key: rowIndex-field） */
  const issuesByCell = computed(() => {
    const map = new Map<string, ValidationIssue[]>();
    issues.value.forEach((issue) => {
      if (issue.rowIndex >= 0 && issue.field) {
        const key = `${issue.rowIndex}-${issue.field}`;
        const list = map.get(key) || [];
        list.push(issue);
        map.set(key, list);
      }
    });
    return map;
  });

  /** 全局问题（rowIndex = -1） */
  const globalIssues = computed(() => issues.value.filter((i) => i.rowIndex === -1));

  // ==================== 核心方法 ====================

  /**
   * 执行校验
   * @param data 要校验的数据
   * @param ctx 校验上下文
   * @returns 校验结果
   */
  const validate = async (data: T[], ctx?: ValidationContext): Promise<ValidationResult> => {
    validating.value = true;
    const allIssues: ValidationIssue[] = [];
    const mergedContext = { ...validationContext.value, ...ctx };

    // 1. 字段规则校验
    if (Array.isArray(data)) {
      data.forEach((row, rowIndex) => {
        Object.entries(currentRules.value).forEach(([field, fieldRules]) => {
          const rulesArray = Array.isArray(fieldRules) ? fieldRules : [fieldRules];
          const value = (row as any)[field];

          rulesArray.forEach((rule, ruleIndex) => {
            const errorMsg = validateByRule(value, rule, row, rowIndex, field);
            if (errorMsg) {
              allIssues.push({
                level: rule.level || 'error',
                rowIndex,
                field,
                fieldLabel: fieldLabels[field] || field,
                message: errorMsg,
                value,
                ruleName: `${field}[${ruleIndex}]`,
              });
            }
          });
        });
      });
    }

    // 2. 全局校验器
    for (const validator of currentGlobalValidators.value) {
      const result = validator.validator(data as any[], mergedContext);
      if (result) {
        const resultArray = Array.isArray(result) ? result : [result];
        resultArray.forEach((issue) => {
          allIssues.push({
            ...issue,
            level: issue.level || validator.level || 'error',
            ruleName: validator.name,
          });
        });
      }
    }

    // 3. 异步校验器（如果有的话）
    // TODO: 支持异步校验

    // 更新状态
    issues.value = allIssues;
    validating.value = false;

    // 构建结果
    const result: ValidationResult = {
      valid: allIssues.filter((i) => i.level === 'error').length === 0,
      errorCount: allIssues.filter((i) => i.level === 'error').length,
      warningCount: allIssues.filter((i) => i.level === 'warning').length,
      infoCount: allIssues.filter((i) => i.level === 'info').length,
      issues: allIssues,
      issuesByRow: issuesByRow.value,
      issuesByCell: issuesByCell.value,
    };

    // 回调
    onValidated?.(result);

    return result;
  };

  /**
   * 校验并在失败时抛出错误（用于阻断保存流程）
   * @param data 要校验的数据
   * @param ctx 校验上下文
   * @throws ValidationError 当存在错误级别的问题时抛出
   *
   * @example
   * ```ts
   * const handleSave = async () => {
   *   try {
   *     await validateOrThrow(tableData.value);
   *     // 校验通过，继续保存
   *     await saveData();
   *   } catch (e) {
   *     // 校验失败，e.message 包含错误信息
   *     ElMessage.error(e.message);
   *   }
   * };
   * ```
   */
  const validateOrThrow = async (data: T[], ctx?: ValidationContext): Promise<ValidationResult> => {
    const result = await validate(data, ctx);

    if (!result.valid) {
      const error = new Error(
        `校验失败：发现 ${result.errorCount} 个错误` +
          (result.warningCount > 0 ? `，${result.warningCount} 个警告` : '')
      );
      (error as any).validationResult = result;
      (error as any).isValidationError = true;
      throw error;
    }

    return result;
  };

  /**
   * 校验是否通过（简化版，直接返回布尔值）
   * @param data 要校验的数据
   * @param ctx 校验上下文
   * @returns true 表示通过，false 表示有错误
   */
  const isValid = async (data: T[], ctx?: ValidationContext): Promise<boolean> => {
    const result = await validate(data, ctx);
    return result.valid;
  };

  /**
   * 校验单行
   */
  const validateRow = async (row: T, rowIndex: number): Promise<ValidationIssue[]> => {
    const rowIssues: ValidationIssue[] = [];

    Object.entries(currentRules.value).forEach(([field, fieldRules]) => {
      const rulesArray = Array.isArray(fieldRules) ? fieldRules : [fieldRules];
      const value = (row as any)[field];

      rulesArray.forEach((rule, ruleIndex) => {
        const errorMsg = validateByRule(value, rule, row, rowIndex, field);
        if (errorMsg) {
          rowIssues.push({
            level: rule.level || 'error',
            rowIndex,
            field,
            fieldLabel: fieldLabels[field] || field,
            message: errorMsg,
            value,
            ruleName: `${field}[${ruleIndex}]`,
          });
        }
      });
    });

    // 更新该行的问题
    issues.value = [...issues.value.filter((i) => i.rowIndex !== rowIndex), ...rowIssues];

    return rowIssues;
  };

  /**
   * 校验单个字段
   */
  const validateField = (
    value: any,
    field: string,
    row: T,
    rowIndex: number
  ): ValidationIssue[] => {
    const fieldRules = currentRules.value[field];
    if (!fieldRules) return [];

    const rulesArray = Array.isArray(fieldRules) ? fieldRules : [fieldRules];
    const fieldIssues: ValidationIssue[] = [];

    rulesArray.forEach((rule, ruleIndex) => {
      const errorMsg = validateByRule(value, rule, row, rowIndex, field);
      if (errorMsg) {
        fieldIssues.push({
          level: rule.level || 'error',
          rowIndex,
          field,
          fieldLabel: fieldLabels[field] || field,
          message: errorMsg,
          value,
          ruleName: `${field}[${ruleIndex}]`,
        });
      }
    });

    // 更新该字段的问题
    const cellKey = `${rowIndex}-${field}`;
    issues.value = [
      ...issues.value.filter((i) => !(i.rowIndex === rowIndex && i.field === field)),
      ...fieldIssues,
    ];

    return fieldIssues;
  };

  /**
   * 清除校验结果
   */
  const clearValidation = () => {
    issues.value = [];
  };

  /**
   * 清除指定行的校验结果
   */
  const clearRowValidation = (rowIndex: number) => {
    issues.value = issues.value.filter((i) => i.rowIndex !== rowIndex);
  };

  /**
   * 清除指定字段的校验结果
   */
  const clearFieldValidation = (field: string, rowIndex?: number) => {
    issues.value = issues.value.filter((i) => {
      if (i.field !== field) return true;
      if (rowIndex !== undefined && i.rowIndex !== rowIndex) return true;
      return false;
    });
  };

  // ==================== VXE-Table 集成 ====================

  /**
   * 获取行的样式类（用于 row-class-name）
   */
  const getRowClassName = ({ rowIndex }: { rowIndex: number }): string => {
    const rowIssues = issuesByRow.value.get(rowIndex);
    if (!rowIssues || rowIssues.length === 0) return '';

    if (rowIssues.some((i) => i.level === 'error')) return 'vxe-row--validation-error';
    if (rowIssues.some((i) => i.level === 'warning')) return 'vxe-row--validation-warning';
    if (rowIssues.some((i) => i.level === 'info')) return 'vxe-row--validation-info';

    return '';
  };

  /**
   * 获取单元格的样式类（用于 cell-class-name）
   */
  const getCellClassName = ({ rowIndex, column }: { rowIndex: number; column: any }): string => {
    const field = column?.field;
    if (!field) return '';

    const key = `${rowIndex}-${field}`;
    const cellIssues = issuesByCell.value.get(key);
    if (!cellIssues || cellIssues.length === 0) return '';

    if (cellIssues.some((i) => i.level === 'error')) return 'vxe-cell--validation-error';
    if (cellIssues.some((i) => i.level === 'warning')) return 'vxe-cell--validation-warning';
    if (cellIssues.some((i) => i.level === 'info')) return 'vxe-cell--validation-info';

    return '';
  };

  /**
   * 获取单元格的 tooltip 内容
   */
  const getCellTooltip = (rowIndex: number, field: string): string | null => {
    const key = `${rowIndex}-${field}`;
    const cellIssues = issuesByCell.value.get(key);
    if (!cellIssues || cellIssues.length === 0) return null;

    return cellIssues.map((i) => i.message).join('\n');
  };

  /**
   * 转换为 VXE-Table 的 edit-rules 格式
   */
  const toVxeEditRules = (): Record<string, any[]> => {
    const vxeRules: Record<string, VxeEditRule[]> = {};

    Object.entries(currentRules.value).forEach(([field, fieldRules]) => {
      const rulesArray = Array.isArray(fieldRules) ? fieldRules : [fieldRules];

      vxeRules[field] = rulesArray.map((rule) => {
        const vxeRule: VxeEditRule = {};

        if (rule.required) vxeRule.required = true;
        if (rule.min !== undefined) vxeRule.min = rule.min;
        if (rule.max !== undefined) vxeRule.max = rule.max;
        if (rule.pattern) {
          vxeRule.pattern =
            typeof rule.pattern === 'string' ? new RegExp(rule.pattern) : rule.pattern;
        }
        if (rule.message) {
          vxeRule.message =
            typeof rule.message === 'function' ? rule.message(undefined, {}) : rule.message;
        }

        // 如果有自定义校验器，转换为 VXE 格式
        if (rule.validator || rule.type) {
          vxeRule.validator = ({ cellValue, row, rowIndex }) => {
            const errorMsg = validateByRule(cellValue, rule, row, rowIndex, field);
            if (errorMsg) {
              return new Error(errorMsg);
            }
          };
        }

        return vxeRule;
      });
    });

    return vxeRules;
  };

  /**
   * VXE-Table 4.x valid-config 配置
   * message: 'tooltip' 鼠标悬停时显示校验消息（右上角三角号触发）
   */
  const vxeValidConfig = {
    // 显示校验消息
    showMessage: true,
    // VXE-Table 4.x: 'tooltip' | 'inline' | 'default'
    // 'tooltip' 鼠标悬停时显示，配合右上角三角号使用
    message: 'tooltip' as const,
    // 'single' 只显示第一个错误，'full' 显示所有
    msgMode: 'single' as const,
    // 校验主题：'beautify'(红底白字) | 'normal'(白底红字)
    theme: 'normal' as const,
    // 自动定位到错误位置
    autoPos: true,
    // 校验失败时不自动清除（保持错误状态）
    autoClear: false,
  };

  // ==================== 动态配置 ====================

  /**
   * 更新校验规则
   */
  const setRules = (newRules: FieldRules) => {
    currentRules.value = newRules;
  };

  /**
   * 添加字段规则
   */
  const addFieldRules = (field: string, rules: ValidationRule | ValidationRule[]) => {
    const existing = currentRules.value[field];
    const existingArray = existing ? (Array.isArray(existing) ? existing : [existing]) : [];
    const newArray = Array.isArray(rules) ? rules : [rules];
    currentRules.value = {
      ...currentRules.value,
      [field]: [...existingArray, ...newArray],
    };
  };

  /**
   * 移除字段规则
   */
  const removeFieldRules = (field: string) => {
    const { [field]: _, ...rest } = currentRules.value;
    currentRules.value = rest;
  };

  /**
   * 添加全局校验器
   */
  const addGlobalValidator = (validator: GlobalValidator) => {
    currentGlobalValidators.value = [...currentGlobalValidators.value, validator];
  };

  /**
   * 移除全局校验器
   */
  const removeGlobalValidator = (name: string) => {
    currentGlobalValidators.value = currentGlobalValidators.value.filter((v) => v.name !== name);
  };

  /**
   * 更新校验上下文
   */
  const setContext = (ctx: ValidationContext) => {
    validationContext.value = { ...validationContext.value, ...ctx };
  };

  // ==================== 自动校验 ====================

  /**
   * 创建自动校验的数据监听器
   */
  const createAutoValidator = (dataRef: Ref<T[]>) => {
    const debouncedValidate = debounce(() => {
      validate(dataRef.value);
    }, autoValidateDelay);

    if (autoValidate) {
      watch(dataRef, debouncedValidate, { deep: true });
    }

    return debouncedValidate;
  };

  // ==================== 返回 ====================

  return {
    // 状态
    issues,
    validating,
    errorCount,
    warningCount,
    infoCount,
    hasIssues,
    hasErrors,
    issuesByRow,
    issuesByCell,
    globalIssues,

    // 核心方法
    validate,
    validateOrThrow, // 校验失败时抛出错误，用于阻断保存
    isValid, // 简化版，直接返回布尔值
    validateRow,
    validateField,
    clearValidation,
    clearRowValidation,
    clearFieldValidation,

    // VXE-Table 集成
    getRowClassName,
    getCellClassName,
    getCellTooltip,
    toVxeEditRules,
    vxeValidConfig,

    // 动态配置
    setRules,
    addFieldRules,
    removeFieldRules,
    addGlobalValidator,
    removeGlobalValidator,
    setContext,
    validationContext,

    // 自动校验
    createAutoValidator,
  };
}

// ==================== 类型导出 ====================

export type UseVxeTableValidationReturn = ReturnType<typeof useVxeTableValidation>;
