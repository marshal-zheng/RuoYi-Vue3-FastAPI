<script setup lang="ts">
import { onBeforeUnmount, computed, PropType, unref, nextTick, ref, watch, shallowRef } from 'vue';
import { Editor, Toolbar } from '@wangeditor/editor-for-vue';
import { IDomEditor, IEditorConfig } from '@wangeditor/editor';
import { propTypes } from '@/utils/propTypes';
import { ElMessage } from 'element-plus';

const props = defineProps({
  editorId: propTypes.string.def('wangeEditor-1'),
  height: propTypes.oneOfType([Number, String]).def('500px'),
  editorConfig: {
    type: Object as PropType<IEditorConfig>,
    default: () => undefined,
  },
  modelValue: propTypes.string.def(''),
  // 是否显示工具栏
  showToolbar: propTypes.bool.def(true),
  // 是否显示边框
  bordered: propTypes.bool.def(true),
  // 是否自动高度（内容撑起，无内部滚动条）
  autoHeight: propTypes.bool.def(false),
});

const emit = defineEmits(['change', 'update:modelValue']);

// 编辑器实例，必须用 shallowRef
const editorRef = shallowRef<IDomEditor>();

const valueHtml = ref('');

watch(
  () => props.modelValue,
  (val: string) => {
    if (val === unref(valueHtml)) return;
    valueHtml.value = val;
  }
);

// 监听
watch(
  () => valueHtml.value,
  (val: string) => {
    emit('update:modelValue', val);
  }
);

const handleCreated = (editor: IDomEditor) => {
  editorRef.value = editor;
  valueHtml.value = props.modelValue;
};

// 编辑器配置
const editorConfig = computed((): IEditorConfig => {
  const baseConfig = {
    readOnly: false,
    customAlert: (s: string, t: string) => {
      switch (t) {
        case 'success':
          ElMessage.success(s);
          break;
        case 'info':
          ElMessage.info(s);
          break;
        case 'warning':
          ElMessage.warning(s);
          break;
        case 'error':
          ElMessage.error(s);
          break;
        default:
          ElMessage.info(s);
          break;
      }
    },
    autoFocus: false,
    // autoHeight 模式下禁用内部滚动，让内容自然撑开
    scroll: props.autoHeight ? false : true,
    uploadImgShowBase64: true,
  };
  return Object.assign(baseConfig, props.editorConfig || {});
});

const editorStyle = computed(() => {
  // autoHeight 模式下不设置固定高度，让内容自然撑开
  if (props.autoHeight) {
    return {};
  }
  return {
    height: typeof props.height === 'number' ? `${props.height}px` : props.height,
  };
});

// 容器样式类
const containerClass = computed(() => {
  const classes = ['rich-editor-container'];
  if (props.bordered) {
    classes.push('border-1 border-solid border-[var(--el-border-color)]');
  }
  if (props.autoHeight) {
    classes.push('auto-height-mode');
  }
  classes.push('z-10');
  return classes.join(' ');
});

// 回调函数
const handleChange = (editor: IDomEditor) => {
  emit('change', editor);
};

// 组件销毁时，及时销毁编辑器
onBeforeUnmount(() => {
  const editor = unref(editorRef.value);

  // 销毁，并移除 editor
  editor?.destroy();
});

const getEditorRef = async (): Promise<IDomEditor> => {
  await nextTick();
  return unref(editorRef.value) as IDomEditor;
};

defineExpose({
  getEditorRef,
});
</script>

<template>
  <div :class="containerClass">
    <!-- 工具栏 -->
    <Toolbar
      v-if="showToolbar"
      :editor="editorRef"
      :editorId="editorId"
      class="border-0 b-b-1 border-solid border-[var(--el-border-color)]"
    />
    <!-- 编辑器 -->
    <Editor
      v-model="valueHtml"
      :editorId="editorId"
      :defaultConfig="editorConfig"
      :style="editorStyle"
      @on-change="handleChange"
      @on-created="handleCreated"
    />
  </div>
