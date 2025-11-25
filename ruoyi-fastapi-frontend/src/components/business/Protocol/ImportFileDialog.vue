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
              <p v-if="protocolType">4. 若包含协议配置信息，将自动填充到对应表单</p>
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
import { ElMessage, ElMessageBox } from 'element-plus';
import { UploadFilled, Document } from '@element-plus/icons-vue';
import { saveAs } from 'file-saver';
import { useDialog } from '@zxio/zxui';
import * as XLSX from 'xlsx';
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

// 解析Excel文件获取配置信息
async function parseProtocolConfig(file) {
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const data = new Uint8Array(e.target.result);
        const workbook = XLSX.read(data, { type: 'array' });
        const configSheetName = workbook.SheetNames.find(
          (name) => name.includes('配置') || name.includes('Config') || name.includes('Header')
        );

        if (!configSheetName) {
          resolve({});
          return;
        }

        const worksheet = workbook.Sheets[configSheetName];
        const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1 });

        const config = {};
        const keyMap = {
          发送方: 'sender',
          Sender: 'sender',
          接收方: 'receiver',
          Receiver: 'receiver',
          协议类型: 'protocolType',
          ProtocolType: 'protocolType',
          'Protocol Type': 'protocolType',
          波特率: 'baudRate',
          BaudRate: 'baudRate',
          Speed: 'speed',
          传输频率: 'frequency',
          发送频率: 'frequency',
          Frequency: 'frequency',
          '传输速率/bps': 'speed',
          校验方式: 'checkMode',
          CheckMode: 'checkMode',
          数据位: 'dataBits',
          DataBits: 'dataBits',
          停止位: 'stopBits',
          StopBits: 'stopBits',
          发送方式: 'method',
          Method: 'method',
          '发送时长/ms': 'sendDuration',
          发送时长: 'duration',
          Duration: 'duration',
          '帧长度/Byte': 'frameLength',
          '帧长度/word': 'frameLength',
          帧长: 'frameLength',
          FrameLength: 'frameLength',
          端口号: 'port',
          子地址: 'subAddress',
          错误处理: 'errorHandle',
          ErrorHandling: 'errorHandle',
        };

        jsonData.forEach((row) => {
          if (row.length >= 2) {
            const key = (row[0] || '').toString().trim();
            const value = row[1];

            if (keyMap[key]) {
              config[keyMap[key]] = value;
            }
          }
        });

        resolve(config);
      } catch {
        resolve({});
      }
    };
    reader.onerror = () => resolve({});
    reader.readAsArrayBuffer(file);
  });
}

const { dialogProps, dialogEvents, open, close } = useDialog({
  title: () => '导入协议数据',
  width: '600px',
  okText: '确定导入',
  preValidate: false,
  autoScrollToError: false,
  onConfirm: async () => {
    if (!fileInfo.value) {
      ElMessage.warning('请先选择要导入的文件');
      throw new Error('no_file');
    }

    try {
      const formData = new FormData();
      formData.append('file', fileInfo.value);

      const [backendResult, frontendConfig] = await Promise.all([
        previewProtocolImport(formData),
        parseProtocolConfig(fileInfo.value),
      ]);

      console.log('backendResult', backendResult);
      console.log('frontendConfig', frontendConfig);

      const payload = backendResult?.data || {};
      const fieldCount = payload?.fields?.length || 0;
      const importedProtocolType = payload?.protocolType;

      const finalResult = {
        ...payload,
        header: {
          ...(payload.header || {}),
          ...frontendConfig,
        },
      };

      const hasConfig = Object.keys(frontendConfig).length > 0;
      if (!fieldCount && !hasConfig) {
        ElMessage.warning('文件中没有有效的数据（字段或配置）');
        throw new Error('empty_data');
      }

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

      let msg = '导入成功';
      if (fieldCount) msg += `，包含 ${fieldCount} 个字段`;
      if (hasConfig) msg += `，已更新协议配置`;
      ElMessage.success(msg);

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
