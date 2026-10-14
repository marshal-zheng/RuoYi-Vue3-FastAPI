import type { ComponentPublicInstance } from 'vue';
import type { FormInstance } from 'element-plus';
import { isRecord } from '@/types/http-contract';

/**
 * 通用js方法封装处理
 * Copyright (c) 2019 ruoyi
 */

interface DictItem {
  value: string | number;
  label: string;
}

interface TreeConfig {
  id: string;
  parentId: string;
  childrenList: string;
}

// 日期格式化
export function parseTime(time?: string | number | Date | null, pattern?: string): string | null {
  if (arguments.length === 0 || !time) {
    return null;
  }
  const format = pattern || '{y}-{m}-{d} {h}:{i}:{s}';
  let date: Date;
  if (typeof time === 'object') {
    date = time;
  } else {
    if (typeof time === 'string' && /^[0-9]+$/.test(time)) {
      time = parseInt(time);
    } else if (typeof time === 'string') {
      time = time
        .replace(new RegExp(/-/gm), '/')
        .replace('T', ' ')
        .replace(new RegExp(/\.[\d]{3}/gm), '');
    }
    if (typeof time === 'number' && time.toString().length === 10) {
      time = time * 1000;
    }
    date = new Date(time);
  }
  const formatObj: { [key: string]: number } = {
    y: date.getFullYear(),
    m: date.getMonth() + 1,
    d: date.getDate(),
    h: date.getHours(),
    i: date.getMinutes(),
    s: date.getSeconds(),
    a: date.getDay(),
  };
  const time_str = format.replace(/{(y|m|d|h|i|s|a)+}/g, (result: string, key: string) => {
    let value = formatObj[key];
    // Note: getDay() returns 0 on Sunday
    if (key === 'a') {
      return ['日', '一', '二', '三', '四', '五', '六'][value];
    }
    if (result.length > 0 && value < 10) {
      return '0' + value;
    }
    return String(value || 0);
  });
  return time_str;
}

// 表单重置
export function resetForm(this: Pick<ComponentPublicInstance, '$refs'>, refName: string): void {
  const form = this.$refs[refName];
  if (
    form &&
    typeof form === 'object' &&
    'resetFields' in form &&
    typeof form.resetFields === 'function'
  ) {
    (form as Pick<FormInstance, 'resetFields'>).resetFields();
  }
}

// 添加日期范围
export function addDateRange<T extends object, Key extends string = 'Time'>(
  params: T,
  dateRange: readonly string[] | null | undefined,
  propName?: Key
): T & Record<`begin${Key}` | `end${Key}`, string | undefined>;
export function addDateRange(
  params: object,
  dateRange: readonly string[] | null | undefined,
  propName?: string
): object {
  const dates = Array.isArray(dateRange) ? dateRange : [];
  const suffix = propName ?? 'Time';
  return Object.assign(params, { [`begin${suffix}`]: dates[0], [`end${suffix}`]: dates[1] });
}

/**
 * 序列化日期范围参数
 * dateRange: ['2024-01-01', '2024-01-31'] -> beginTime/endTime
 * @param propName 自定义字段名后缀，如 'CreateTime' -> beginCreateTime/endCreateTime
 */
export function serializeDateRange(
  query: Record<string, unknown>,
  propName?: string
): Record<string, unknown> {
  const result = { ...query };
  const dateRange = result.dateRange;

  if (Array.isArray(dateRange) && dateRange.length >= 2) {
    const [begin, end] = dateRange;
    if (begin || end) {
      if (propName) {
        result[`begin${propName}`] = begin;
        result[`end${propName}`] = end;
      } else {
        result.beginTime = begin;
        result.endTime = end;
      }
    }
    delete result.dateRange;
  }

  return result;
}

// 回显数据字典
export function selectDictLabel(datas: DictItem[], value: string | number | undefined): string {
  if (value === undefined) {
    return '';
  }
  const matched = datas.find((item) => item.value == '' + value);
  if (matched) {
    return matched.label;
  }
  return String(value);
}