</template>

<style src="@wangeditor/editor/dist/css/style.css"></style>

<style scoped>
/* The application owns this third-party editor adapter. Content's explicit
   inline colors keep their precedence; only the editor's default UI is themed. */
.rich-editor-container {
  --w-e-textarea-bg-color: var(--zx-semantic-surface-card-fill);
  --w-e-textarea-color: var(--zx-semantic-surface-card-on-text);
  --w-e-textarea-border-color: var(--zx-semantic-border-default);
  --w-e-textarea-slight-border-color: var(--zx-semantic-border-subtle);
  --w-e-textarea-slight-color: var(--zx-semantic-text-secondary);
  --w-e-textarea-slight-bg-color: var(--zx-semantic-fill-subtle);
  --w-e-textarea-selected-border-color: var(--zx-semantic-accent-base);
  --w-e-textarea-handler-bg-color: var(--zx-semantic-accent-base);
  --w-e-toolbar-bg-color: var(--zx-semantic-surface-header-fill);
  --w-e-toolbar-color: var(--zx-semantic-surface-header-on-text);
  --w-e-toolbar-active-color: var(--zx-semantic-surface-selected-on-text);
  --w-e-toolbar-active-bg-color: var(--zx-semantic-surface-selected-fill);
  --w-e-toolbar-disabled-color: var(--zx-semantic-text-disabled);
  --w-e-toolbar-border-color: var(--zx-semantic-border-default);
  --w-e-modal-button-bg-color: var(--zx-semantic-surface-field-fill);
  --w-e-modal-button-border-color: var(--zx-semantic-border-control);
}

/* Toolbar geometry follows density; stored document layout is independent. */
:deep(.w-e-bar-divider) {
  height: calc(var(--zx-semantic-spacing-control-y) * 3 + 16px);
}
:deep(.w-e-bar-item) {
  height: auto;
  padding-block: max(2px, calc(var(--zx-semantic-spacing-control-y) / 2));
}
:deep(.w-e-bar-item button),
:deep(.w-e-modal button) {
  height: calc(var(--zx-semantic-spacing-control-y) * 2 + 16px);
}
:deep(.w-e-select-list),
:deep(.w-e-drop-panel) {
  top: 100%;
  margin-top: 0;
}
:deep(.w-e-select-list ul li) {
  padding-block: max(2px, calc(var(--zx-semantic-spacing-control-y) - 1px));
}
:deep(.w-e-drop-panel) {
  padding-block: calc(var(--zx-semantic-spacing-control-y) + 2px);
}
:deep(.w-e-modal) {
  padding-top: calc(var(--zx-semantic-spacing-control-y) * 2 + 4px);
}
:deep(.w-e-modal input[type='text']),
:deep(.w-e-modal input[type='number']),
:deep(.w-e-modal textarea) {
  padding-block: max(2px, calc(var(--zx-semantic-spacing-control-y) - 3.5px));
}

/* 基础编辑器样式 */
:deep(.w-e-text-container) {
  font-family:
    'Segoe UI',
    'Microsoft YaHei',
    'PingFang SC',
    -apple-system,
    BlinkMacSystemFont,
    sans-serif;
  font-size: 14px;
  line-height: 1.8;
  color: var(--zx-semantic-surface-card-on-text);
}

:deep(.w-e-text-container [data-slate-editor]) {
  padding: 16px 20px;
  caret-color: var(--zx-semantic-surface-card-on-text);
}

:deep(.w-e-text-container [data-slate-editor] h1) {
  font-size: 26px;
  margin: 24px 0 16px;
  font-weight: 600;
  color: var(--zx-semantic-surface-card-on-text);
  line-height: 1.4;
}

:deep(.w-e-text-container [data-slate-editor] h2) {
  font-size: 22px;
  margin: 20px 0 14px;
  font-weight: 600;
  color: var(--zx-semantic-surface-card-on-text);
  line-height: 1.4;
}

