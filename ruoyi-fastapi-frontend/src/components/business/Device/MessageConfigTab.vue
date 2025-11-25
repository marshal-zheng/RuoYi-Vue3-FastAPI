<template>
  <div class="message-config-tab">
    <!-- 协议配置区域 -->
    <div v-if="currentTemplateComponent" class="protocol-config-section">
      <div class="section-header">
        <div class="flex items-center gap-2">
          <span class="section-title">协议格式配置</span>
          <el-tag size="small" type="info" effect="plain">{{ currentProtocolLabel }}</el-tag>
        </div>
        <el-button type="primary" link icon="Upload" @click="handleImport">导入配置</el-button>
      </div>

      <div class="config-content">
        <component
          :is="currentTemplateComponent"
          v-if="currentTemplateComponent"
          ref="templateRef"
          v-model="protocolConfig"
          :deviceMode="deviceMode"
          :senderEditable="!deviceMode"
          :receiverEditable="!deviceMode"
        />
      </div>
    </div>

    <el-empty
      v-else
      description="请先选择协议类型"
      class="bg-white rounded-lg border border-dashed border-gray-300 mt-4"
    />

    <!-- 导入文件对话框 -->
    <ImportFileDialog
      ref="importDialogRef"
      :protocol-type="portInfo?.interfaceType?.toLowerCase()"
      :protocol-id="portInfo?.protocolId"
      @confirm="handleImportConfirm"
    />
  </div>
</template>

<script setup name="MessageConfigTab">
import { ref, computed, watch } from 'vue';
import { ElMessage } from 'element-plus';
import ImportFileDialog from '../Protocol/ImportFileDialog.vue';
import {
  EthernetProtocolTemplate,
  RS422ProtocolTemplate,
  RS422ProtocolTemplate as RS485ProtocolTemplate,
  CANProtocolTemplate,
  Protocol1553BTemplate,
} from '../Protocol/templates';

const props = defineProps({
  portInfo: {
    type: Object,
    default: () => ({}),
  },
  // 设备模式：在设备侧使用时，发送方/接收方应保持为空且不自动填充
  deviceMode: {
    type: Boolean,
    default: false,
  },
});

// 模板引用
const templateRef = ref();

// 导入对话框引用
const importDialogRef = ref();

// 协议配置数据
const protocolConfig = ref({});

// 根据接口类型映射协议模板组件
const PROTOCOL_TEMPLATE_MAP = {
  ethernet: EthernetProtocolTemplate,
  lan: EthernetProtocolTemplate, // 兼容 LAN
  rs422: RS422ProtocolTemplate,
  rs485: RS485ProtocolTemplate, // 兼容 RS485
  can: CANProtocolTemplate,
  '1553b': Protocol1553BTemplate,
};

// 当前使用的模板组件
const currentTemplateComponent = computed(() => {
  const interfaceType = props.portInfo?.interfaceType?.toLowerCase();
  return interfaceType ? PROTOCOL_TEMPLATE_MAP[interfaceType] : null;
});

const currentProtocolLabel = computed(() => {
  const interfaceType = props.portInfo?.interfaceType;
  return interfaceType ? String(interfaceType).toUpperCase() : '';
});

// 打开导入对话框
function handleImport() {
  importDialogRef.value?.open?.();
}

// 处理导入确认
function handleImportConfirm(data) {
  if (!data) return;

  // 构建协议配置对象
  const config = {
    ...protocolConfig.value,
  };

  // 更新表头信息
  if (data.header) {
    Object.assign(config, normalizeHeader(data.header));

    // 设备模式下强制清空发送方/接收方
    if (props.deviceMode) {
      config.sender = '';
      config.receiver = '';
    }
  }

  // 更新字段列表
  if (data.fields && data.fields.length > 0) {
    config.fields = data.fields.map((field) => ({
      ...field,
      id: field.id || Date.now().toString() + Math.random(),
      parentId: field.parentId || null,
    }));
  }

  protocolConfig.value = config;
  ElMessage.success('导入成功');
}

// 兼容后端 header 字段命名
function normalizeHeader(rawConfig = {}) {
  const cfg = { ...rawConfig };
  if (cfg.errorHandle === undefined && cfg.errorHandling !== undefined) {
    cfg.errorHandle = cfg.errorHandling;
  }
  if (cfg.sendDuration === undefined && cfg.duration !== undefined) {
    cfg.sendDuration = cfg.duration;
  }
  return cfg;
}

