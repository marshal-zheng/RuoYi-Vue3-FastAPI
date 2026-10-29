<template>
  <div v-if="imagesEnabled">
    <el-upload
      :http-request="uploadRequest"
      :before-upload="handleBeforeUpload"
      :on-success="handleUploadSuccess"
      :accept="accept"
      :show-file-list="false"
      class="editor-img-uploader"
    >
      <i ref="uploadRef" class="editor-img-uploader"></i>
    </el-upload>
  </div>
  <div class="editor">
    <quill-editor
      ref="quillEditorRef"
      v-model:content="content"
      contentType="html"
      @textChange="(e) => $emit('update:modelValue', content)"
      :options="options"
      :style="styles"
    />
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, toRaw, watch } from 'vue';
import { ElMessage } from 'element-plus';
import { QuillEditor } from '@vueup/vue-quill';
import '@vueup/vue-quill/dist/vue-quill.snow.css';
import { assetIdOfContentUrl } from '@/api/fileAssets';
import { useAuthenticatedUpload } from '@/composables/useAuthenticatedUpload';
import { installAssetImageRecovery } from '@/utils/file-assets/image-recovery';
import {
  IMAGE_TYPE_IDS,
  MAX_IMAGE_BYTES,
  acceptFor,
  describeTypes,
  isAllowedFileName,
} from '@/utils/file-assets/types';

const quillEditorRef = ref();
const uploadRef = ref();

const props = defineProps({
  /* 编辑器的内容（UTF-8 HTML；图片只能是 /file-assets/{assetId}/content） */
  modelValue: {
    type: String,
  },
  /* 图片上传用途（服务端登记），例如 notice.image；不传时该富文本不支持图片（如生成器富文本字段） */
  purpose: {
    type: String,
    default: '',
  },
  /* 编辑已有业务对象时的业务ID；新建时不传 */
  ownerId: {
    type: [String, Number],
    default: undefined,
  },
  /* 高度 */
  height: {
    type: Number,
    default: null,
  },
  /* 最小高度 */
  minHeight: {
    type: Number,
    default: null,
  },
  /* 只读 */
  readOnly: {
    type: Boolean,
    default: false,
  },
  /* 上传文件大小限制(MB) */
  fileSize: {
    type: Number,
    default: MAX_IMAGE_BYTES / 1024 / 1024,
  },
});

const { upload, pending } = useAuthenticatedUpload({
  purpose: () => props.purpose,
  ownerId: () => props.ownerId,
});
const accept = acceptFor(IMAGE_TYPE_IDS);
// Images exist only as assets of a registered purpose; without one the editor stays text-only.
const imagesEnabled = Boolean(props.purpose);
let uploadSeed = 0;

const options = ref({
  theme: 'snow',
  bounds: document.body,
  debug: 'warn',
  modules: {
    // 工具栏配置（不提供服务端不支持的视频嵌入）
    toolbar: [
      ['bold', 'italic', 'underline', 'strike'], // 加粗 斜体 下划线 删除线
      ['blockquote', 'code-block'], // 引用  代码块
      [{ list: 'ordered' }, { list: 'bullet' }], // 有序、无序列表
      [{ indent: '-1' }, { indent: '+1' }], // 缩进
      [{ size: ['small', false, 'large', 'huge'] }], // 字体大小
      [{ header: [1, 2, 3, 4, 5, 6, false] }], // 标题
      [{ color: [] }, { background: [] }], // 字体颜色、字体背景颜色
      [{ align: [] }], // 对齐方式
      ['clean'], // 清除文本格式
      imagesEnabled ? ['link', 'image'] : ['link'], // 链接、图片（需登记的上传用途）
    ],
  },
  placeholder: '请输入内容',
  readOnly: props.readOnly,
});

const styles = computed(() => {
  let style = {};
  if (props.minHeight) {
    style.minHeight = `${props.minHeight}px`;
  }
  if (props.height) {
    style.height = `${props.height}px`;
  }
  return style;
});

const content = ref('');
watch(
  () => props.modelValue,
  (v) => {
    if (v !== content.value) {
      content.value = v == undefined ? '<p></p>' : v;
    }
  },
  { immediate: true }
);

const quill = () => toRaw(quillEditorRef.value)?.getQuill();

function validImage(file) {
  if (
    !isAllowedFileName(file.name || 'pasted.png', IMAGE_TYPE_IDS) &&
    !file.type?.startsWith('image/')
  ) {
    ElMessage.error(`图片格式错误，仅支持 ${describeTypes(IMAGE_TYPE_IDS)}`);
    return false;
  }
  if (props.fileSize && file.size / 1024 / 1024 > props.fileSize) {
    ElMessage.error(`上传文件大小不能超过 ${props.fileSize} MB!`);
    return false;
  }
  return true;
}

