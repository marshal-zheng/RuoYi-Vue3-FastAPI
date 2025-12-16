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
import { height } from 'happy-dom/lib/PropertySymbol.js';

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
  title: '用户导入',
  width: '45%',
  height: '60%',
  showFooter: true,
  defaultData: () => ({}),
});

/** 文件上传中处理 */
function handleUploadProgress() {
  isUploading.value = true;
}

/** 文件上传成功处理 */
function handleUploadSuccess(response) {
  isUploading.value = false;
  fileList.value = [];
  close();

  proxy.$alert(
    "<div style='overflow: auto;overflow-x: hidden;max-height: 70vh;padding: 10px 20px 0;'>" +
      response.msg +
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
