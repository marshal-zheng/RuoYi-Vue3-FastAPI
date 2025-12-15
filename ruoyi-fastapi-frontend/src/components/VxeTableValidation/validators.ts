/**
 * VXE-Table 通用校验框架 - 预置校验器
 * 提供常用的校验规则，类似 async-validator
 */

import type { ValidationRule, ValidatorFunction, GlobalValidator, ValidationIssue } from './types';

// ==================== 工具函数 ====================

/** 判断值是否为空 */
export const isEmpty = (value: any): boolean => {
  if (value === null || value === undefined) return true;
  if (typeof value === 'string' && value.trim() === '') return true;
  if (Array.isArray(value) && value.length === 0) return true;
  return false;
};

/** 解析数值 */
export const parseNumber = (value: any): number | null => {
  if (value === null || value === undefined || value === '') return null;
  const num = Number(value);
  return Number.isFinite(num) ? num : null;
};

/** 获取值的长度 */
export const getLength = (value: any): number => {
  if (value === null || value === undefined) return 0;
  if (typeof value === 'string') return value.length;
  if (Array.isArray(value)) return value.length;
  return String(value).length;
};

// ==================== 类型校验器 ====================

const typeValidators: Record<string, (value: any) => boolean> = {
  string: (value) => typeof value === 'string',
  number: (value) => {
    const num = parseNumber(value);
    return num !== null;
  },
  integer: (value) => {
    const num = parseNumber(value);
    return num !== null && Number.isInteger(num);
  },
  float: (value) => {
    const num = parseNumber(value);
    return num !== null;
  },
  boolean: (value) => typeof value === 'boolean' || value === 'true' || value === 'false' || value === 0 || value === 1,
  array: (value) => Array.isArray(value),
  object: (value) => typeof value === 'object' && value !== null && !Array.isArray(value),
  date: (value) => {
    if (value instanceof Date) return !isNaN(value.getTime());
    const date = new Date(value);
    return !isNaN(date.getTime());
  },
  url: (value) => {
    if (typeof value !== 'string') return false;
    try {
      new URL(value);
      return true;
    } catch {
      return /^https?:\/\/.+/.test(value);
    }
  },
  email: (value) => {
    if (typeof value !== 'string') return false;
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
  },
};

// ==================== 核心校验函数 ====================

/**
 * 执行单条规则校验
 */
export const validateByRule = (
  value: any,
  rule: ValidationRule,
  row: any,
  rowIndex: number,
  field: string
): string | null => {
  // 条件校验
  if (rule.when && !rule.when(row, rowIndex)) {
    return null;
  }

  // 值转换
  let validValue = value;
  if (rule.transform) {
    validValue = rule.transform(value);
  }

  // 必填校验
  if (rule.required && isEmpty(validValue)) {
    return getMessage(rule.message, '此字段为必填项', validValue, row);
  }

  // 空值跳过后续校验（非必填时）
  if (isEmpty(validValue)) {
    return null;
  }

  // 类型校验
  if (rule.type && typeValidators[rule.type]) {
    if (!typeValidators[rule.type](validValue)) {
      const typeMessages: Record<string, string> = {
        string: '必须是字符串',
        number: '必须是有效数字',
        integer: '必须是整数',
        float: '必须是数字',
        boolean: '必须是布尔值',
        array: '必须是数组',
        object: '必须是对象',
        date: '必须是有效日期',
        url: '必须是有效的URL',
        email: '必须是有效的邮箱地址',
      };
      return getMessage(rule.message, typeMessages[rule.type] || '类型不正确', validValue, row);
    }
  }

  // 长度/范围校验
  const numValue = parseNumber(validValue);
  const lenValue = getLength(validValue);

  if (rule.len !== undefined) {
    if (rule.type === 'number' || rule.type === 'integer' || rule.type === 'float') {
      if (numValue !== rule.len) {
        return getMessage(rule.message, `必须等于 ${rule.len}`, validValue, row);
      }
    } else {
      if (lenValue !== rule.len) {
        return getMessage(rule.message, `长度必须是 ${rule.len}`, validValue, row);
      }
    }
  }

  if (rule.min !== undefined) {
    if (rule.type === 'number' || rule.type === 'integer' || rule.type === 'float') {
      if (numValue !== null && numValue < rule.min) {
        return getMessage(rule.message, `不能小于 ${rule.min}`, validValue, row);
      }
    } else {
      if (lenValue < rule.min) {
        return getMessage(rule.message, `长度不能小于 ${rule.min}`, validValue, row);
      }
    }
  }

  if (rule.max !== undefined) {
    if (rule.type === 'number' || rule.type === 'integer' || rule.type === 'float') {
      if (numValue !== null && numValue > rule.max) {
        return getMessage(rule.message, `不能大于 ${rule.max}`, validValue, row);
      }
    } else {
      if (lenValue > rule.max) {
        return getMessage(rule.message, `长度不能超过 ${rule.max}`, validValue, row);
      }
    }
  }

  // 正则校验
  if (rule.pattern) {
    const regex = typeof rule.pattern === 'string' ? new RegExp(rule.pattern) : rule.pattern;
    if (!regex.test(String(validValue))) {
      return getMessage(rule.message, '格式不正确', validValue, row);
    }
  }

  // 枚举校验
  if (rule.enum && !rule.enum.includes(validValue)) {
    return getMessage(rule.message, `必须是 [${rule.enum.join(', ')}] 之一`, validValue, row);
  }

  // 自定义校验器
  if (rule.validator) {
    const result = rule.validator(validValue, row, rowIndex, field);
    if (result === false) {
      return getMessage(rule.message, '校验失败', validValue, row);
    }
    if (typeof result === 'string') {
      return result;
    }
  }

  return null;
};