const IMAGE_EXTENSIONS = { 'image/jpeg': 'jpg', 'image/png': 'png', 'image/webp': 'webp' };

function named(file) {
  if (file.name && isAllowedFileName(file.name, IMAGE_TYPE_IDS)) return file;
  return new File([file], `pasted-image.${IMAGE_EXTENSIONS[file.type] || 'png'}`, {
    type: file.type || 'image/png',
  });
}

/**
 * Upload first, then insert the stable content URL at the remembered position.
 * Returns the position after the inserted image so several images keep their order.
 */
async function insertUploaded(file, index) {
  if (!file || !validImage(file)) return index;
  try {
    const descriptor = await upload(named(file), ++uploadSeed);
    const editor = quill();
    if (!editor) return index;
    const at = Math.min(index ?? editor.getLength() - 1, editor.getLength() - 1);
    editor.insertEmbed(at, 'image', descriptor.contentUrl, 'user');
    editor.setSelection(at + 1, 0, 'silent');
    return at + 1;
  } catch {
    // The request layer already reported the failure; nothing unsaved is inserted.
    return index;
  }
}

async function insertSequentially(files, index) {
  let at = index;
  for (const file of files) at = await insertUploaded(file, at);
}

/** Decodes base64 and URL-encoded data URLs; returns null (with a message) when unreadable. */
function dataUrlToFile(dataUrl) {
  try {
    const comma = dataUrl.indexOf(',');
    const header = dataUrl.slice(0, comma);
    const body = dataUrl.slice(comma + 1);
    const type = /^data:([^;,]+)/.exec(header)?.[1] || 'image/png';
    const bytes = /;base64$/i.test(header)
      ? Uint8Array.from(atob(body), (char) => char.charCodeAt(0))
      : new TextEncoder().encode(decodeURIComponent(body));
    return new File([bytes], `pasted-image.${IMAGE_EXTENSIONS[type] || 'png'}`, { type });
  } catch {
    ElMessage.error('无法读取粘贴的图片，请保存为文件后再上传');
    return null;
  }
}

/** Copying an image inside the editor yields an absolute same-origin URL; keep the stable path. */
function sameOriginContentPath(src) {
  try {
    const url = new URL(src, window.location.href);
    if (url.origin !== window.location.origin || url.search || url.hash) return null;
    return assetIdOfContentUrl(url.pathname) ? url.pathname : null;
  } catch {
    return null;
  }
}

let removeRecovery;
const onFiles = (event, list) => {
  const images = Array.from(list || []).filter((file) => file.type?.startsWith('image/'));
  if (!images.length) return;
  // Office/Excel put both the rich HTML and a rendered picture on the clipboard: keep the content.
  if (event.type === 'paste' && event.clipboardData?.types?.includes('text/html')) return;
  event.preventDefault();
  // Quill's own clipboard handler lives on the same root element; it must not see these files.
  event.stopImmediatePropagation();
  if (!imagesEnabled) {
    ElMessage.warning('此处不支持插入图片');
    return;
  }
  void insertSequentially(images, quill()?.getSelection()?.index);
};
const onPaste = (event) => onFiles(event, event.clipboardData?.files);
const onDrop = (event) => onFiles(event, event.dataTransfer?.files);

onMounted(() => {
  const editor = quill();
  if (!editor) return;
  if (imagesEnabled)
    editor.getModule('toolbar').addHandler('image', () => uploadRef.value?.click());
  // Pasted HTML may carry data: images: upload them instead of storing inline bytes.
  editor.clipboard.addMatcher('IMG', (node, delta) => {
    const src = node.getAttribute('src') || '';
    if (!imagesEnabled) {
      ElMessage.warning('此处不支持插入图片');
      return new delta.constructor();
    }
    if (!src.startsWith('data:image/')) {
      const path = sameOriginContentPath(src);
      if (!path || path === src) return delta;
      return new delta.constructor(
        delta.ops.map((op) => (op.insert?.image ? { ...op, insert: { image: path } } : op))
      );
    }
    void insertUploaded(dataUrlToFile(src), editor.getSelection()?.index);
    return delta.compose ? new delta.constructor() : delta;
  });
  editor.root.addEventListener('paste', onPaste, true);
  editor.root.addEventListener('drop', onDrop, true);
  removeRecovery = installAssetImageRecovery(editor.root);
});

