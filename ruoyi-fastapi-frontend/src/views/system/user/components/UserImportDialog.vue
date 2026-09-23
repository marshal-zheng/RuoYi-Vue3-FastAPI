<template>
  <ZxDialog v-bind="dialogProps" v-on="dialogEvents" :showFooter="false">
    <zx-upload
      ref="uploadRef"
      v-model="fileList"
      :action="uploadUrl"
      :headers="uploadHeaders"
      :drag="true"
      :auto-upload="false"
      :limit="1"
      accept=".xlsx,.xls"
      main-text="将文件拖到此处"
      sub-text="或点击上传"
      @success="handleUploadSuccess"
      @progress="handleUploadProgress"
    />
    <div class="upload-tip text-center mt-4">
      <el-checkbox v-model="updateSupport" class="mr-2" />
      <span class="text-sm text-gray-500">是否更新已经存在的用户数据</span>
    </div>
    <div class="upload-tip text-center mt-2">
      <span class="text-sm text-gray-400">仅允许导入xls、xlsx格式文件。</span>
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
        <el-button type="primary" :loading="isUploading" @click="handleSubmit">确 定</el-button>
        <el-button @click="handleClose">取 消</el-button>
      </div>
    </template>
  </ZxDialog>
</template>

<script setup>
import { ref, computed, getCurrentInstance } from 'vue';
import { useDialog } from '@zxio/zxui';
import { getToken } from '@/utils/auth';

const { proxy } = getCurrentInstance();

const emit = defineEmits(['success']);

const uploadRef = ref();
const fileList = ref([]);
const isUploading = ref(false);
const updateSupport = ref(false);

const uploadHeaders = computed(() => ({
  Authorization: 'Bearer ' + getToken(),
}));

const uploadUrl = computed(
  () =>
    import.meta.env.VITE_APP_BASE_API +
    '/system/user/importData?updateSupport=' +
    (updateSupport.value ? 1 : 0)
);

const { dialogProps, dialogEvents, open, close } = useDialog({
  dialogSize: 'md',
  title: '用户导入',

  showFooter: true,
  defaultData: () => ({}),
});

/** 文件上传中处理 */
function handleUploadProgress() {
  isUploading.value = true;
}

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
  isUploading.value = false;
  fileList.value = [];
  close();

  proxy.$alert(
    "<div style='overflow: auto;overflow-x: hidden;max-height: 70vh;padding: 10px 20px 0;'>" +
      buildImportResultHtml(response) +
      '</div>',
    '导入结果',
    { dangerouslyUseHTMLString: true }
  );

  emit('success');
}

/** 下载模板 */
function handleDownloadTemplate() {
  proxy.download('system/user/importTemplate', {}, `user_template_${new Date().getTime()}.xlsx`);
}

/** 提交上传 */
function handleSubmit() {
  uploadRef.value?.submit();
}

/** 关闭对话框 */
function handleClose() {
  fileList.value = [];
  isUploading.value = false;
  updateSupport.value = false;
  close();
}

/** 打开对话框 */
function openDialog() {
  fileList.value = [];
  updateSupport.value = false;
  open();
}

defineExpose({ open: openDialog, close: handleClose });
</script>