/** 获取消息 */
const getMessage = (
  message: string | ((value: any, row: any) => string) | undefined,
  defaultMsg: string,
  value: any,
  row: any
): string => {
  if (!message) return defaultMsg;
  if (typeof message === 'function') return message(value, row);
  return message;
};

// ==================== 预置规则工厂 ====================

/** 必填规则 */
export const required = (message?: string): ValidationRule => ({
  required: true,
  message: message || '此字段为必填项',
});

/** 数字类型规则 */
export const number = (message?: string): ValidationRule => ({
  type: 'number',
  message: message || '请输入有效数字',
});

/** 整数规则 */
export const integer = (message?: string): ValidationRule => ({
  type: 'integer',
  message: message || '请输入整数',
});

/** 正整数规则 */
export const positiveInteger = (message?: string): ValidationRule => ({
  type: 'integer',
  min: 1,
  message: message || '请输入正整数',
});

/** 非负整数规则 */
export const nonNegativeInteger = (message?: string): ValidationRule => ({
  type: 'integer',
  min: 0,
  message: message || '请输入非负整数',
});

/** 范围规则 */
export const range = (min: number, max: number, message?: string): ValidationRule => ({
  type: 'number',
  min,
  max,
  message: message || `必须在 ${min} - ${max} 之间`,
});

/** 长度范围规则 */
export const lengthRange = (min: number, max: number, message?: string): ValidationRule => ({
  min,
  max,
  message: message || `长度必须在 ${min} - ${max} 之间`,
});

/** 精确长度规则 */
export const length = (len: number, message?: string): ValidationRule => ({
  len,
  message: message || `长度必须是 ${len}`,
});

/** 正则规则 */
export const pattern = (regex: RegExp | string, message?: string): ValidationRule => ({
  pattern: regex,
  message: message || '格式不正确',
});

/** 邮箱规则 */
export const email = (message?: string): ValidationRule => ({
  type: 'email',
  message: message || '请输入有效的邮箱地址',
});

/** URL规则 */
export const url = (message?: string): ValidationRule => ({
  type: 'url',
  message: message || '请输入有效的URL',
});

/** 枚举规则 */
export const oneOf = (values: any[], message?: string): ValidationRule => ({
  enum: values,
  message: message || `必须是 [${values.join(', ')}] 之一`,
});

/** 自定义校验规则 */
export const custom = (
  validator: ValidatorFunction,
  message?: string,
  options?: Partial<ValidationRule>
): ValidationRule => ({
  validator,
  message,
  ...options,
});