onBeforeUnmount(() => {
  const editor = quill();
  editor?.root.removeEventListener('paste', onPaste, true);
  editor?.root.removeEventListener('drop', onDrop, true);
  removeRecovery?.();
});

// 上传前校检格式和大小
function handleBeforeUpload(file) {
  return validImage(file);
}

function uploadRequest(options) {
  return upload(options.file, options.file.uid, options.onProgress);
}

// 上传成功处理：插入稳定内容地址（不带环境前缀）
function handleUploadSuccess(descriptor) {
  const editor = quill();
  const length = editor.getSelection()?.index ?? editor.getLength() - 1;
  editor.insertEmbed(length, 'image', descriptor.contentUrl, 'user');
  editor.setSelection(length + 1);
}

/**
 * Blocks a save while uploads are running or when the content still holds images the server
 * cannot accept (external URLs, inline data). Returns the user-facing reason, or '' when valid.
 */
function validate() {
  if (pending.value > 0) return '图片仍在上传，请稍候再保存';
  const root = quill()?.root;
  const images = Array.from(root?.querySelectorAll('img') || []);
  if (!imagesEnabled && images.length) return '此处不支持图片，请删除后再保存';
  const invalid = images.filter((image) => !assetIdOfContentUrl(image.getAttribute('src')));
  if (invalid.length)
    return `内容中有 ${invalid.length} 张外部或未上传的图片，请删除后通过上传插入`;
  return '';
}

defineExpose({ pending, validate });
</script>

<style>
/* Theme only editor chrome and default content presentation, never saved inline colors. */
.editor .ql-toolbar.ql-snow,
.editor .ql-container.ql-snow {
  border-color: var(--zx-semantic-border-default);
  color: var(--zx-semantic-text-primary);
  background: var(--zx-semantic-surface-field-fill);
}
.editor .ql-toolbar.ql-snow {
  background: var(--zx-semantic-surface-panel-fill);
  padding-block: var(--zx-semantic-spacing-control-y);
}
/* Density changes editing chrome, not the document's typography or spacing. */
.editor .ql-toolbar.ql-snow button,
.editor .ql-toolbar.ql-snow .ql-picker {
  height: calc(var(--zx-semantic-spacing-control-y) * 2 + 12px);
}
.editor .ql-toolbar.ql-snow button {
  padding-block: max(2px, calc(var(--zx-semantic-spacing-control-y) - 3px));
}
.editor .ql-toolbar.ql-snow .ql-picker-label {
  display: flex;
  align-items: center;
}
.editor .ql-snow .ql-picker-options {
  padding-block: var(--zx-semantic-spacing-control-y);
}
.editor .ql-snow .ql-picker:not(.ql-color-picker) .ql-picker-item {
  padding-block: max(2px, calc(var(--zx-semantic-spacing-control-y) - 3px));
}
.editor .ql-snow .ql-tooltip {
  padding-block: max(2px, calc(var(--zx-semantic-spacing-control-y) - 3px));
}
.editor .ql-snow .ql-tooltip input[type='text'] {
  height: calc(var(--zx-semantic-spacing-control-y) * 2 + 12px);
}
.editor .ql-snow .ql-picker {
  color: var(--zx-semantic-text-primary);
}
.editor .ql-snow .ql-stroke:not(.ql-color-label) {
  stroke: var(--zx-semantic-text-primary);
}
.editor .ql-snow .ql-fill:not(.ql-color-label) {
  fill: var(--zx-semantic-text-primary);
}
.editor .ql-snow .ql-picker-options,
.editor .ql-snow .ql-tooltip {
  color: var(--zx-semantic-surface-overlay-on-text);
  background: var(--zx-semantic-surface-overlay-fill);
  border-color: var(--zx-semantic-border-default);
  box-shadow: var(--zx-semantic-surface-overlay-depth);
}
.editor .ql-snow .ql-tooltip input[type='text'] {
  color: var(--zx-semantic-text-primary);
  background: var(--zx-semantic-surface-field-fill);
  border-color: var(--zx-semantic-border-control);
}
.editor
  .ql-snow
  :is(
    button:hover,
    button:focus,
    button.ql-active,
    .ql-picker-label:hover,
    .ql-picker-label.ql-active,
    .ql-picker-item:hover,
    .ql-picker-item.ql-selected
  ),
