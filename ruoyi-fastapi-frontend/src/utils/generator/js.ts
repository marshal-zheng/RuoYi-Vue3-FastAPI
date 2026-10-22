import type { GeneratorValue } from './types';
import { titleCase } from '@/utils/index';
import { trigger } from './config';
import { normalizeGeneratorFields, resolveGeneratorColumns } from './identity';
import { isElementIconName } from './icon-name';

// 文件大小单位映射接口
interface Units {
  [key: string]: string;
}

// 正则验证规则接口
interface RegRule {
  pattern: string;
  message: string;
}

// 选项接口
interface Option {
  label: string;
  value: string | number | boolean;
  disabled?: boolean;
}

// Props配置接口
interface PropsConfig {
  props: {
    value?: string;
    label?: string;
    children?: string;
    [key: string]: GeneratorValue;
  };
}

// 表单元素接口
interface FormElement {
  span?: number;
  full?: boolean;
  vModel?: string;
  tag: string;
  label?: string;
  placeholder?: string;
  defaultValue?: GeneratorValue;
  multiple?: boolean;
  required?: boolean;
  regList?: RegRule[];
  options?: Option[];
  dataType?: string;
  props?: PropsConfig;
  action?: string;
  'auto-upload'?: boolean;
  fileSize?: number;
  sizeUnit?: string;
  accept?: string;
  valueKey?: string;
  labelKey?: string;
  childrenKey?: string;
  children?: FormElement[];
  icon?: string;
  'prefix-icon'?: string;
  'suffix-icon'?: string;
  'list-type'?: string;
}

// 表单配置接口
interface FormConfig {
  columns?: 1 | 2 | 3;
  fields: FormElement[];
  formRef: string;
  formModel: string;
  formRules: string;
}

// 文件大小设置
const units: Units = {
  KB: '1024',
  MB: '1024 / 1024',
  GB: '1024 / 1024 / 1024',
};

/**
 * 生成js需要的数据
 * @param conf - 表单配置
 * @param type - 弹窗或表单类型
 * @returns 生成的JavaScript代码字符串
 */
export function makeUpJs(conf: FormConfig, type: string): string {
  conf = JSON.parse(JSON.stringify(conf));
  conf.fields = normalizeGeneratorFields(conf.fields);
  const dataList: string[] = [];
  const ruleList: string[] = [];
  const optionsList: string[] = [];
  const propsList: string[] = [];
  const methodList: string[] = [];
  const uploadVarList: string[] = [];

  conf.fields.forEach((el) => {
    buildAttributes(el, dataList, ruleList, optionsList, methodList, propsList, uploadVarList);
  });

  const script = buildexport(
    conf,
    type,
    dataList.join('\n'),
    ruleList.join('\n'),
    optionsList.join('\n'),
    uploadVarList.join('\n'),
    propsList.join('\n'),
    methodList.join('\n')
  );

  return script;
}

/**
 * 生成参数，包括表单数据表单验证数据，多选选项数据，上传数据等
 */
function buildAttributes(
  el: FormElement,
  dataList: string[],
  ruleList: string[],
  optionsList: string[],
  methodList: string[],
  propsList: string[],
  uploadVarList: string[]
): void {
  buildData(el, dataList);
  buildRules(el, ruleList);

  if (el.options && el.options.length) {
    buildOptions(el, optionsList);
    if (el.dataType === 'dynamic') {
      const model = `${el.vModel}Options`;
      const options = titleCase(model);
      buildOptionMethod(`get${options}`, model, methodList);
    }
  }

  if (el.props && el.props.props) {
    buildProps(el, propsList);
  }

  if (el.action && el.tag === 'el-upload') {
    uploadVarList.push(
      `
      // 上传请求路径
      const ${el.vModel}Action = ref('${el.action}')
      // 上传文件列表
      const ${el.vModel}fileList =  ref([])`
    );
    methodList.push(buildBeforeUpload(el));
    if (!el['auto-upload']) {
      methodList.push(buildSubmitUpload(el));
    }
  }

  if (el.children) {
    el.children.forEach((el2) => {
      buildAttributes(el2, dataList, ruleList, optionsList, methodList, propsList, uploadVarList);
    });
  }
}

/**
 * 生成表单数据formData
 * @param conf - 表单元素配置
 * @param dataList - 数据列表
 */
