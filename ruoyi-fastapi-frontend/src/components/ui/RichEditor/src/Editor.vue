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
  color: #333;
}

:deep(.w-e-text-container [data-slate-editor]) {
  padding: 16px 20px;
  caret-color: #1a1a1a;
}

:deep(.w-e-text-container [data-slate-editor] h1) {
  font-size: 26px;
  margin: 24px 0 16px;
  font-weight: 600;
  color: #1a1a1a;
  line-height: 1.4;
}

:deep(.w-e-text-container [data-slate-editor] h2) {
  font-size: 22px;
  margin: 20px 0 14px;
  font-weight: 600;
  color: #1a1a1a;
  line-height: 1.4;
}

:deep(.w-e-text-container [data-slate-editor] h3) {
  font-size: 18px;
  margin: 18px 0 12px;
  font-weight: 600;
  color: #1a1a1a;
  line-height: 1.4;
}

:deep(.w-e-text-container [data-slate-editor] h4) {
  font-size: 16px;
  margin: 16px 0 10px;
  font-weight: 600;
  color: #1a1a1a;
  line-height: 1.4;
}

:deep(.w-e-text-container [data-slate-editor] h5) {
  font-size: 14px;
  margin: 14px 0 8px;
  font-weight: 600;
  color: #1a1a1a;
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
  border-left: 4px solid #d0d7de;
  padding: 12px 16px;
  margin: 16px 0;
  background: #f6f8fa;
  color: #57606a;
}

:deep(.w-e-text-container [data-slate-editor] table) {
  border-collapse: collapse;
  width: 100%;
  margin: 16px 0;
}

:deep(.w-e-text-container [data-slate-editor] th),
:deep(.w-e-text-container [data-slate-editor] td) {
  border: 1px solid #d0d7de;
  padding: 10px 12px;
  text-align: left;
}

:deep(.w-e-text-container [data-slate-editor] th) {
  background: #f6f8fa;
  font-weight: 600;
}

:deep(.w-e-text-container [data-slate-editor] code) {
  background: #f6f8fa;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
  color: #d63384;
}

:deep(.w-e-text-container [data-slate-editor] pre) {
  background: #f6f8fa;
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
  color: #0969da;
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
  border-top: 1px solid #d0d7de;
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
  background: #fff;
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
