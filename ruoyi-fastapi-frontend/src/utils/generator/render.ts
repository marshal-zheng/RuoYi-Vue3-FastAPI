import { isRecord } from '@/types/http-contract';
import { defineComponent, h, resolveComponent } from 'vue';
import { makeMap } from '@/utils/index';
import { ZxInput } from '@zxio/zxui/input';
import {
  ElButton,
  ElCascader,
  ElCheckbox,
  ElCheckboxButton,
  ElCheckboxGroup,
  ElColorPicker,
  ElDatePicker,
  ElIcon,
  ElInputNumber,
  ElOption,
  ElRadio,
  ElRadioButton,
  ElRadioGroup,
  ElRate,
  ElSelect,
  ElSlider,
  ElSwitch,
  ElTimePicker,
  ElUpload,
} from 'element-plus';
import { Plus } from '@element-plus/icons-vue';
import { generatorTags, resolveGeneratorTag } from './identity';
import type { Component, PropType, CSSProperties, VNodeChild } from 'vue';

// Saved designs keep their tag identity; preview owns the concrete components.
const generatorComponents: Record<string, Component> = {
  [generatorTags.input]: ZxInput,
  'el-button': ElButton,
  'el-cascader': ElCascader,
  'el-checkbox-group': ElCheckboxGroup,
  'el-color-picker': ElColorPicker,
  'el-date-picker': ElDatePicker,
  'el-input-number': ElInputNumber,
  'el-radio-group': ElRadioGroup,
  'el-rate': ElRate,
  'el-select': ElSelect,
  'el-slider': ElSlider,
  'el-switch': ElSwitch,
  'el-time-picker': ElTimePicker,
  'el-upload': ElUpload,
};

// 选项接口
interface Option {
  label: string;
  value: string | number | boolean;
  disabled?: boolean;
}

// 表单元素配置接口
interface FormElementConfig {
  tag: string;
  default?: string;
  prepend?: string;
  append?: string;
  options?: Option[];
  optionType?: string;
  border?: boolean;
  'list-type'?: string;
  showTip?: boolean;
  fileSize?: number;
  sizeUnit?: string;
  accept?: string;
  buttonText?: string;
  [key: string]: unknown;
}

// 数据对象接口
interface DataObject {
  attrs: Record<string, unknown>;
  props: Record<string, unknown>;
  on: Record<string, unknown>;
  style: CSSProperties;
}

// 子组件渲染函数类型
type ChildRenderFunction = (
  h: (typeof import('vue'))['h'],
  conf: FormElementConfig,
  key: string
) => VNodeChild;

// 插槽渲染函数类型
type SlotRenderFunction = (
  h: (typeof import('vue'))['h'],
  conf: FormElementConfig,
  key: string
) => (() => VNodeChild) | undefined;

// 子组件配置接口
interface ComponentChildConfig {
  [componentName: string]: {
    [key: string]: ChildRenderFunction;
  };
}

// 插槽配置接口
interface ComponentSlotConfig {
  [componentName: string]: {
    [key: string]: SlotRenderFunction;
  };
}

const isAttr = makeMap(
  'accept,accept-charset,accesskey,action,align,alt,async,autocomplete,' +
    'autofocus,autoplay,autosave,bgcolor,border,buffered,challenge,charset,' +
    'checked,cite,class,code,codebase,color,cols,colspan,content,http-equiv,' +
    'name,contenteditable,contextmenu,controls,coords,data,datetime,default,' +
    'defer,dir,dirname,disabled,download,draggable,dropzone,enctype,method,for,' +
    'form,formaction,headers,height,hidden,high,href,hreflang,http-equiv,' +
    'icon,id,ismap,itemprop,keytype,kind,label,lang,language,list,loop,low,' +
    'manifest,max,maxlength,media,method,GET,POST,min,multiple,email,file,' +
    'muted,name,novalidate,open,optimum,pattern,ping,placeholder,poster,' +
    'preload,radiogroup,readonly,rel,required,reversed,rows,rowspan,sandbox,' +
    'scope,scoped,seamless,selected,shape,size,type,text,password,sizes,span,' +
    'spellcheck,src,srcdoc,srclang,srcset,start,step,style,summary,tabindex,' +
    'target,title,type,usemap,value,width,wrap' +
    'prefix-icon'
);

const isNotProps = makeMap(
  'layout,prepend,append,regList,tag,document,changeTag,defaultValue,vModel,span,full,labelWidth'
);