.editor .ql-snow .ql-tooltip a {
  color: var(--zx-semantic-accent-on-surface);
}
.editor
  .ql-snow
  :is(
    button:hover,
    button:focus,
    button.ql-active,
    .ql-picker-label:hover,
    .ql-picker-label.ql-active
  )
  .ql-stroke:not(.ql-color-label) {
  stroke: var(--zx-semantic-accent-on-surface);
}
.editor
  .ql-snow
  :is(
    button:hover,
    button:focus,
    button.ql-active,
    .ql-picker-label:hover,
    .ql-picker-label.ql-active
  )
  .ql-fill:not(.ql-color-label) {
  fill: var(--zx-semantic-accent-on-surface);
}
/* Preserve color swatches while adapting toolbar interaction surfaces. */
.editor .ql-snow :is(button:hover, button:focus, button.ql-active, .ql-picker-label:hover),
.editor .ql-snow .ql-picker:not(.ql-color-picker) .ql-picker-item:hover {
  background-color: var(--zx-semantic-fill-hover);
}
.editor .ql-snow button.ql-active,
.editor .ql-snow .ql-picker-label.ql-active,
.editor .ql-snow .ql-picker:not(.ql-color-picker) .ql-picker-item.ql-selected {
  background-color: var(--zx-semantic-fill-selected);
}
.editor .ql-editor.ql-blank::before {
  color: var(--zx-semantic-text-secondary);
}
.editor .ql-snow .ql-picker.ql-expanded .ql-picker-label,
.editor .ql-snow .ql-picker.ql-expanded .ql-picker-options {
  border-color: var(--zx-semantic-border-default);
}

.editor-img-uploader {
  display: none;
}
.editor,
.ql-toolbar {
  white-space: pre-wrap !important;
  line-height: normal !important;
}
.quill-img {
  display: none;
}
.ql-snow .ql-tooltip[data-mode='link']::before {
  content: '请输入链接地址:';
}
.ql-snow .ql-tooltip.ql-editing a.ql-action::after {
  border-right: 0px;
  content: '保存';
  padding-right: 0px;
}
.ql-snow .ql-picker.ql-size .ql-picker-label::before,
.ql-snow .ql-picker.ql-size .ql-picker-item::before {
  content: '14px';
}
.ql-snow .ql-picker.ql-size .ql-picker-label[data-value='small']::before,
.ql-snow .ql-picker.ql-size .ql-picker-item[data-value='small']::before {
  content: '10px';
}
.ql-snow .ql-picker.ql-size .ql-picker-label[data-value='large']::before,
.ql-snow .ql-picker.ql-size .ql-picker-item[data-value='large']::before {
  content: '18px';
}
.ql-snow .ql-picker.ql-size .ql-picker-label[data-value='huge']::before,
.ql-snow .ql-picker.ql-size .ql-picker-item[data-value='huge']::before {
  content: '32px';
}
.ql-snow .ql-picker.ql-header .ql-picker-label::before,
.ql-snow .ql-picker.ql-header .ql-picker-item::before {
  content: '文本';
}
.ql-snow .ql-picker.ql-header .ql-picker-label[data-value='1']::before,
.ql-snow .ql-picker.ql-header .ql-picker-item[data-value='1']::before {
  content: '标题1';
}
.ql-snow .ql-picker.ql-header .ql-picker-label[data-value='2']::before,
.ql-snow .ql-picker.ql-header .ql-picker-item[data-value='2']::before {
  content: '标题2';
}
.ql-snow .ql-picker.ql-header .ql-picker-label[data-value='3']::before,
.ql-snow .ql-picker.ql-header .ql-picker-item[data-value='3']::before {
  content: '标题3';
}
.ql-snow .ql-picker.ql-header .ql-picker-label[data-value='4']::before,
.ql-snow .ql-picker.ql-header .ql-picker-item[data-value='4']::before {
  content: '标题4';
}
.ql-snow .ql-picker.ql-header .ql-picker-label[data-value='5']::before,
.ql-snow .ql-picker.ql-header .ql-picker-item[data-value='5']::before {
  content: '标题5';
}
.ql-snow .ql-picker.ql-header .ql-picker-label[data-value='6']::before,
.ql-snow .ql-picker.ql-header .ql-picker-item[data-value='6']::before {
  content: '标题6';
}
.ql-snow .ql-picker.ql-font .ql-picker-label::before,
.ql-snow .ql-picker.ql-font .ql-picker-item::before {
  content: '标准字体';
}
.ql-snow .ql-picker.ql-font .ql-picker-label[data-value='serif']::before,
.ql-snow .ql-picker.ql-font .ql-picker-item[data-value='serif']::before {
  content: '衬线字体';
}
.ql-snow .ql-picker.ql-font .ql-picker-label[data-value='monospace']::before,
.ql-snow .ql-picker.ql-font .ql-picker-item[data-value='monospace']::before {
  content: '等宽字体';
}
</style>
