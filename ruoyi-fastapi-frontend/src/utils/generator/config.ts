// 表单配置接口
export interface FormConfig {
  formRef: string;
  formModel: string;
  size: 'large' | 'default' | 'small';
  labelPosition: 'left' | 'right' | 'top';
  labelWidth: number;
  formRules: string;
  gutter: number;
  disabled: boolean;
  span: number;
  formBtns: boolean;
}

// 正则验证规则接口
export interface RegRule {
  pattern: string;
  message: string;
}

// 选项接口
export interface Option {
  label: string;
  value: string | number;
  disabled?: boolean;
}

// 级联选择器属性接口
export interface CascaderProps {
  props: {
    multiple?: boolean;
    value?: string;
    label?: string;
    children?: string;
  };
}

// 自动调整大小接口
export interface Autosize {
  minRows: number;
  maxRows: number;
}

// 样式接口
export interface ComponentStyle {
  width?: string;
}

// 基础组件配置接口
export interface BaseComponent {
  label: string;
  tag: string;
  tagIcon: string;
  placeholder?: string;
  defaultValue: any;
  span: number;
  labelWidth: number | null;
  style?: ComponentStyle;
  disabled: boolean;
  required: boolean;
  regList: RegRule[];
  changeTag: boolean;
  document: string;
}

// 输入组件接口
export interface InputComponent extends BaseComponent {
  type: 'text' | 'textarea' | 'password';
  clearable?: boolean;
  prepend?: string;
  append?: string;
  'prefix-icon'?: string;
  'suffix-icon'?: string;
  maxlength?: number | null;
  'show-word-limit'?: boolean;
  readonly?: boolean;
  'show-password'?: boolean;
  autosize?: Autosize;
}

// 数字输入组件接口
export interface InputNumberComponent extends BaseComponent {
  min?: number;
  max?: number;
  step?: number;
  'step-strictly'?: boolean;
  precision?: number;
  'controls-position'?: string;
}

// 选择组件接口
export interface SelectComponent extends BaseComponent {
  clearable: boolean;
  filterable: boolean;
  multiple: boolean;
  options: Option[];
  dataType?: 'static' | 'dynamic';
  labelKey?: string;
  valueKey?: string;
  childrenKey?: string;
}

// 级联选择器组件接口
export interface CascaderComponent extends BaseComponent {
  props: CascaderProps;
  'show-all-levels': boolean;
  clearable: boolean;
  filterable: boolean;
  options: Option[];
  dataType: 'static' | 'dynamic';
  labelKey: string;
  valueKey: string;
  childrenKey: string;
  separator: string;
}

// 单选框组组件接口
export interface RadioGroupComponent extends BaseComponent {
  optionType: 'default' | 'button';
  border: boolean;
  size: 'large' | 'default' | 'small';
  options: Option[];
}

// 多选框组组件接口
export interface CheckboxGroupComponent extends BaseComponent {
  optionType: 'default' | 'button';
  border: boolean;
  size: 'large' | 'default' | 'small';
  options: Option[];
}

// 开关组件接口
export interface SwitchComponent extends BaseComponent {
  'active-text': string;
  'inactive-text': string;
  'active-color': string | null;
  'inactive-color': string | null;
  'active-value': boolean | string | number;
  'inactive-value': boolean | string | number;
}

// 滑块组件接口
export interface SliderComponent extends BaseComponent {
  min: number;
  max: number;
  step: number;
  'show-stops': boolean;
  range: boolean;
}

// 时间选择器组件接口
export interface TimePickerComponent extends BaseComponent {
  clearable: boolean;
  format: string;
  'value-format': string;
  'is-range'?: boolean;
  'range-separator'?: string;
  'start-placeholder'?: string;
  'end-placeholder'?: string;
}

// 日期选择器组件接口
export interface DatePickerComponent extends BaseComponent {
  type: 'date' | 'daterange' | 'datetime' | 'datetimerange' | 'week' | 'month' | 'year';
  clearable: boolean;
  format: string;
  'value-format': string;
  readonly: boolean;
  'range-separator'?: string;
  'start-placeholder'?: string;
  'end-placeholder'?: string;
}