// 子组件配置
const componentChild: ComponentChildConfig = {
  'el-button': {
    default(...[, conf]) {
      return conf.default;
    },
  },
  'el-select': {
    options(h, conf) {
      return conf.options!.map((item) =>
        h(ElOption, {
          label: item.label,
          value: item.value,
        })
      );
    },
  },
  'el-radio-group': {
    options(h, conf) {
      return conf.optionType === 'button'
        ? conf.options!.map((item) =>
            h(
              ElRadioButton,
              {
                label: item.value,
              },
              () => item.label
            )
          )
        : conf.options!.map((item) =>
            h(
              ElRadio,
              {
                label: item.value,
                border: conf.border,
              },
              () => item.label
            )
          );
    },
  },
  'el-checkbox-group': {
    options(h, conf) {
      return conf.optionType === 'button'
        ? conf.options!.map((item) =>
            h(
              ElCheckboxButton,
              {
                label: item.value,
              },
              () => item.label
            )
          )
        : conf.options!.map((item) =>
            h(
              ElCheckbox,
              {
                label: item.value,
                border: conf.border,
              },
              () => item.label
            )
          );
    },
  },
  'el-upload': {
    'list-type': (h, conf) => {
      const option: Record<string, unknown> = {};
      // if (conf.showTip) {
      //   tip = h('div', {
      //     class: "el-upload__tip"
      //   }, () => '只能上传不超过' + conf.fileSize + conf.sizeUnit + '的' + conf.accept + '文件')
      // }
      if (conf['list-type'] === 'picture-card') {
        return h(ElIcon, option, () => h(Plus));
      } else {
        // option.size = "small"
        option.type = 'primary';
        option.icon = 'Upload';
        return h(ElButton, option, () => conf.buttonText);
      }
    },
  },
};

// 插槽配置
const componentSlot: ComponentSlotConfig = {
  [generatorTags.input]: {
    prepend: (h, conf) => () => h('span', conf.prepend),
    append: (h, conf) => () => h('span', conf.append),
  },
  'el-upload': {
    tip: (h, conf) => {
      if (conf.showTip) {
        return () =>
          h(
            'div',
            {
              class: 'el-upload__tip',
            },
            '只能上传不超过' + conf.fileSize + conf.sizeUnit + '的' + conf.accept + '文件'
          );
      }
      return undefined;
    },
  },
};

export default defineComponent({
  name: 'FormElementRender',
  inheritAttrs: false,
  emits: ['update:modelValue'],
  // 使用 render 函数
  render() {
    const dataObject: DataObject = {
      attrs: {},
      props: {},
      on: {},
      style: {},
    };
    const confClone: FormElementConfig = JSON.parse(JSON.stringify(this.conf));
    confClone.tag = resolveGeneratorTag(confClone.tag);
    const children: VNodeChild[] = [];
    const slot: Record<string, () => VNodeChild> = {};

    const childObjs = componentChild[confClone.tag];
    if (childObjs) {
      Object.keys(childObjs).forEach((key) => {
        const childFunc = childObjs[key];
        if (confClone[key]) {
          const result = childFunc(h, confClone, key);
          if (Array.isArray(result)) {
            children.push(...result);
          } else {
            children.push(result);
          }
        }
      });
    }

    const slotObjs = componentSlot[confClone.tag];
    if (slotObjs) {
      Object.keys(slotObjs).forEach((key) => {
        const childFunc = slotObjs[key];
        if (confClone[key]) {
          const slotFunc = childFunc(h, confClone, key);
          if (slotFunc) {
            slot[key] = slotFunc;
          }
        }
      });
    }

    Object.keys(confClone).forEach((key) => {
      const val = confClone[key];
      if (key === 'attrs' || key === 'props' || key === 'on') {
        if (isRecord(val)) dataObject[key] = val;
      } else if (key === 'style') {
        if (isRecord(val)) {
          dataObject.style = Object.fromEntries(
            Object.entries(val).filter(
              (entry): entry is [string, string | number] =>
                typeof entry[1] === 'string' || typeof entry[1] === 'number'
            )
          );
        }
      } else if (isAttr(key)) {
        dataObject.attrs[key] = val;
      } else if (!isNotProps(key)) {
        dataObject.props[key] = val;
      }
    });

    if (children.length > 0) {
      slot.default = () => children;
    }

    return h(
      generatorComponents[confClone.tag] ?? resolveComponent(confClone.tag),
      {
        ...this.$attrs,
        ...dataObject.props,
        ...dataObject.attrs,
        modelValue: this.$attrs.modelValue,
        'onUpdate:modelValue': (value: unknown) => this.$emit('update:modelValue', value),
        style: {
          ...dataObject.style,
        },
      },
      Object.keys(slot).length > 0 ? slot : undefined
    );
  },
  props: {
    conf: {
      type: Object as PropType<FormElementConfig>,
      required: true,
    },
  },
});

export type {
  FormElementConfig,
  Option,
  DataObject,
  ChildRenderFunction,
  SlotRenderFunction,
  ComponentChildConfig,
  ComponentSlotConfig,
};
