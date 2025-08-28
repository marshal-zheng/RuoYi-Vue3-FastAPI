// 正则验证规则接口
interface RegRule {
  pattern: string;
  message: string;
}

// 样式接口
interface ElementStyle {
  width?: string;
  height?: string;
  [key: string]: any;
}

// 默认表单元素接口
interface DefaultFormElement {
  layout: string;
  tagIcon: string;
  label: string;
  vModel: string;
  formId: number;
  tag: string;
  placeholder: string;
  defaultValue: string | number | boolean | any[];
  span: number;
  style: ElementStyle;
  clearable?: boolean;
  prepend?: string;
  append?: string;
  'prefix-icon'?: string;
  'suffix-icon'?: string;
  maxlength?: number;
  'show-word-limit'?: boolean;
  readonly?: boolean;
  disabled?: boolean;
  required?: boolean;
  changeTag?: boolean;
  regList?: RegRule[];
  // 其他可能的属性
  type?: string;
  min?: number;
  max?: number;
  step?: number;
  precision?: number;
  'controls-position'?: string;
  'step-strictly'?: boolean;
  filterable?: boolean;
  multiple?: boolean;
  options?: Array<{ label: string; value: any; disabled?: boolean }>;
  size?: string;
  optionType?: string;
  border?: boolean;
  'active-text'?: string;
  'inactive-text'?: string;
  'active-color'?: string;
  'inactive-color'?: string;
  'active-value'?: any;
  'inactive-value'?: any;
  'show-stops'?: boolean;
  range?: boolean;
  'start-placeholder'?: string;
  'end-placeholder'?: string;
  'range-separator'?: string;
  'is-range'?: boolean;
  format?: string;
  'value-format'?: string;
  'picker-options'?: any;
  'allow-half'?: boolean;
  'show-text'?: boolean;
  'show-score'?: boolean;
  'show-alpha'?: boolean;
  'color-format'?: string;
  action?: string;
  'auto-upload'?: boolean;
  'before-upload'?: string;
  'list-type'?: string;
  accept?: string;
  name?: string;
  showTip?: boolean;
  buttonText?: string;
  fileSize?: number;
  sizeUnit?: string;
  icon?: string;
  props?: any;
  'show-all-levels'?: boolean;
  separator?: string;
}

// 默认表单元素数组
const drawingDefault: DefaultFormElement[] = [
  {
    layout: 'colFormItem',
    tagIcon: 'input',
    label: '手机号',
    vModel: 'mobile',
    formId: 6,
    tag: 'el-input',
    placeholder: '请输入手机号',
    defaultValue: '',
    span: 24,
    style: { width: '100%' },
    clearable: true,
    prepend: '',
    append: '',
    'prefix-icon': 'Cellphone',
    'suffix-icon': '',
    maxlength: 11,
    'show-word-limit': true,
    readonly: false,
    disabled: false,
    required: true,
    changeTag: true,
    regList: [
      {
        pattern: '/^1(3|4|5|7|8|9)\\d{9}$/',
        message: '手机号格式错误',
      },
    ],
  },
];

export default drawingDefault;
export type { DefaultFormElement, RegRule, ElementStyle };