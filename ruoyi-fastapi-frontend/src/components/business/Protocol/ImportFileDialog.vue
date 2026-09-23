<template>
  <ZxDialog v-bind="dialogProps" v-on="dialogEvents" @close="onClose">
    <div class="import-file-dialog">
      <div class="tips">
        <el-alert title="导入说明" type="info" :closable="false" show-icon>
          <template #default>
            <div class="tip-content">
              <p>1. 支持导入 Excel(.xlsx, .xls)、CSV(.csv) 或 JSON(.json) 格式文件</p>
              <p>2. 请按照模板格式整理数据，确保字段名称、数据类型等信息完整</p>
              <p>3. 导入的数据将追加到现有字段列表中</p>
              <p v-if="protocolType">4. 若包含协议配置信息，将自动填充到对应表单</p>
            </div>
          </template>
        </el-alert>
      </div>

      <ZxUpload
        ref="uploadRef"
        v-model="fileList"
        drag
        :auto-upload="false"
        :limit="1"
        :accept="acceptTypes"
        :max-size="10 * 1024 * 1024"
        :custom-file-list="true"
        :show-file-list="true"
        main-text="将文件拖到此处，或点击上传"
        sub-text="支持 xlsx/xls/csv/json 格式"
        tip-text="只能上传 xlsx/xls/csv/json 文件，且不超过 10MB"
        :show-tip="true"
        :show-sub-text="true"
        @change="handleFileChange"
        @exceed="handleExceed"
      />
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
import { ref, computed } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { saveAs } from 'file-saver';
import { useDialog } from '@zxio/zxui';
import { downloadProtocolImportTemplate, previewProtocolImport } from '@/api/protocol/protocol';

const props = defineProps({
  protocolType: {
    type: String,
    default: '',
  },
  protocolId: {
    type: [String, Number],
    default: null,
  },
});

const emit = defineEmits(['confirm', 'close']);

const uploadRef = ref();
const fileList = ref([]);
const acceptTypes = '.xlsx,.xls,.csv,.json';
const downloading = ref(false);

// 计算当前选中的文件信息
const fileInfo = computed(() => {
  if (fileList.value.length > 0) {
    const file = fileList.value[0];
    return file.raw || file;
  }
  return null;
});

// 文件变化处理
function handleFileChange(fileList) {
  if (fileList.length === 0) {
    return;
  }

  const file = fileList[0];
  const fileObj = file.raw || file;

  // 文件类型验证（ZxUpload 已经做了基础验证，这里做二次确认）
  const isValidType = /\.(xlsx|xls|csv|json)$/i.test(fileObj.name);
  if (!isValidType) {
    ElMessage.error('只能上传 xlsx/xls/csv/json 格式的文件！');
    // 清空文件列表
    uploadRef.value?.clearFiles();
    return;
  }
}

// 文件超出限制
function handleExceed() {
  ElMessage.warning('只能上传一个文件，请删除后重新上传');
}

// 下载模板
async function downloadTemplate() {
  if (downloading.value) return;
  try {
    downloading.value = true;
    const params = {};
    if (props.protocolType) {
      params.protocolType = props.protocolType;
    }
    if (props.protocolId) {
      params.protocolId = props.protocolId;
    }
    const blob = await downloadProtocolImportTemplate(params);
    const fileName = `协议导入模板${props.protocolType ? '_' + props.protocolType : ''}.xlsx`;
    saveAs(blob, fileName);
    ElMessage.success('模板下载成功');
  } catch (error) {
    ElMessage.error(error?.message || '模板下载失败');
  } finally {
    downloading.value = false;
  }
}

const { dialogProps, dialogEvents, open, close } = useDialog({
  dialogSize: 'md',
  title: () => '导入协议数据',

  okText: '确定导入',
  preValidate: false,
  autoScrollToError: false,
  onConfirm: async () => {
    if (!fileInfo.value || fileList.value.length === 0) {
      ElMessage.warning('请先选择要导入的文件');
      throw new Error('no_file');
    }

    try {
      const formData = new FormData();
      const file = fileInfo.value;
      formData.append('file', file);

      const backendResult = await previewProtocolImport(formData);
      const payload = backendResult || {};
      const fieldCount = payload?.fields?.length || 0;
      const importedProtocolType = payload?.protocolType;
      const headerValues = payload?.header ? Object.values(payload.header) : [];
      const hasHeaderConfig = headerValues.some(
        (value) => value !== '' && value !== null && value !== undefined
      );

      if (!fieldCount && !hasHeaderConfig) {
        ElMessage.warning('文件中没有有效的数据（字段或配置）');
        throw new Error('empty_data');
      }

      const finalResult = { ...payload };

      if (
        importedProtocolType &&
        props.protocolType &&
        importedProtocolType.toLowerCase() !== props.protocolType.toLowerCase()
      ) {
        const currentTypeUpper = props.protocolType.toUpperCase();
        const importedTypeUpper = importedProtocolType.toUpperCase();

        await ElMessageBox.confirm(
          `检测到导入文件的协议类型为 ${importedTypeUpper}，与当前选择的 ${currentTypeUpper} 不一致。是否切换到 ${importedTypeUpper} 协议类型并导入？`,
          '协议类型不一致',
          {
            confirmButtonText: `切换到 ${importedTypeUpper} 并导入`,
            cancelButtonText: '取消导入',
            type: 'warning',
            distinguishCancelAndClose: true,
          }
        );

        finalResult.switchProtocolType = importedProtocolType;
      }

      emit('confirm', finalResult);

      close();
      return finalResult;
    } catch (error) {
      if (error === 'cancel' || error === 'close') {
        throw new Error('user_cancelled');
      }
      ElMessage.error('导入失败: ' + (error?.message || '文件解析错误'));
      throw error;
    }
  },
});

function onClose() {
  uploadRef.value?.clearFiles();
  fileList.value = [];
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

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>
