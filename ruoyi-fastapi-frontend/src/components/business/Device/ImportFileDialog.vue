<template>
  <ZxDialog v-bind="dialogProps" v-on="dialogEvents" @close="onClose">
    <div class="import-file-dialog">
      <div class="tips">
        <el-alert title="导入说明" type="info" :closable="false" show-icon>
          <template #default>
            <div class="tip-content">
              <p>1. 支持导入 Excel(.xlsx, .xls) 或 CSV(.csv) 格式文件</p>
              <p>2. 请按照模板格式整理数据，确保字段名称、数据类型等信息完整</p>
              <p>3. 导入的数据将追加到现有字段列表中</p>
            </div>
          </template>
        </el-alert>
      </div>

      <el-upload
        ref="uploadRef"
        class="upload-container"
        drag
        :auto-upload="false"
        :limit="1"
        :accept="acceptTypes"
        :on-change="handleFileChange"
        :on-exceed="handleExceed"
        :file-list="fileList"
      >
        <el-icon class="el-icon--upload">
          <upload-filled />
        </el-icon>
        <div class="el-upload__text">将文件拖到此处，或<em>点击上传</em></div>
        <template #tip>
          <div class="el-upload__tip">只能上传 xlsx/xls/csv 文件，且不超过 10MB</div>
        </template>
      </el-upload>

      <div v-if="fileInfo" class="file-info">
        <el-icon><Document /></el-icon>
        <span class="file-name">{{ fileInfo.name }}</span>
        <span class="file-size">{{ formatFileSize(fileInfo.size) }}</span>
      </div>
    </div>

    <template #footerLeft>
      <el-button
        type="primary"
        link
        icon="Download"
        :loading="downloading"
        @click="downloadTemplate"
      >
        下载导入模板
      </el-button>
    </template>
  </ZxDialog>
</template>

<script setup name="ImportFileDialog">
import { ref } from 'vue';
import { ElMessage } from 'element-plus';
import { UploadFilled, Document } from '@element-plus/icons-vue';
import { saveAs } from 'file-saver';
import { useDialog } from '@zxio/zxui';
import { downloadProtocolImportTemplate, previewProtocolImport } from '@/api/protocol/protocol';

const emit = defineEmits(['confirm', 'close']);

const uploadRef = ref();
const fileList = ref([]);
const fileInfo = ref(null);
const acceptTypes = '.xlsx,.xls,.csv';
const downloading = ref(false);

// 文件变化处理
function handleFileChange(file) {
  const isValidType = /\.(xlsx|xls|csv)$/.test(file.name.toLowerCase());
  const isLt10M = file.size / 1024 / 1024 < 10;

  if (!isValidType) {
    ElMessage.error('只能上传 xlsx/xls/csv 格式的文件！');
    fileList.value = [];
    fileInfo.value = null;
    return false;
  }

  if (!isLt10M) {
    ElMessage.error('文件大小不能超过 10MB！');
    fileList.value = [];
    fileInfo.value = null;
    return false;
  }

  fileInfo.value = file.raw || file;
  fileList.value = [file];
  return true;
}

// 文件超出限制
function handleExceed() {
  ElMessage.warning('只能上传一个文件，请删除后重新上传');
}

// 格式化文件大小
function formatFileSize(bytes) {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}

// 下载模板
async function downloadTemplate() {
  if (downloading.value) return;
  try {
    downloading.value = true;
    const blob = await downloadProtocolImportTemplate();
    const fileName = '协议导入模板.xlsx';
    saveAs(blob, fileName);
    ElMessage.success('模板下载成功');
  } catch (error) {
    ElMessage.error(error?.message || '模板下载失败');
  } finally {
    downloading.value = false;
  }
}

const { dialogProps, dialogEvents, open, close } = useDialog({
  title: () => '导入报文字段',
  width: '60%',
  okText: '确定导入',
  preValidate: false,
  autoScrollToError: false,
  onConfirm: async () => {
    if (!fileInfo.value) {
      ElMessage.warning('请先选择要导入的文件');
      throw new Error('no_file');
    }
    const formData = new FormData();
    formData.append('file', fileInfo.value);
    const response = await previewProtocolImport(formData);
    const payload = response?.data || {};
    const fieldCount = payload?.fields?.length || 0;
    if (!fieldCount) {
      ElMessage.warning('文件中没有有效的数据');
      throw new Error('empty_data');
    }
    emit('confirm', payload);
    ElMessage.success(`成功导入 ${fieldCount} 个字段`);
    close();
    return payload;
  },
  onConfirmError: (error) => {
    ElMessage.error('导入失败: ' + (error?.message || '文件解析错误'));
  },
});

function onClose() {
  fileList.value = [];
  fileInfo.value = null;
  emit('close');
}

defineExpose({ open, close });
</script>

<style lang="less" scoped>
.import-file-dialog {
  padding: 10px 0;
}

.tips {
  margin-bottom: 20px;

  .tip-content {
    p {
      margin: 5px 0;
      line-height: 1.6;
      color: #606266;
    }
  }
}

.upload-container {
  :deep(.el-upload) {
    width: 100%;
  }

  :deep(.el-upload-dragger) {
    width: 100%;
    padding: 40px 20px;
  }
}

.file-info {
  margin-top: 20px;
  padding: 12px 15px;
  background-color: #f5f7fa;
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 10px;

  .el-icon {
    font-size: 20px;
    color: #409eff;
  }

  .file-name {
    flex: 1;
    font-size: 14px;
    color: #303133;
    font-weight: 500;
  }

  .file-size {
    font-size: 12px;
    color: #909399;
  }
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>