/** 警告级别规则（不阻止提交） */
export const warning = (rule: ValidationRule): ValidationRule => ({
  ...rule,
  level: 'warning',
});

/** 信息级别规则（仅提示） */
export const info = (rule: ValidationRule): ValidationRule => ({
  ...rule,
  level: 'info',
});

// ==================== 业务常用校验器 ====================

/** 端口号校验 */
export const port = (message?: string): ValidationRule => ({
  type: 'integer',
  min: 0,
  max: 65535,
  message: message || '端口号范围应在 0-65535',
});

/** IP地址校验 */
export const ipAddress = (message?: string): ValidationRule => ({
  pattern: /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/,
  message: message || '请输入有效的IP地址',
});

/** MAC地址校验 */
export const macAddress = (message?: string): ValidationRule => ({
  pattern: /^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$/,
  message: message || '请输入有效的MAC地址',
});

/** 字节数校验（正整数，可选最大值） */
export const byteCount = (maxBytes?: number, message?: string): ValidationRule => ({
  type: 'integer',
  min: 1,
  max: maxBytes,
  message: message || (maxBytes ? `字节数必须在 1-${maxBytes} 之间` : '字节数必须为正整数'),
});

/** 比例尺校验（非零数字） */
export const scale = (message?: string): ValidationRule => ({
  type: 'number',
  validator: (value) => {
    const num = parseNumber(value);
    return num !== null && num !== 0;
  },
  message: message || '比例尺不能为0',
});

// ==================== 全局校验器工厂 ====================

/**
 * 创建带宽校验器
 */
export const createBandwidthValidator = (options: {
  /** 获取帧长度的函数 */
  getFrameLength: (data: any[]) => number;
  /** 获取传输频率的函数 */
  getFrequency: (context?: any) => number;
  /** 获取带宽限制的函数 */
  getBandwidthLimit: (context?: any) => number;
  /** 格式化带宽显示 */
  formatBandwidth?: (bps: number) => string;
}): GlobalValidator => {
  const defaultFormat = (bps: number): string => {
    if (bps >= 1e9) return `${(bps / 1e9).toFixed(2)} Gbps`;
    if (bps >= 1e6) return `${(bps / 1e6).toFixed(2)} Mbps`;
    if (bps >= 1e3) return `${(bps / 1e3).toFixed(2)} Kbps`;
    return `${bps} bps`;
  };

  const formatBandwidth = options.formatBandwidth || defaultFormat;

  return {
    name: 'bandwidth',
    validator: (data, context) => {
      const frameLength = options.getFrameLength(data);
      const frequency = options.getFrequency(context);
      const limit = options.getBandwidthLimit(context);

      if (!limit || !frequency) return null;

      const requiredBandwidth = frameLength * 8 * frequency;

      if (requiredBandwidth > limit) {
        return {
          level: 'error',
          rowIndex: -1,
          field: 'bandwidth',
          fieldLabel: '带宽',
          message: `数据带宽需求 (${formatBandwidth(requiredBandwidth)}) 超出限制 (${formatBandwidth(limit)})`,
          value: requiredBandwidth,
          suggestion: `当前帧长度 ${frameLength} 字节，传输频率 ${frequency}Hz`,
        };
      }

      if (requiredBandwidth > limit * 0.8) {
        return {
          level: 'warning',
          rowIndex: -1,
          field: 'bandwidth',
          fieldLabel: '带宽',
          message: `带宽使用率已达 ${Math.round((requiredBandwidth / limit) * 100)}%`,
          value: requiredBandwidth,
          suggestion: '建议预留一定带宽余量',
        };
      }

      return null;
    },
  };
};

/**
 * 创建帧长度校验器
 */