// 评分组件接口
export interface RateComponent extends BaseComponent {
  max: number;
  'allow-half': boolean;
  'show-text': boolean;
  'show-score': boolean;
}

// 颜色选择器组件接口
export interface ColorPickerComponent extends BaseComponent {
  'show-alpha': boolean;
  'color-format': string;
  size: 'large' | 'default' | 'small';
  span: number;
}

// 上传组件接口
export interface UploadComponent extends BaseComponent {
  action: string;
  accept: string;
  name: string;
  'auto-upload': boolean;
  showTip: boolean;
  buttonText: string;
  fileSize: number;
  sizeUnit: 'KB' | 'MB' | 'GB';
  'list-type': 'text' | 'picture' | 'picture-card';
  multiple: boolean;
  tip: string;
  span: number;
}

// 布局组件接口
export interface LayoutComponent {
  layout: 'rowFormItem' | 'colFormItem';
  tagIcon: string;
  label: string;
  layoutTree?: boolean;
  children?: any[];
  document: string;
  type?: string;
  justify?: string;
  align?: string;
  changeTag?: boolean;
  labelWidth?: number | null;
  tag?: string;
  span?: number;
  default?: string;
  icon?: string;
  size?: string;
  disabled?: boolean;
}

export const formConf: FormConfig = {
  formRef: 'formRef',
  formModel: 'formData',
  size: 'default',
  labelPosition: 'right',
  labelWidth: 100,
  formRules: 'rules',
  gutter: 15,
  disabled: false,
  span: 24,
  formBtns: true,
};

export const inputComponents: InputComponent[] = [
  {
    label: '单行文本',
    tag: 'el-input',
    tagIcon: 'input',
    type: 'text',
    placeholder: '请输入',
    defaultValue: undefined,
    span: 24,
    labelWidth: null,
    style: { width: '100%' },
    clearable: true,
    prepend: '',
    append: '',
    'prefix-icon': '',
    'suffix-icon': '',
    maxlength: null,
    'show-word-limit': false,
    readonly: false,
    disabled: false,
    required: true,
    regList: [],
    changeTag: true,
    document: 'https://element-plus.org/zh-CN/component/input',
  },
  {
    label: '多行文本',
    tag: 'el-input',
    tagIcon: 'textarea',
    type: 'textarea',
    placeholder: '请输入',
    defaultValue: undefined,
    span: 24,
    labelWidth: null,
    autosize: {
      minRows: 4,
      maxRows: 4,
    },
    style: { width: '100%' },
    maxlength: null,
    'show-word-limit': false,
    readonly: false,
    disabled: false,
    required: true,
    regList: [],
    changeTag: true,
    document: 'https://element-plus.org/zh-CN/component/input',
  },
  {
    label: '密码',
    tag: 'el-input',
    tagIcon: 'password',
    type: 'password',
    placeholder: '请输入',
    defaultValue: undefined,
    span: 24,
    'show-password': true,
    labelWidth: null,
    style: { width: '100%' },
    clearable: true,
    prepend: '',
    append: '',
    'prefix-icon': '',
    'suffix-icon': '',
    maxlength: null,
    'show-word-limit': false,
    readonly: false,
    disabled: false,
    required: true,
    regList: [],
    changeTag: true,
    document: 'https://element-plus.org/zh-CN/component/input',
  },
  {
    label: '计数器',
    tag: 'el-input-number',
    tagIcon: 'number',
    placeholder: '',
    defaultValue: undefined,
    span: 24,
    labelWidth: null,
    min: undefined,
    max: undefined,
    step: undefined,
    'step-strictly': false,
    precision: undefined,
    'controls-position': '',
    disabled: false,
    required: true,
    regList: [],
    changeTag: true,
    document: 'https://element-plus.org/zh-CN/component/input-number',
  } as any,
];

