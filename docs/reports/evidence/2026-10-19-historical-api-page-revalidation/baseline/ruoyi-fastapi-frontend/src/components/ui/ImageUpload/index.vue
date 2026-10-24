<template>
  <div class="component-upload-image">
    <el-upload
      multiple
      action="/common/upload"
      :http-request="httpRequest"
      list-type="picture-card"
      :on-success="handleUploadSuccess"
      :before-upload="handleBeforeUpload"
      :limit="limit"
      :on-exceed="handleExceed"
      ref="imageUpload"
      :on-remove="handleRemove"
      :show-file-list="true"
      v-model:file-list="fileList"
      :on-preview="handlePictureCardPreview"
      :class="{ hide: fileList.length >= limit }"
    >
      <el-icon class="avatar-uploader-icon"><plus /></el-icon>
    </el-upload>
    <!-- 上传提示 -->
    <div class="el-upload__tip" v-if="showTip">
      请上传
      <template v-if="fileSize">
        大小不超过
        <b style="color: var(--zx-semantic-status-danger-on-surface)">{{ fileSize }}MB</b>
      </template>
      <template v-if="fileType">
        格式为
        <b style="color: var(--zx-semantic-status-danger-on-surface)">{{ fileType.join('/') }}</b>
      </template>
      的文件
    </div>

    <ZxDialog
      dialog-size="lg"
      :draggable="false"
      :show-full-screen="false"
      :destroy-on-close="false"
      :close-on-click-modal="true"
      :footer="false"
      v-model="dialogVisible"
      title="预览"
    >
      <img :src="dialogImageUrl" style="display: block; max-width: 100%; margin: 0 auto" />
    </ZxDialog>
  </div>
</template>

<script setup>
import { ref, watch, computed, getCurrentInstance, onBeforeUnmount } from 'vue';
import { ElMessage } from 'element-plus';
import { isExternal } from '@/utils/validate';
import { useAuthenticatedUpload } from '@/composables/useAuthenticatedUpload';
import { useUploadModel } from '@/composables/useUploadModel';

const props = defineProps({
  modelValue: [String, Object, Array],
  // 图片数量限制
  limit: {
    type: Number,
    default: 5,
  },
  // 大小限制(MB)
  fileSize: {
    type: Number,
    default: 5,
  },
  // 文件类型, 例如['png', 'jpg', 'jpeg']
  fileType: {
    type: Array,
    default: () => ['png', 'jpg', 'jpeg'],
  },
  // 是否显示提示
  isShowTip: {
    type: Boolean,
    default: true,
  },
});

const { proxy } = getCurrentInstance();
const emit = defineEmits(['update:modelValue']);
const dialogImageUrl = ref('');
const dialogVisible = ref(false);
const baseUrl = import.meta.env.VITE_APP_BASE_API;
const { httpRequest, abort, pending } = useAuthenticatedUpload();
const {
  files: fileList,
  success: handleUploadSuccess,
  remove: handleRemove,
} = useUploadModel(
  () => props.modelValue,
  emit,
  abort,
  (url) => (isExternal(url) || url.startsWith(baseUrl + '/') ? url : baseUrl + url),
  (url) => (url.startsWith(baseUrl + '/') ? url.slice(baseUrl.length) : url)
);
const showTip = computed(() => props.isShowTip && (props.fileType || props.fileSize));
watch(
  () => pending.value > 0,
  (busy) => {
    if (busy) proxy.$modal.loading('正在上传图片，请稍候...');
    else proxy.$modal.closeLoading();
  }
);
onBeforeUnmount(() => {
  if (pending.value) proxy.$modal.closeLoading();
});

// 上传前loading加载
function handleBeforeUpload(file) {
  let isImg = false;
  if (props.fileType.length) {
    let fileExtension = '';
    if (file.name.lastIndexOf('.') > -1) {
      fileExtension = file.name.slice(file.name.lastIndexOf('.') + 1);
    }
    isImg = props.fileType.some((type) => {
      if (file.type.indexOf(type) > -1) return true;
      if (fileExtension && fileExtension.indexOf(type) > -1) return true;
      return false;
    });
  } else {
    isImg = file.type.indexOf('image') > -1;
  }
  if (!isImg) {
    ElMessage.error(`文件格式不正确，请上传${props.fileType.join('/')}图片格式文件!`);
    return false;
  }
  if (file.name.includes(',')) {
    ElMessage.error('文件名不正确，不能包含英文逗号!');
    return false;
  }
  if (props.fileSize) {
    const isLt = file.size / 1024 / 1024 < props.fileSize;
    if (!isLt) {
      ElMessage.error(`上传头像图片大小不能超过 ${props.fileSize} MB!`);
      return false;
    }
  }
  return true;
}

function handleExceed() {
  ElMessage.error(`上传文件数量不能超过 ${props.limit} 个!`);
}
function handlePictureCardPreview(file) {
  dialogImageUrl.value = file.url;
  dialogVisible.value = true;
}
</script>

<style scoped>
/* .el-upload--picture-card 控制加号部分 */
:deep(.hide .el-upload--picture-card) {
  display: none;
}
</style>