function buildData(conf: FormElement, dataList: string[]): void {
  if (conf.vModel === undefined) return;
  let defaultValue: string;
  if (typeof conf.defaultValue === 'string' && !conf.multiple) {
    defaultValue = JSON.stringify(conf.defaultValue);
  } else {
    defaultValue = `${JSON.stringify(conf.defaultValue)}`;
  }
  dataList.push(`${conf.vModel}: ${defaultValue},`);
}

/**
 * 生成表单验证数据rule
 * @param conf - 表单元素配置
 * @param ruleList - 验证数据列表
 */
function buildRules(conf: FormElement, ruleList: string[]): void {
  if (conf.vModel === undefined) return;
  const rules: string[] = [];
  if (trigger[conf.tag]) {
    if (conf.required) {
      const type = Array.isArray(conf.defaultValue) ? "type: 'array'," : '';
      let message = Array.isArray(conf.defaultValue)
        ? `请至少选择一个${conf.vModel}`
        : conf.placeholder;
      if (message === undefined) message = `${conf.label}不能为空`;
      rules.push(
        `{ required: true, ${type} message: '${message}', trigger: '${trigger[conf.tag]}' }`
      );
    }
    if (conf.regList && Array.isArray(conf.regList)) {
      conf.regList.forEach((item) => {
        if (item.pattern) {
          rules.push(
            `{ pattern: new RegExp(${item.pattern}), message: '${
              item.message
            }', trigger: '${trigger[conf.tag]}' }`
          );
        }
      });
    }
    ruleList.push(`${conf.vModel}: [${rules.join(',')}],`);
  }
}

/**
 * 生成选项数据，单选多选下拉等
 * @param conf - 表单元素配置
 * @param optionsList - 选项数据列表
 */
function buildOptions(conf: FormElement, optionsList: string[]): void {
  if (conf.vModel === undefined) return;
  if (conf.dataType === 'dynamic') {
    conf.options = [];
  }
  const str = `const ${conf.vModel}Options = ref(${JSON.stringify(conf.options)})`;
  optionsList.push(str);
}

/**
 * 生成方法
 * @param methodName - 方法名
 * @param model - 模型名
 * @param methodList - 方法列表
 */
function buildOptionMethod(methodName: string, model: string, methodList: string[]): void {
  const str = `function ${methodName}() {
    // TODO 发起请求获取数据
    ${model}.value
  }`;
  methodList.push(str);
}

/**
 * 生成表单组件需要的props设置，如级联组件
 * @param conf - 表单元素配置
 * @param propsList - props列表
 */
function buildProps(conf: FormElement, propsList: string[]): void {
  if (conf.dataType === 'dynamic') {
    if (conf.valueKey !== 'value') conf.props!.props.value = conf.valueKey;
    if (conf.labelKey !== 'label') conf.props!.props.label = conf.labelKey;
    if (conf.childrenKey !== 'children') conf.props!.props.children = conf.childrenKey;
  }
  const str = `
  // props设置
  const ${conf.vModel}Props = ref(${JSON.stringify(conf.props!.props)})`;
  propsList.push(str);
}

/**
 * 生成上传组件的相关内容
 * @param conf - 表单元素配置
 * @returns 上传前验证函数字符串
 */
function buildBeforeUpload(conf: FormElement): string {
  const unitNum = units[conf.sizeUnit!];
  let rightSizeCode = '';
  let acceptCode = '';
  const returnList: string[] = [];
  if (conf.fileSize) {
    rightSizeCode = `let isRightSize = file.size / ${unitNum} < ${conf.fileSize}
    if(!isRightSize){
      ElMessage.error('文件大小超过 ${conf.fileSize}${conf.sizeUnit}')
    }`;
    returnList.push('isRightSize');
  }
  if (conf.accept) {
    acceptCode = `let isAccept = new RegExp('${conf.accept}').test(file.type)
    if(!isAccept){
      ElMessage.error('应该选择${conf.accept}类型的文件')
    }`;
    returnList.push('isAccept');
  }
  const str = `
  /**
   * 上传之前的文件判断
   * @param file - 上传的文件
   * @returns 是否通过验证
   */  
  function ${conf.vModel}BeforeUpload(file) {
    ${rightSizeCode}
    ${acceptCode}
    return ${returnList.join('&&')}
  }`;
  return returnList.length ? str : '';
}

