<template>
  <div class="upload-file">
    <el-upload
      multiple
      action="/common/upload"
      :http-request="httpRequest"
      :before-upload="handleBeforeUpload"
      v-model:file-list="fileList"
      :limit="limit"
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
      <template v-if="fileType">
        格式为
        <b style="color: var(--zx-semantic-status-danger-on-surface)">{{ fileType.join('/') }}</b>
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
        <el-link :href="`${baseUrl}${file.url}`" :underline="false" target="_blank">
          <span class="el-icon-document"> {{ getFileName(file.name) }} </span>
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
import { useAuthenticatedUpload } from '@/composables/useAuthenticatedUpload';
import { useUploadModel } from '@/composables/useUploadModel';

const props = defineProps({
  modelValue: [String, Object, Array],
  // 数量限制
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
    default: () => ['doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'pdf'],
  },
  // 是否显示提示
  isShowTip: {
    type: Boolean,
    default: true,
  },
  // 禁用组件（仅查看文件）
  disabled: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(['update:modelValue']);
const { proxy } = getCurrentInstance();
const fileUpload = ref();
const baseUrl = import.meta.env.VITE_APP_BASE_API;
const { httpRequest, abort, pending } = useAuthenticatedUpload();
const {
  files: fileList,
  success: handleUploadSuccess,
  remove: handleRemove,
} = useUploadModel(() => props.modelValue, emit, abort);
const showTip = computed(() => props.isShowTip && (props.fileType || props.fileSize));
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

// 上传前校检格式和大小
function handleBeforeUpload(file) {
  // 校检文件类型
  if (props.fileType.length) {
    const fileName = file.name.split('.');
    const fileExt = fileName[fileName.length - 1];
    const isTypeOk = props.fileType.indexOf(fileExt) >= 0;
    if (!isTypeOk) {
      ElMessage.error(`文件格式不正确，请上传${props.fileType.join('/')}格式文件!`);
      return false;
    }
  }
  // 校检文件名是否包含特殊字符
  if (file.name.includes(',')) {
    ElMessage.error('文件名不正确，不能包含英文逗号!');
    return false;
  }
  // 校检文件大小
  if (props.fileSize) {
    const isLt = file.size / 1024 / 1024 < props.fileSize;
    if (!isLt) {
      ElMessage.error(`上传文件大小不能超过 ${props.fileSize} MB!`);
      return false;
    }
  }
  return true;
}

function handleExceed() {
  ElMessage.error(`上传文件数量不能超过 ${props.limit} 个!`);
}
function getFileName(name) {
  return name.slice(name.lastIndexOf('/') + 1);
}
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
