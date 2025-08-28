// CSS 样式映射接口
interface StylesMap {
  [key: string]: string;
}

// 表单元素接口（简化版，用于 CSS 生成）
interface FormElement {
  tag: string;
  children?: FormElement[];
}

// 表单配置接口（简化版，用于 CSS 生成）
interface FormConfig {
  fields: FormElement[];
}

// 预定义的样式映射
const styles: StylesMap = {
  'el-rate': '.el-rate{display: inline-block; vertical-align: text-top;}',
  'el-upload': '.el-upload__tip{line-height: 1.2;}',
};

/**
 * 递归添加CSS样式到样式列表中
 * @param cssList - CSS样式列表
 * @param el - 表单元素
 */
function addCss(cssList: string[], el: FormElement): void {
  const css = styles[el.tag];
  css && cssList.indexOf(css) === -1 && cssList.push(css);
  if (el.children) {
    el.children.forEach(el2 => addCss(cssList, el2));
  }
}

/**
 * 生成表单的CSS样式
 * @param conf - 表单配置对象
 * @returns 生成的CSS样式字符串
 */
export function makeUpCss(conf: FormConfig): string {
  const cssList: string[] = [];
  conf.fields.forEach(el => addCss(cssList, el));
  return cssList.join('\n');
}

export { styles, addCss };
export type { StylesMap, FormElement, FormConfig };