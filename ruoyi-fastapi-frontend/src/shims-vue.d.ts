declare module '*.vue' {
  import type { DefineComponent } from 'vue';
  const component: DefineComponent;
  export default component;
}

// The package publishes these declarations but omits its types condition from exports.
// Consume the shipped declarations rather than inventing permissive component props.
declare module '@wangeditor/editor-for-vue' {
  export const Editor: (typeof import('../node_modules/@wangeditor/editor-for-vue/dist/src/index'))['Editor'];
  export const Toolbar: (typeof import('../node_modules/@wangeditor/editor-for-vue/dist/src/index'))['Toolbar'];
}

declare module '@/layout/index' {
  const component: (typeof import('@/layout/index.vue'))['default'];
  export default component;
}

declare module '@/layout/components/InnerLink' {
  const component: (typeof import('@/layout/components/InnerLink/index.vue'))['default'];
  export default component;
}

declare module '@/components/ui/ParentView' {
  const component: (typeof import('@/components/ui/ParentView/index.vue'))['default'];
  export default component;
}

declare module '@/components/ui/SvgIcon' {
  const component: (typeof import('@/components/ui/SvgIcon/index.vue'))['default'];
  export default component;
}

declare module '@/components/ui/Pagination' {
  const component: (typeof import('@/components/ui/Pagination/index.vue'))['default'];
  export default component;
}

declare module '@/components/ui/RightToolbar' {
  const component: (typeof import('@/components/ui/RightToolbar/index.vue'))['default'];
  export default component;
}

declare module '@/components/ui/Editor' {
  const component: (typeof import('@/components/ui/Editor/index.vue'))['default'];
  export default component;
}

declare module '@/components/ui/FileUpload' {
  const component: (typeof import('@/components/ui/FileUpload/index.vue'))['default'];
  export default component;
}

declare module '@/components/ui/ImageUpload' {
  const component: (typeof import('@/components/ui/ImageUpload/index.vue'))['default'];
  export default component;
}

declare module '@/components/ui/ImagePreview' {
  const component: (typeof import('@/components/ui/ImagePreview/index.vue'))['default'];
  export default component;
}

declare module '@/components/ui/DictTag' {
  const component: (typeof import('@/components/ui/DictTag/index.vue'))['default'];
  export default component;
}
