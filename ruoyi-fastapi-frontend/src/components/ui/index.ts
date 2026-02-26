/**
 * UI Components Unified Export
 *
 * All pure UI components (no API calls) are exported from here.
 * Usage: import { Pagination, SvgIcon } from '@/components/ui'
 */

// Layout & Navigation
export { default as Breadcrumb } from './Breadcrumb/index.vue';
export { default as Hamburger } from './Hamburger/index.vue';
export { default as HeaderSearch } from './HeaderSearch/index.vue';
export { default as TopNav } from './TopNav/index.vue';
export { default as ParentView } from './ParentView/index.vue';

// Content Display
export { default as ContentDetailWrap } from './ContentDetailWrap/index.vue';
export { default as FloatingPanel } from './FloatingPanel/index.vue';
export { default as iFrame } from './iFrame/index.vue';
export { default as DictTag } from './DictTag/index.vue';

// Media & Assets
export { default as SvgIcon } from './SvgIcon/index.vue';
export { default as ImagePreview } from './ImagePreview/index.vue';
export { default as ImageUpload } from './ImageUpload/index.vue';
export { default as FileUpload } from './FileUpload/index.vue';

// Editors
export { default as Editor } from './Editor/index.vue';
export { Editor as RichEditor } from './RichEditor/index';

// Form & Input
export { default as IconSelect } from './IconSelect/index.vue';
export { default as Crontab } from './Crontab/index.vue';

// Table
export { default as Pagination } from './Pagination/index.vue';
export { default as RightToolbar } from './RightToolbar/index.vue';
export { default as VxeSchemaTable } from './VxeSchemaTable/index.vue';

// Settings & Tools
export { default as Screenfull } from './Screenfull/index.vue';
export { default as SizeSelect } from './SizeSelect/index.vue';

// Documentation & Demo
export { default as RuoYiDoc } from './RuoYi/Doc/index.vue';
export { default as RuoYiGit } from './RuoYi/Git/index.vue';
export { default as ThemeDemo } from './ThemeDemo/index.vue';
export { default as ThemeValidation } from './ThemeValidation/index.vue';

// VXE Table Validation (composable + component)
export * from './VxeTableValidation';