// 回显数据字典（字符串数组）
export function selectDictLabels(
  datas: DictItem[],
  value: string | string[] | undefined,
  separator?: string
): string {
  if (value === undefined || (Array.isArray(value) && value.length === 0)) {
    return '';
  }
  const currentSeparator = separator ?? ',';
  const values = Array.isArray(value)
    ? value
    : value.split(value.includes(currentSeparator) ? currentSeparator : ',');

  return values
    .map((item) => {
      const matched = datas.find((dict) => dict.value == '' + item);
      return matched ? matched.label : item;
    })
    .join(currentSeparator);
}

// 字符串格式化(%s )
export function sprintf(str: string, ...args: unknown[]): string {
  var flag = true,
    i = 0;
  str = str.replace(/%s/g, function () {
    var arg = args[i++];
    if (typeof arg === 'undefined') {
      flag = false;
      return '';
    }
    return String(arg);
  });
  return flag ? str : '';
}

// 转换字符串，undefined,null等转化为""
export function parseStrEmpty<T>(str: T): T | '' {
  if (!str || str == 'undefined' || str == 'null') {
    return '';
  }
  return str;
}

// Dynamic merge data is inspected before recursion; callers retain an unknown value boundary.
export function mergeRecursive(
  source: Record<string, unknown>,
  target: Record<string, unknown>
): Record<string, unknown> {
  for (const key in target) {
    const value = target[key];
    if (isRecord(value) && value.constructor === Object && isRecord(source[key])) {
      source[key] = mergeRecursive(source[key], value);
    } else {
      source[key] = value;
    }
  }
  return source;
}

/**
 * 构造树型结构数据
 * @param {*} data 数据源
 * @param {*} id id字段 默认 'id'
 * @param {*} parentId 父节点字段 默认 'parentId'
 * @param {*} children 孩子节点字段 默认 'children'
 */
export type TreeNode<T, Key extends string = 'children'> = T & {
  [Field in Key]?: TreeNode<T, Key>[];
};

export function handleTree<T extends object, Key extends string = 'children'>(
  data: T[],
  id?: string,
  parentId?: string,
  children?: Key
): TreeNode<T, Key>[];
export function handleTree<T extends object>(
  data: T[],
  id?: string,
  parentId?: string,
  children?: string
): T[] {
  const config: TreeConfig = {
    id: id || 'id',
    parentId: parentId || 'parentId',
    childrenList: children || 'children',
  };
  const childrenByParent = new Map<string, T[]>();
  const nodeIds = new Set<string>();
  for (const node of data) {
    const parent = String(Reflect.get(node, config.parentId));
    const siblings = childrenByParent.get(parent) ?? [];
    siblings.push(node);
    childrenByParent.set(parent, siblings);
    nodeIds.add(String(Reflect.get(node, config.id)));
  }
  const roots = data.filter((node) => !nodeIds.has(String(Reflect.get(node, config.parentId))));
  const attachChildren = (node: T): void => {
    const descendants = childrenByParent.get(String(Reflect.get(node, config.id)));
    Reflect.set(node, config.childrenList, descendants);
    descendants?.forEach(attachChildren);
  };
  roots.forEach(attachChildren);
  return roots;
}

/**
 * 参数处理
 * @param {*} params  参数
 */
export function tansParams(params: Record<string, unknown>): string {
  let result = '';
  for (const propName of Object.keys(params)) {
    const value = params[propName];
    var part = encodeURIComponent(propName) + '=';
    if (value !== null && value !== '' && typeof value !== 'undefined') {
      if (isRecord(value) || Array.isArray(value)) {
        for (const key of Object.keys(value)) {
          if (
            Reflect.get(value, key) !== null &&
            Reflect.get(value, key) !== '' &&
            Reflect.get(value, key) !== undefined
          ) {
            let params = propName + '[' + key + ']';
            var subPart = encodeURIComponent(params) + '=';
            result += subPart + encodeURIComponent(String(Reflect.get(value, key))) + '&';
          }
        }
      } else {
        result += part + encodeURIComponent(String(value)) + '&';
      }
    }
  }
  return result;
}

// 返回项目路径
export function getNormalPath(p?: string): string {
  if (!p || p == 'undefined') {
    return '';
  }
  let res = p.replace(/\/+/g, '/');
  if (res[res.length - 1] === '/') {
    return res.slice(0, res.length - 1);
  }
  return res;
}

// 验证是否为blob格式
export function blobValidate(data: Pick<Blob, 'type'>): boolean {
  return data.type !== 'application/json';
}
