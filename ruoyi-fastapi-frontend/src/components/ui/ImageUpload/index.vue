<template>
  <div class="component-upload-image">
    <el-upload
      multiple
      :http-request="httpRequest"
      list-type="picture-card"
      :on-success="handleUploadSuccess"
      :before-upload="handleBeforeUpload"
      :limit="limit"
      :accept="accept"
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
      <template v-if="typeHint">
        格式为
        <b style="color: var(--zx-semantic-status-danger-on-surface)">{{ typeHint }}</b>
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
      <img
        :src="dialogImageUrl"
        style="display: block; max-width: 100%; margin: 0 auto"
        @error="onImageError"
      />
    </ZxDialog>
  </div>
</template>

<script setup>
import { ref, watch, computed, getCurrentInstance, onBeforeUnmount, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import { useAuthenticatedUpload } from '@/composables/useAuthenticatedUpload';
import { useUploadModel } from '@/composables/useUploadModel';
import { installAssetImageRecovery, retryAssetImage } from '@/utils/file-assets/image-recovery';
import {
  IMAGE_TYPE_IDS,
  MAX_IMAGE_BYTES,
  acceptFor,
  describeTypes,
  isAllowedFileName,
} from '@/utils/file-assets/types';

const props = defineProps({
  /** 资产ID数组（唯一持久契约） */
  modelValue: { type: Array, default: () => [] },
  /** 服务端登记的上传用途 */
  purpose: { type: String, required: true },
  /** 编辑已有业务对象时的业务ID；新建时不传 */
  ownerId: { type: [String, Number], default: undefined },
  /** 字段声明的图片类型ID子集（jpeg/png/webp） */
  typeIds: { type: Array, default: () => IMAGE_TYPE_IDS },
  // 图片数量限制
  limit: { type: Number, default: 5 },
  // 大小限制(MB)
  fileSize: { type: Number, default: MAX_IMAGE_BYTES / 1024 / 1024 },
  // 是否显示提示
  isShowTip: { type: Boolean, default: true },
});

const { proxy } = getCurrentInstance();
const emit = defineEmits(['update:modelValue']);
const dialogImageUrl = ref('');
const dialogVisible = ref(false);
const imageUpload = ref();
const { httpRequest, abort, pending } = useAuthenticatedUpload({
  purpose: () => props.purpose,
  ownerId: () => props.ownerId,
});
const {
  files: fileList,
  success: handleUploadSuccess,
  remove: handleRemove,
} = useUploadModel({
  value: () => props.modelValue,
  emit: (ids) => emit('update:modelValue', ids),
  abort,
});
const accept = computed(() => acceptFor(props.typeIds));
const typeHint = computed(() => describeTypes(props.typeIds));
const showTip = computed(() => props.isShowTip && (typeHint.value || props.fileSize));
let removeRecovery;
onMounted(() => {
  // Thumbnails of the picture-card list recover from an expired session at most once.
  if (imageUpload.value?.$el) removeRecovery = installAssetImageRecovery(imageUpload.value.$el);
});
watch(
  () => pending.value > 0,
  (busy) => {
    if (busy) proxy.$modal.loading('正在上传图片，请稍候...');
    else proxy.$modal.closeLoading();
  }
);
onBeforeUnmount(() => {
  removeRecovery?.();
  if (pending.value) proxy.$modal.closeLoading();
});

// 上传前预检格式和大小（服务端按实际解码格式再次校验并规范化）
function handleBeforeUpload(file) {
  if (!isAllowedFileName(file.name, props.typeIds)) {
    ElMessage.error(`文件格式不正确，请上传${typeHint.value}图片格式文件!`);
    return false;
  }
  if (props.fileSize && file.size / 1024 / 1024 > props.fileSize) {
    ElMessage.error(`上传图片大小不能超过 ${props.fileSize} MB!`);
    return false;
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
function onImageError(event) {
  void retryAssetImage(event.target);
}

defineExpose({ pending });
</script>

<style scoped>
/* .el-upload--picture-card 控制加号部分 */
:deep(.hide .el-upload--picture-card) {
  display: none;
}
</style>