:deep(.w-e-text-container [data-slate-editor] h3) {
  font-size: 18px;
  margin: 18px 0 12px;
  font-weight: 600;
  color: var(--zx-semantic-surface-card-on-text);
  line-height: 1.4;
}

:deep(.w-e-text-container [data-slate-editor] h4) {
  font-size: 16px;
  margin: 16px 0 10px;
  font-weight: 600;
  color: var(--zx-semantic-surface-card-on-text);
  line-height: 1.4;
}

:deep(.w-e-text-container [data-slate-editor] h5) {
  font-size: 14px;
  margin: 14px 0 8px;
  font-weight: 600;
  color: var(--zx-semantic-surface-card-on-text);
  line-height: 1.4;
}

:deep(.w-e-text-container [data-slate-editor] p) {
  margin: 0 0 12px;
  text-align: justify;
}

:deep(.w-e-text-container [data-slate-editor] ul) {
  list-style-type: disc;
  margin: 12px 0;
  padding-left: 32px;
}

:deep(.w-e-text-container [data-slate-editor] ol) {
  list-style-type: decimal;
  margin: 12px 0;
  padding-left: 32px;
}

:deep(.w-e-text-container [data-slate-editor] li) {
  margin: 6px 0;
}

:deep(.w-e-text-container [data-slate-editor] blockquote) {
  border-left: 4px solid var(--zx-semantic-border-default);
  padding: 12px 16px;
  margin: 16px 0;
  background: var(--zx-semantic-fill-subtle);
  color: var(--zx-semantic-text-secondary);
}

:deep(.w-e-text-container [data-slate-editor] table) {
  border-collapse: collapse;
  width: 100%;
  margin: 16px 0;
}

:deep(.w-e-text-container [data-slate-editor] th),
:deep(.w-e-text-container [data-slate-editor] td) {
  border: 1px solid var(--zx-semantic-border-default);
  padding: 10px 12px;
  text-align: left;
}

:deep(.w-e-text-container [data-slate-editor] th) {
  background: var(--zx-semantic-fill-subtle);
  font-weight: 600;
}

:deep(.w-e-text-container [data-slate-editor] code) {
  background: var(--zx-semantic-fill-subtle);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
  color: var(--zx-semantic-text-primary);
}

:deep(.w-e-text-container [data-slate-editor] pre) {
  background: var(--zx-semantic-fill-subtle);
  padding: 16px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 16px 0;
}

:deep(.w-e-text-container [data-slate-editor] pre code) {
  background: transparent;
  padding: 0;
  color: inherit;
}

:deep(.w-e-text-container [data-slate-editor] a) {
  color: var(--zx-semantic-accent-on-surface, var(--zx-semantic-text-primary));
  text-decoration: none;
}

:deep(.w-e-text-container [data-slate-editor] a:hover) {
  text-decoration: underline;
}

:deep(.w-e-text-container [data-slate-editor] img) {
  max-width: 100%;
  border-radius: 4px;
  margin: 12px 0;
}

:deep(.w-e-text-container [data-slate-editor] hr) {
  border: none;
  border-top: 1px solid var(--zx-semantic-border-default);
  margin: 24px 0;
}

/* 自动高度模式样式：内容撑起，无内部滚动条，Word风格 */
.auto-height-mode {
  background: transparent;
}

.auto-height-mode :deep(.w-e-text-container) {
  min-height: 100% !important; /* Ensure it fills the parent */
  height: auto !important;
  overflow: visible !important;
  background: var(--zx-semantic-surface-card-fill);
  border-radius: 2px;
  /* Add word-break to prevent overflow */
  word-break: break-word;
  display: flex;
  flex-direction: column;
}

.auto-height-mode :deep(.w-e-scroll) {
  overflow: visible !important;
  height: auto !important;
  min-height: 100% !important;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.auto-height-mode :deep([data-slate-editor]) {
  min-height: 100% !important;
  padding: 32px 40px;
  /* Ensure text wraps */
  word-break: break-word;
  white-space: pre-wrap;
  flex: 1;
}
</style>