export const createFrameLengthValidator = (options: {
  /** 获取实际帧长度的函数 */
  getActualLength: (data: any[]) => number;
  /** 获取配置的帧长度限制 */
  getConfiguredLimit?: (context?: any) => number | undefined;
  /** 总线类型帧长度限制 */
  busLimits?: Record<string, number>;
  /** 获取当前总线类型 */
  getBusType?: (context?: any) => string | undefined;
}): GlobalValidator => {
  return {
    name: 'frameLength',
    validator: (data, context) => {
      const actualLength = options.getActualLength(data);
      const configuredLimit = options.getConfiguredLimit?.(context);
      const busType = options.getBusType?.(context);
      const busLimit = busType && options.busLimits ? options.busLimits[busType] : undefined;

      const issues: ValidationIssue[] = [];

      if (configuredLimit && actualLength > configuredLimit) {
        issues.push({
          level: 'error',
          rowIndex: -1,
          field: 'frameLength',
          fieldLabel: '帧长度',
          message: `实际数据长度 (${actualLength} 字节) 超出配置的帧长度 (${configuredLimit} 字节)`,
          value: actualLength,
          suggestion: '请增加配置的帧长度或减少字段数据',
        });
      }

      if (busLimit && actualLength > busLimit) {
        issues.push({
          level: 'error',
          rowIndex: -1,
          field: 'frameLength',
          fieldLabel: '帧长度',
          message: `实际数据长度 (${actualLength} 字节) 超出 ${busType} 总线限制 (${busLimit} 字节)`,
          value: actualLength,
          suggestion: `${busType} 总线单帧最大支持 ${busLimit} 字节`,
        });
      }

      return issues.length > 0 ? issues : null;
    },
  };
};

/**
 * 创建数值范围溢出校验器
 */
export const createValueRangeValidator = (options: {
  /** 数据类型字段名 */
  dataTypeField: string;
  /** 值域字段名 */
  valueRangeField: string;
  /** 数据类型对应的值范围 */
  typeRanges: Record<string, { min: number; max: number }>;
}): GlobalValidator => {
  return {
    name: 'valueRange',
    validator: (data) => {
      const issues: ValidationIssue[] = [];

      data.forEach((row, index) => {
        const dataType = row[options.dataTypeField];
        const valueRange = row[options.valueRangeField];

        if (!dataType || !valueRange) return;

        const typeKey = String(dataType).toUpperCase();
        const range = options.typeRanges[typeKey];
        if (!range) return;

        // 尝试从值域中提取数值范围
        const rangeMatch = String(valueRange).match(/(-?\d+(?:\.\d+)?)\s*[-~,]\s*(-?\d+(?:\.\d+)?)/);
        if (rangeMatch) {
          const minVal = parseFloat(rangeMatch[1]);
          const maxVal = parseFloat(rangeMatch[2]);

          if (minVal < range.min || maxVal > range.max) {
            issues.push({
              level: 'error',
              rowIndex: index,
              field: options.valueRangeField,
              fieldLabel: '值域',
              message: `值域 [${minVal}, ${maxVal}] 超出 ${dataType} 的有效范围 [${range.min}, ${range.max}]`,
              value: valueRange,
              suggestion: `${dataType} 的有效范围是 ${range.min} ~ ${range.max}`,
            });
          }
        }
      });

      return issues.length > 0 ? issues : null;
    },
  };
};

/**
 * 创建唯一性校验器
 */
export const createUniqueValidator = (options: {
  /** 需要唯一的字段名 */
  field: string;
  /** 字段显示名称 */
  fieldLabel?: string;
  /** 是否忽略空值 */
  ignoreEmpty?: boolean;
}): GlobalValidator => {
  return {
    name: `unique-${options.field}`,
    validator: (data) => {
      const issues: ValidationIssue[] = [];
      const seen = new Map<any, number>();

      data.forEach((row, index) => {
        const value = row[options.field];
        if (options.ignoreEmpty !== false && isEmpty(value)) return;

        if (seen.has(value)) {
          issues.push({
            level: 'error',
            rowIndex: index,
            field: options.field,
            fieldLabel: options.fieldLabel || options.field,
            message: `"${value}" 与第 ${seen.get(value)! + 1} 行重复`,
            value,
            suggestion: '请确保此字段值唯一',
          });
        } else {
          seen.set(value, index);
        }
      });

      return issues.length > 0 ? issues : null;
    },
  };
};