export const selectComponents: (
  | SelectComponent
  | CascaderComponent
  | RadioGroupComponent
  | CheckboxGroupComponent
  | SwitchComponent
  | SliderComponent
  | TimePickerComponent
  | DatePickerComponent
  | RateComponent
  | ColorPickerComponent
  | UploadComponent
)[] = [
  {
    label: '下拉选择',
    tag: 'el-select',
    tagIcon: 'select',
    placeholder: '请选择',
    defaultValue: undefined,
    span: 24,
    labelWidth: null,
    style: { width: '100%' },
    clearable: true,
    disabled: false,
    required: true,
    filterable: false,
    multiple: false,
    options: [
      {
        label: '选项一',
        value: 1,
      },
      {
        label: '选项二',
        value: 2,
      },
    ],
    regList: [],
    changeTag: true,
    document: 'https://element-plus.org/zh-CN/component/select',
  } as SelectComponent,
  {
    label: '级联选择',
    tag: 'el-cascader',
    tagIcon: 'cascader',
    placeholder: '请选择',
    defaultValue: [],
    span: 24,
    labelWidth: null,
    style: { width: '100%' },
    props: {
      props: {
        multiple: false,
      },
    },
    'show-all-levels': true,
    disabled: false,
    clearable: true,
    filterable: false,
    required: true,
    options: [
      {
        label: '选项1',
        value: 1,
      },
    ],
    dataType: 'dynamic',
    labelKey: 'label',
    valueKey: 'value',
    childrenKey: 'children',
    separator: '/',
    regList: [],
    changeTag: true,
    document: 'https://element-plus.org/zh-CN/component/cascader',
  } as CascaderComponent,
  {
    label: '单选框组',
    tag: 'el-radio-group',
    tagIcon: 'radio',
    defaultValue: 0,
    span: 24,
    labelWidth: null,
    style: {},
    optionType: 'default',
    border: false,
    size: 'default',
    disabled: false,
    required: true,
    options: [
      {
        label: '选项一',
        value: 1,
      },
      {
        label: '选项二',
        value: 2,
      },
    ],
    regList: [],
    changeTag: true,
    document: 'https://element-plus.org/zh-CN/component/radio',
  } as RadioGroupComponent,
  {
    label: '多选框组',
    tag: 'el-checkbox-group',
    tagIcon: 'checkbox',
    defaultValue: [],
    span: 24,
    labelWidth: null,
    style: {},
    optionType: 'default',
    border: false,
    size: 'default',
    disabled: false,
    required: true,
    options: [
      {
        label: '选项一',
        value: 1,
      },
      {
        label: '选项二',
        value: 2,
      },
    ],
    regList: [],
    changeTag: true,
    document: 'https://element-plus.org/zh-CN/component/checkbox',
  } as CheckboxGroupComponent,
  {
    label: '开关',
    tag: 'el-switch',
    tagIcon: 'switch',
    defaultValue: false,
    span: 24,
    labelWidth: null,
    style: {},
    disabled: false,
    required: true,
    'active-text': '',
    'inactive-text': '',
    'active-color': null,
    'inactive-color': null,
    'active-value': true,
    'inactive-value': false,
    regList: [],
    changeTag: true,
    document: 'https://element-plus.org/zh-CN/component/switch',
  } as SwitchComponent,
  {
    label: '滑块',
    tag: 'el-slider',
    tagIcon: 'slider',
    defaultValue: null,
    span: 24,
    labelWidth: null,
    disabled: false,
    required: true,
    min: 0,
    max: 100,
    step: 1,
    'show-stops': false,
    range: false,
    regList: [],
    changeTag: true,
    document: 'https://element-plus.org/zh-CN/component/slider',
  } as SliderComponent,
  {
    label: '时间选择',
    tag: 'el-time-picker',
    tagIcon: 'time',
    placeholder: '请选择',
    defaultValue: '',
    span: 24,
    labelWidth: null,
    style: { width: '100%' },
    disabled: false,
    clearable: true,
    required: true,
    format: 'HH:mm:ss',
    'value-format': 'HH:mm:ss',
    regList: [],
    changeTag: true,
    document: 'https://element-plus.org/zh-CN/component/time-picker',
  } as TimePickerComponent,
  {
    label: '时间范围',
    tag: 'el-time-picker',
    tagIcon: 'time-range',
    defaultValue: null,
    span: 24,
    labelWidth: null,
    style: { width: '100%' },
    disabled: false,
    clearable: true,
    required: true,
    'is-range': true,
    'range-separator': '至',
    'start-placeholder': '开始时间',
    'end-placeholder': '结束时间',
    format: 'HH:mm:ss',
    'value-format': 'HH:mm:ss',
    regList: [],
    changeTag: true,
    document: 'https://element-plus.org/zh-CN/component/time-picker',
  } as TimePickerComponent,
  {
    label: '日期选择',
    tag: 'el-date-picker',
    tagIcon: 'date',
    placeholder: '请选择',
    defaultValue: null,
    type: 'date',
    span: 24,
    labelWidth: null,
    style: { width: '100%' },
    disabled: false,
    clearable: true,
    required: true,
    format: 'YYYY-MM-DD',
    'value-format': 'YYYY-MM-DD',
    readonly: false,
    regList: [],
    changeTag: true,
    document: 'https://element-plus.org/zh-CN/component/date-picker',
  } as DatePickerComponent,
  {
    label: '日期范围',
    tag: 'el-date-picker',
    tagIcon: 'date-range',
    defaultValue: null,
    span: 24,
    labelWidth: null,
    style: { width: '100%' },
    type: 'daterange',
    'range-separator': '至',
    'start-placeholder': '开始日期',
    'end-placeholder': '结束日期',
    disabled: false,
    clearable: true,
    required: true,
    format: 'YYYY-MM-DD',
    'value-format': 'YYYY-MM-DD',
    readonly: false,
    regList: [],
    changeTag: true,
    document: 'https://element-plus.org/zh-CN/component/date-picker',
  } as DatePickerComponent,
  {
    label: '评分',
    tag: 'el-rate',
    tagIcon: 'rate',
    defaultValue: 0,
    span: 24,
    labelWidth: null,
    style: {},
    max: 5,
    'allow-half': false,
    'show-text': false,
    'show-score': false,
    disabled: false,
    required: true,
    regList: [],
    changeTag: true,
    document: 'https://element-plus.org/zh-CN/component/rate',
  } as RateComponent,
  {
    label: '颜色选择',
    tag: 'el-color-picker',
    tagIcon: 'color',
    defaultValue: null,
    labelWidth: null,
    'show-alpha': false,
    'color-format': '',
    disabled: false,
    required: true,
    size: 'default',
    regList: [],
    changeTag: true,
    span: 24,
    document: 'https://element-plus.org/zh-CN/component/color-picker',
  } as ColorPickerComponent,
  {
    label: '上传',
    tag: 'el-upload',
    tagIcon: 'upload',
    action: 'https://jsonplaceholder.typicode.com/posts/',
    defaultValue: null,
    labelWidth: null,
    disabled: false,
    required: true,
    accept: '',
    name: 'file',
    'auto-upload': true,
    showTip: false,
    buttonText: '点击上传',
    fileSize: 2,
    sizeUnit: 'MB',
    'list-type': 'text',
    multiple: false,
    regList: [],
    changeTag: true,
    document: 'https://element-plus.org/zh-CN/component/upload',
    tip: '只能上传不超过 2MB 的文件',
    style: { width: '100%' },
    span: 24,
  } as UploadComponent,
];

export const layoutComponents: LayoutComponent[] = [
  {
    layout: 'rowFormItem',
    tagIcon: 'row',
    type: 'default',
    justify: 'start',
    align: 'top',
    label: '行容器',
    layoutTree: true,
    children: [],
    document: 'https://element-plus.org/zh-CN/component/layout',
  },
  {
    layout: 'colFormItem',
    label: '按钮',
    changeTag: true,
    labelWidth: null,
    tag: 'el-button',
    tagIcon: 'button',
    span: 24,
    default: '主要按钮',
    type: 'primary',
    icon: 'Search',
    size: 'default',
    disabled: false,
    document: 'https://element-plus.org/zh-CN/component/button',
  },
];

// 组件rule的触发方式，无触发方式的组件不生成rule
export const trigger: Record<string, string> = {
  'el-input': 'blur',
  'el-input-number': 'blur',
  'el-select': 'change',
  'el-radio-group': 'change',
  'el-checkbox-group': 'change',
  'el-cascader': 'change',
  'el-time-picker': 'change',
  'el-date-picker': 'change',
  'el-rate': 'change',
};
