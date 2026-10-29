<template>
  <div class="upload-file">
    <el-upload
      multiple
      :http-request="httpRequest"
      :before-upload="handleBeforeUpload"
      v-model:file-list="fileList"
      :limit="limit"
      :accept="accept"
      :on-exceed="handleExceed"
      :on-success="handleUploadSuccess"
      :show-file-list="false"
      :on-remove="handleRemove"
      class="upload-file-uploader"
      ref="fileUpload"
      v-if="!disabled"
    >
      <!-- 上传按钮 -->
      <el-button type="primary">选取文件</el-button>
    </el-upload>
    <!-- 上传提示 -->
    <div class="el-upload__tip" v-if="showTip && !disabled">
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
    <!-- 文件列表 -->
    <transition-group
      class="upload-file-list el-upload-list el-upload-list--text"
      name="el-fade-in-linear"
      tag="ul"
    >
      <li
        :key="file.uid"
        class="el-upload-list__item ele-upload-list__item-content"
        v-for="file in fileList"
      >
        <el-link
          :href="file.assetId ? assetDownloadUrl(file.assetId) : undefined"
          :underline="false"
          :disabled="!file.assetId || file.unavailable"
          target="_blank"
        >
          <span class="el-icon-document">
            {{ file.unavailable ? '文件不可用' : file.name || '加载中…' }}
          </span>
        </el-link>
        <div class="ele-upload-list__item-content-action">
          <el-link
            :underline="false"
            @click="fileUpload.handleRemove(file)"
            type="danger"
            v-if="!disabled"
            >删除</el-link
          >
        </div>
      </li>
    </transition-group>
  </div>
</template>

<script setup>
import { ref, watch, computed, getCurrentInstance, onBeforeUnmount } from 'vue';
import { ElMessage } from 'element-plus';
import { assetDownloadUrl } from '@/api/fileAssets';
import { useAuthenticatedUpload } from '@/composables/useAuthenticatedUpload';
import { useUploadModel } from '@/composables/useUploadModel';
import { acceptFor, describeTypes, isAllowedFileName } from '@/utils/file-assets/types';

const props = defineProps({
  /** 资产ID数组（唯一持久契约） */
  modelValue: { type: Array, default: () => [] },
  /** 服务端登记的上传用途 */
  purpose: { type: String, required: true },
  /** 编辑已有业务对象时的业务ID；新建时不传 */
  ownerId: { type: [String, Number], default: undefined },
  /** 字段声明的类型ID子集（与服务端校验同源） */
  typeIds: { type: Array, required: true },
  // 数量限制
  limit: { type: Number, default: 5 },
  // 大小限制(MB)
  fileSize: { type: Number, default: 20 },
  // 是否显示提示
  isShowTip: { type: Boolean, default: true },
  // 禁用组件（仅查看文件）
  disabled: { type: Boolean, default: false },
});

const emit = defineEmits(['update:modelValue']);
const { proxy } = getCurrentInstance();
const fileUpload = ref();
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
watch(
  () => pending.value > 0,
  (busy) => {
    if (busy) proxy.$modal.loading('正在上传文件，请稍候...');
    else proxy.$modal.closeLoading();
  }
);
onBeforeUnmount(() => {
  if (pending.value) proxy.$modal.closeLoading();
});

// 上传前预检格式和大小（服务端按实际内容再次校验）
function handleBeforeUpload(file) {
  if (!isAllowedFileName(file.name, props.typeIds)) {
    ElMessage.error(`文件格式不正确，请上传${typeHint.value}格式文件!`);
    return false;
  }
  if (props.fileSize && file.size / 1024 / 1024 > props.fileSize) {
    ElMessage.error(`上传文件大小不能超过 ${props.fileSize} MB!`);
    return false;
  }
  return true;
}

function handleExceed() {
  ElMessage.error(`上传文件数量不能超过 ${props.limit} 个!`);
}

defineExpose({ pending });
</script>

<style scoped>
.upload-file-uploader {
  margin-bottom: 5px;
}
.upload-file-list .el-upload-list__item {
  border: 1px solid var(--zx-semantic-border-subtle);
  line-height: 2;
  margin-bottom: 10px;
  position: relative;
}
.upload-file-list .ele-upload-list__item-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: inherit;
}
.ele-upload-list__item-content-action .el-link {
  margin-right: 10px;
}
</style>
