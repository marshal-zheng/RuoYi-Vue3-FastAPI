import { defineComponent, h, resolveComponent, VNode } from 'vue';
import { makeMap } from '@/utils/index';
import type { PropType } from 'vue';

// 选项接口
interface Option {
  label: string;
  value: any;
  disabled?: boolean;
}

// 表单元素配置接口
interface FormElementConfig {
  tag: string;
  options?: Option[];
  optionType?: string;
  border?: boolean;
  'list-type'?: string;
  showTip?: boolean;
  fileSize?: number;
  sizeUnit?: string;
  accept?: string;
  buttonText?: string;
  [key: string]: any;
}

// 数据对象接口
interface DataObject {
  attrs: Record<string, any>;
  props: Record<string, any>;
  on: Record<string, any>;
  style: Record<string, any>;
}

// 子组件渲染函数类型
type ChildRenderFunction = (h: any, conf: FormElementConfig, key: string) => VNode | VNode[];

// 插槽渲染函数类型
type SlotRenderFunction = (h: any, conf: FormElementConfig, key: string) => (() => VNode) | undefined;

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

const isNotProps = makeMap('layout,prepend,regList,tag,document,changeTag,defaultValue');

/**
 * 使用 v-model 的辅助函数
 * @param props - 组件属性
 * @param emit - 事件发射器
 * @returns v-model 配置对象
 */
function useVModel(props: any, emit: any): Record<string, any> {
  return {
    modelValue: props.defaultValue,
    'onUpdate:modelValue': (val: any) => emit('update:modelValue', val),
  };
}

// 子组件配置
const componentChild: ComponentChildConfig = {
  'el-button': {
    default(h, conf, key) {
      return conf[key];
    },
  },
  'el-select': {
    options(h, conf, key) {
      return conf.options!.map(item =>
        h(resolveComponent('el-option'), {
          label: item.label,
          value: item.value,
        })
      );
    },
  },
  'el-radio-group': {
    options(h, conf, key) {
      return conf.optionType === 'button'
        ? conf.options!.map(item =>
            h(
              resolveComponent('el-radio-button'),
              {
                label: item.value,
              },
              () => item.label
            )
          )
        : conf.options!.map(item =>
            h(
              resolveComponent('el-radio'),
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
    options(h, conf, key) {
      return conf.optionType === 'button'
        ? conf.options!.map(item =>
            h(
              resolveComponent('el-checkbox-button'),
              {
                label: item.value,
              },
              () => item.label
            )
          )
        : conf.options!.map(item =>
            h(
              resolveComponent('el-checkbox'),
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
    'list-type': (h, conf, key) => {
      const option: Record<string, any> = {};
      // if (conf.showTip) {
      //   tip = h('div', {
      //     class: "el-upload__tip"
      //   }, () => '只能上传不超过' + conf.fileSize + conf.sizeUnit + '的' + conf.accept + '文件')
      // }
      if (conf['list-type'] === 'picture-card') {
        return h(resolveComponent('el-icon'), option, () => h(resolveComponent('Plus')));
      } else {
        // option.size = "small"
        option.type = 'primary';
        option.icon = 'Upload';
        return h(resolveComponent('el-button'), option, () => conf.buttonText);
      }
    },
  },
};

// 插槽配置
const componentSlot: ComponentSlotConfig = {
  'el-upload': {
    tip: (h, conf, key) => {
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
  // 使用 render 函数
  render() {
    const dataObject: DataObject = {
      attrs: {},
      props: {},
      on: {},
      style: {},
    };
    const confClone: FormElementConfig = JSON.parse(JSON.stringify(this.conf));
    const children: VNode[] = [];
    const slot: Record<string, () => VNode | VNode[]> = {};
    
    const childObjs = componentChild[confClone.tag];
    if (childObjs) {
      Object.keys(childObjs).forEach(key => {
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
      Object.keys(slotObjs).forEach(key => {
        const childFunc = slotObjs[key];
        if (confClone[key]) {
          const slotFunc = childFunc(h, confClone, key);
          if (slotFunc) {
            slot[key] = slotFunc;
          }
        }
      });
    }
    
    Object.keys(confClone).forEach(key => {
      const val = confClone[key];
      if (dataObject[key as keyof DataObject]) {
        (dataObject[key as keyof DataObject] as any) = val;
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
      resolveComponent(this.conf.tag),
      {
        modelValue: this.$attrs.modelValue,
        ...dataObject.props,
        ...dataObject.attrs,
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