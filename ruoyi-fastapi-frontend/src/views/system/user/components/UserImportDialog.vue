<template>
  <ZxDialog v-bind="dialogProps" v-on="dialogEvents" :showFooter="false">
    <zx-upload
      v-model="fileList"
      :disabled="isUploading"
      :drag="true"
      :auto-upload="false"
      :limit="1"
      :accept="fileRules.accept.join(',')"
      :max-size="fileRules.maxSize"
      main-text="将文件拖到此处"
      sub-text="或点击上传"
      @remove="cancelUpload"
    />
    <div class="upload-tip text-center mt-4">
      <el-checkbox v-model="updateSupport" :disabled="isUploading" class="mr-2" />
      <span class="text-sm text-zx-surface-blocking-on-text-secondary"
        >是否更新已经存在的用户数据</span
      >
    </div>
    <div class="upload-tip text-center mt-2">
      <span class="text-sm text-zx-surface-blocking-on-text-secondary"
        >仅允许导入xls、xlsx格式文件。</span
      >
      <el-link
        type="primary"
        :underline="false"
        class="text-sm ml-1"
        @click="handleDownloadTemplate"
      >
        下载模板
      </el-link>
    </div>
    <template #footer>
      <div class="dialog-footer">
        <el-button type="primary" :loading="isUploading" @click="handleSubmitClick"
          >确 定</el-button
        >
        <el-button @click="handleClose">取 消</el-button>
      </div>
    </template>
  </ZxDialog>
</template>

<script setup>
import { ref, shallowRef, computed, getCurrentInstance, watch, onBeforeUnmount } from 'vue';
import { useDialog } from '@zxio/zxui/hooks';
import { isAbortError } from '@zxio/http';
import { ElMessage } from 'element-plus';
import { captureUserCommand, userCommands } from '@/queries/system/user';
import { queryScope, requireQueryScope } from '@/queries/context';
import { validateFile } from '@/utils/io-toolkit/upload';
import { presentProblemFeedback, resolveFeedbackOptions } from '@/utils/feedback/presenter';

const { proxy } = getCurrentInstance();

const emit = defineEmits(['success']);

const fileList = ref([]);
const activeUpload = shallowRef();
const isUploading = computed(() => !!activeUpload.value);
const updateSupport = ref(false);
let openingScope;
const fileRules = { accept: ['.xlsx', '.xls'], maxSize: 10 * 1024 * 1024 };

const { dialogProps, dialogEvents, state, open, close } = useDialog({
  dialogSize: 'md',
  title: '用户导入',

  showFooter: true,
  defaultData: () => ({}),
});

function cancelUpload() {
  const operation = activeUpload.value;
  // 先失效再取消：旧进度、结果和 finally 均不能影响下次打开。
  activeUpload.value = undefined;
  operation?.controller.abort('user-import-dialog-closed');
}

watch(
  () => state.visible,
  (visible) => {
    if (!visible) cancelUpload();
  },
  { flush: 'sync' }
);
onBeforeUnmount(cancelUpload);
watch(queryScope, handleClose, { flush: 'sync' });

function escapeHtml(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function buildImportResultHtml(response) {
  const summary = response?.summary || {};
  const results = Array.isArray(response?.results) ? response.results : [];
  const total = Number(summary.total ?? results.length ?? 0);
  const succeeded = Number(summary.succeeded ?? results.filter((item) => item.success).length);
  const failed = Number(summary.failed ?? results.filter((item) => !item.success).length);
  const lines = [`<p>共 ${total} 条，成功 ${succeeded} 条，失败 ${failed} 条。</p>`];

  if (results.length > 0) {
    lines.push('<ol style="padding-left: 18px;">');
    results.forEach((item) => {
      const rowLabel = item.rowNumber ? `第 ${escapeHtml(item.rowNumber)} 行` : '未知行';
      const userName = item.userName ? `，账号 ${escapeHtml(item.userName)}` : '';
      if (item.success) {
        const action = item.action === 'updated' ? '更新成功' : '创建成功';
        lines.push(`<li>${rowLabel}${userName}：${action}</li>`);
        return;
      }
      const detail = item.error?.detail || item.error?.title || '导入失败';
      lines.push(`<li>${rowLabel}${userName}：${escapeHtml(detail)}</li>`);
    });
    lines.push('</ol>');
  }

  return lines.join('');
}

/** 文件上传成功处理 */
function handleUploadSuccess(response) {
  fileList.value = [];
  close();

  void Promise.resolve(
    proxy.$alert(
      "<div style='overflow: auto;overflow-x: hidden;max-height: 70vh;padding: 10px 20px 0;'>" +
        buildImportResultHtml(response) +
        '</div>',
      '导入结果',
      { dangerouslyUseHTMLString: true }
    )
  ).catch((error) => {
    if (error !== 'cancel' && error !== 'close') {
      ElMessage.error(error instanceof Error ? error.message : '导入结果展示失败');
    }
  });

  emit('success');
}

/** 下载模板 */
function handleDownloadTemplate() {
  proxy.download('system/user/importTemplate', {}, `user_template_${new Date().getTime()}.xlsx`);
}

/** 提交上传 */
function handleSubmit() {
  if (activeUpload.value) return activeUpload.value.task;
  if (!state.visible || openingScope !== queryScope.value) return Promise.resolve();
  const file = fileList.value[0];
  if (!file?.raw) {
    ElMessage.error('请先选择 Excel 文件');
    return Promise.resolve();
  }
  const validation = validateFile(file.raw, fileRules);
  if (!validation.valid) {
    ElMessage.error(validation.error);
    return Promise.resolve();
  }

  const operation = { controller: new AbortController(), task: undefined };
  const updateExisting = updateSupport.value;
  const command = captureUserCommand(
    { file: file.raw, updateSupport: updateExisting },
    openingScope
  );
  operation.task = Promise.resolve().then(async () => {
    // 允许同一事件周期内关闭弹窗，不再派发已经失效的导入。
    if (activeUpload.value !== operation) return;
    file.status = 'uploading';
    file.percentage = 0;
    try {
      const response = await userCommands.importExcel(command, {
        signal: operation.controller.signal,
        onUploadProgress(event) {
          if (activeUpload.value === operation && event.progress !== undefined) {
            file.percentage = Math.round(event.progress * 100);
          }
        },
      });
      if (activeUpload.value === operation) {
        activeUpload.value = undefined;
        handleUploadSuccess(response);
      }
      return response;
    } catch (error) {
      if (activeUpload.value === operation && !isAbortError(error)) {
        if (error.problem) {
          presentProblemFeedback({
            problem: error.problem,
            meta: error.meta || { status: error.status || 0 },
            feedback: resolveFeedbackOptions({ mode: 'auto' }),
          });
        } else {
          ElMessage.error(error instanceof Error ? error.message : '用户导入失败，请稍后重试');
        }
      }
      throw error;
    } finally {
      if (activeUpload.value === operation) {
        activeUpload.value = undefined;
        file.status = 'ready';
        file.percentage = 0;
      }
    }
  });
  activeUpload.value = operation;
  return operation.task;
}

function handleSubmitClick() {
  // 请求错误已由当前操作反馈，点击事件只承接拒绝，避免 Vue 重复上报。
  return handleSubmit().catch(() => {});
}

/** 关闭对话框 */
function handleClose() {
  cancelUpload();
  fileList.value = [];
  updateSupport.value = false;
  close();
}

/** 打开对话框 */
function openDialog() {
  cancelUpload();
  openingScope = requireQueryScope();
  fileList.value = [];
  updateSupport.value = false;
  open();
}

defineExpose({ open: openDialog, close: handleClose });
</script>