/**
 * 生成提交表单方法
 * @param conf - 表单元素配置
 * @returns 提交上传函数字符串
 */
function buildSubmitUpload(conf: FormElement): string {
  const str = `function submitUpload() {
    this.$refs['${conf.vModel}'].submit()
  }`;
  return str;
}

/**
 * 组装js代码
 * @param conf - 表单配置
 * @param type - 类型
 * @param data - 数据
 * @param rules - 验证规则
 * @param selectOptions - 选项
 * @param uploadVar - 上传变量
 * @param props - 属性
 * @param methods - 方法
 * @returns 完整的JavaScript代码字符串
 */
function buildexport(
  conf: FormConfig,
  type: string,
  data: string,
  rules: string,
  selectOptions: string,
  uploadVar: string,
  props: string,
  methods: string
): string {
  const names = new Set(['ElForm', 'ElFormItem', 'ElButton']);
  const zxNames = new Set<string>();
  const iconNames = new Set<string>();
  const visit = (fields: FormElement[]) =>
    fields.forEach((field) => {
      const name = field.tag
        .split('-')
        .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
        .join('');
      if (field.tag.startsWith('zx-')) zxNames.add(name);
      else if (field.tag.startsWith('el-')) names.add(name);
      if (field.tag === 'el-select') names.add('ElOption');
      if (field.tag === 'el-radio-group') {
        names.add('ElRadio');
        names.add('ElRadioButton');
      }
      if (field.tag === 'el-checkbox-group') {
        names.add('ElCheckbox');
        names.add('ElCheckboxButton');
      }
      if (field.tag === 'el-upload') {
        names.add('ElMessage');
        if (field['list-type'] === 'picture-card') {
          names.add('ElIcon');
          iconNames.add('Plus');
        } else iconNames.add('Upload');
      }
      for (const key of ['icon', 'prefix-icon', 'suffix-icon'] as const) {
        const icon = field[key];
        if (isElementIconName(icon)) iconNames.add(icon);
      }
      if (field.children) visit(field.children);
    });
  visit(conf.fields);
  if (type === 'dialog') zxNames.add('ZxDialog');
  else {
    names.add('ElRow');
    names.add('ElCol');
  }
  let str = `
    import { ref, reactive, computed, watch } from 'vue'
    import { ${[...names].join(', ')} } from 'element-plus'
    ${iconNames.size ? `import { ${[...iconNames].sort().join(', ')} } from '@element-plus/icons-vue'` : ''}
    ${zxNames.size ? `import { ${[...zxNames].join(', ')} } from '@zxio/zxui/core'` : ''}
    ${type === 'dialog' ? "import { FormGrid, useFormDialog } from '@/components/ui/FormDialog'" : ''}
    const ${conf.formRef} = ref()
    const ${conf.formRules} = reactive({ ${rules} })
    ${selectOptions}
    ${uploadVar}
    ${props}
    ${methods}
  `;
  if (type === 'dialog') {
    str += `
      const dialogVisible = defineModel({ default: false })
      const emit = defineEmits(['confirm'])
      const { state, dialogProps, dialogEvents, formProps, layoutProps, open, close } = useFormDialog({
        columns: ${resolveGeneratorColumns(conf)},
        title: '表单',
        formRef: ${conf.formRef},
        defaultData: () => ({ ${data} }),
        onConfirm: async (value) => {
          // TODO 提交表单；返回 false 可保留弹框。
          emit('confirm', value)
        },
      })
      const ${conf.formModel} = computed(() => state.data)
      watch(dialogVisible, (visible) => {
        if (visible !== state.visible) visible ? open() : close()
      }, { immediate: true })
      watch(() => state.visible, (visible) => { dialogVisible.value = visible })
    `;
  } else {
    str += `
      const ${conf.formModel} = reactive({ ${data} })
      async function submitForm() {
        const valid = await ${conf.formRef}.value.validate().catch(() => false)
        if (!valid) return
        // TODO 提交表单。
      }
      function resetForm() { ${conf.formRef}.value.resetFields() }
    `;
  }
  return str;
}

export type { FormElement, FormConfig, RegRule, Option, PropsConfig, Units };