// 获取表单数据
function getFormData() {
  const config = { ...protocolConfig.value };

  // 设备模式下强制清空发送方/接收方
  if (props.deviceMode) {
    config.sender = '';
    config.receiver = '';
  }

  return {
    header: {
      sender: config.sender || '',
      receiver: config.receiver || '',
      frequency: config.frequency || '',
      baudRate: config.speed || '',
      method: config.method || '',
      duration: config.sendDuration || null,
      frameLength: config.frameLength || null,
      errorHandling: config.errorHandle || '',
    },
    fields: config.fields || [],
    protocolId: selectedProtocolId.value,
  };
}

// 验证表单
async function validate() {
  if (!props.deviceMode) {
    const config = protocolConfig.value;
    if (!config.sender) {
      ElMessage.error('请输入发送方');
      return false;
    }
  }
  return true;
}

// 清除验证
function clearValidate() {
  // 不需要清除验证
}

// 初始化数据
function initializeData() {
  if (props.portInfo.messageConfig) {
    const config = JSON.parse(JSON.stringify(props.portInfo.messageConfig.header || {}));
    const fields = JSON.parse(JSON.stringify(props.portInfo.messageConfig.fields || []));

    protocolConfig.value = {
      sender: config.sender || '',
      receiver: config.receiver || '',
      frequency: config.frequency || '',
      speed: config.baudRate || '',
      method: config.method || '',
      sendDuration: config.duration || null,
      frameLength: config.frameLength || null,
      errorHandle: config.errorHandling || '',
      fields,
    };
  } else {
    protocolConfig.value = {};
  }

  // 设备模式下，发送方/接收方保持为空
  if (!props.deviceMode && props.portInfo) {
    const currentDeviceName = props.portInfo.deviceName || '';
    const peerDeviceName = props.portInfo.peerDeviceName || '';
    const direction = props.portInfo.direction || 'forward';

    const expectedSender =
      direction === 'reverse'
        ? peerDeviceName || currentDeviceName
        : currentDeviceName || peerDeviceName;
    const expectedReceiver =
      direction === 'reverse'
        ? currentDeviceName || peerDeviceName
        : peerDeviceName || currentDeviceName;

    if (!protocolConfig.value.sender && expectedSender) {
      protocolConfig.value.sender = expectedSender;
    }
    if (!protocolConfig.value.receiver && expectedReceiver) {
      protocolConfig.value.receiver = expectedReceiver;
    }
  } else if (props.deviceMode) {
    protocolConfig.value.sender = '';
    protocolConfig.value.receiver = '';
  }
}

// 监听 portInfo 变化，每次打开不同端口时重新加载数据
watch(
  () => props.portInfo,
  () => {
    initializeData();
  },
  { deep: true, immediate: true }
);

// 添加字段
const handleAddField = () => {
  templateRef.value?.insertRow?.();
};

// 删除选中
const handleDeleteSelected = () => {
  templateRef.value?.removeSelectRow?.();
};

// 暴露方法（兼容旧接口）
defineExpose({
  getFormData,
  validate,
  clearValidate,
  handleAddField,
  handleDeleteSelected,
});
</script>

<style lang="less" scoped>
.message-config-tab {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 0 4px;
}

.protocol-config-section {
  background-color: var(--el-fill-color-light);
  border-radius: 8px;
  padding: 16px;
  border: 1px solid var(--el-border-color-lighter);
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;

  .section-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--el-border-color-lighter);
    flex-shrink: 0;

    .section-title {
      font-size: 15px;
      font-weight: 600;
      color: var(--el-text-color-primary);
      position: relative;
      padding-left: 12px;

      &::before {
        content: '';
        position: absolute;
        left: 0;
        top: 50%;
        transform: translateY(-50%);
        width: 4px;
        height: 14px;
        background-color: var(--el-color-primary);
        border-radius: 2px;
      }
    }
  }

  .config-content {
    flex: 1;
    overflow: auto;

    /* 修复表格在 flex 容器中的高度问题 */
    :deep(.protocol-template-wrapper) {
      height: 100%;
      display: flex;
      flex-direction: column;

      .vxe-table--render-wrapper {
        height: 100% !important;
      }
    }
  }
}
</style>
