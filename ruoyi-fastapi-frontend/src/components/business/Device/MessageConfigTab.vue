<template>
  <div class="message-config-tab">
    <!-- 协议选择区域 -->
    <div v-if="currentTemplateComponent" class="protocol-selector-section">
      <div class="flex items-center gap-3">
        <span class="text-sm font-medium text-zx-text-primary"
          >选择协议模板：</span
        >
        <ProtocolTemplateSelector
          v-model="selectedProtocolId"
          :protocol-type="portInfo?.interfaceType?.toLowerCase()"
          placeholder="请选择已有协议模板"
          clearable
          style="flex: 1"
          @entity-change="handleProtocolSelect"
        />
      </div>
    </div>

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
      class="rounded-lg border-dashed mt-4"
      data-zx-surface="card"
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
import ProtocolTemplateSelector from '../Protocol/selector/ProtocolTemplateSelector.vue';
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

// 选中的协议ID
const selectedProtocolId = ref(null);

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

// 处理协议选择
function handleProtocolSelect(protocol) {
  if (!protocol || !protocol.protocolConfig) return;

  // 从选中的协议中加载配置
  const config = protocol.protocolConfig;

  // 构建协议配置对象
  const newConfig = {
    ...protocolConfig.value,
  };

  // 更新表头信息（兼容扁平结构和嵌套结构）
  // 后端返回的 protocolConfig 可能是扁平结构（header 字段直接在根级别）
  // 或者是嵌套结构（header 字段在 config.header 中）
  const headerData = config.header || config;
  Object.assign(newConfig, normalizeHeader(headerData));

  // 设备模式下强制清空发送方/接收方
  if (props.deviceMode) {
    newConfig.sender = '';
    newConfig.receiver = '';
  }

  // 更新字段列表
  if (config.fields && config.fields.length > 0) {
    newConfig.fields = config.fields.map((field) => ({
      ...field,
      id: field.id || Date.now().toString() + Math.random(),
      parentId: field.parentId || null,
    }));
  }

  protocolConfig.value = newConfig;
}

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

  // 更新表头信息（兼容扁平结构和嵌套结构）
  const headerData = data.header || data;
  Object.assign(config, normalizeHeader(headerData));

  // 设备模式下强制清空发送方/接收方
  if (props.deviceMode) {
    config.sender = '';
    config.receiver = '';
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
  // CAN 协议 ID 字段兼容（后端可能用 id、canId、frameId）
  if (cfg.canId === undefined) {
    cfg.canId = cfg.id || cfg.frameId || '';
  }
  // 1553B 协议子地址字段兼容
  if (cfg.subAddress === undefined) {
    cfg.subAddress = cfg.sub_address || cfg.subaddress || '';
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
      frequencyLabel: config.frequencyLabel || '',
      baudRate: config.speed || '',
      speed: config.speed || '',
      speedLabel: config.speedLabel || '',
      method: config.method || '',
      methodLabel: config.methodLabel || '',
      duration: config.sendDuration || null,
      sendDuration: config.sendDuration || null,
      frameLength: config.frameLength || null,
      errorHandling: config.errorHandle || '',
      errorHandle: config.errorHandle || '',
      errorHandleLabel: config.errorHandleLabel || '',
      errorHandlingLabel: config.errorHandleLabel || '',
      // 以太网协议字段
      port: config.port || '',
      // CAN 协议字段
      canId: config.canId || '',
      id: config.canId || '', // 兼容后端可能使用 id 字段
      // 1553B 协议字段
      subAddress: config.subAddress || '',
      // 通用
      notes: config.notes || '',
    },
    fields: config.fields || [],
    protocolId: props.portInfo?.protocolId || null,
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

  // 校验协议模板（VXE-Table 表格校验）
  if (templateRef.value?.validateBeforeSave) {
    const templateValid = await templateRef.value.validateBeforeSave();
    if (!templateValid) {
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
  // 设置选中的协议ID
  selectedProtocolId.value = props.portInfo?.protocolId || null;

  if (props.portInfo.messageConfig) {
    const config = JSON.parse(JSON.stringify(props.portInfo.messageConfig.header || {}));
    const fields = JSON.parse(JSON.stringify(props.portInfo.messageConfig.fields || []));

    protocolConfig.value = {
      sender: config.sender || '',
      receiver: config.receiver || '',
      frequency: config.frequency || '',
      frequencyLabel: config.frequencyLabel || '',
      speed: config.baudRate || config.speed || '',
      speedLabel: config.speedLabel || '',
      method: config.method || '',
      methodLabel: config.methodLabel || '',
      sendDuration: config.duration || config.sendDuration || null,
      frameLength: config.frameLength || null,
      errorHandle: config.errorHandling || config.errorHandle || '',
      errorHandleLabel: config.errorHandleLabel || config.errorHandlingLabel || '',
      // 以太网协议字段
      port: config.port || '',
      // CAN 协议字段
      canId: config.canId || config.id || config.frameId || '',
      // 1553B 协议字段
      subAddress: config.subAddress || config.sub_address || config.subaddress || '',
      // 通用
      notes: config.notes || '',
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
  templateRef, // 暴露协议模板 ref，供父组件访问校验状态
});
</script>

<style lang="less" scoped>
.message-config-tab {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 0 4px;
  gap: 12px;
}

// .protocol-selector-section {
//   background-color: var(--el-fill-color-light);
//   border-radius: 8px;
//   padding: 12px 16px;
//   border: 1px solid var(--el-border-color-lighter);
//   flex-shrink: 0;
// }

// .protocol-config-section {
//   background-color: var(--el-fill-color-light);
//   border-radius: 8px;
//   padding: 16px;
//   border: 1px solid var(--el-border-color-lighter);
//   flex: 1;
//   display: flex;
//   flex-direction: column;
//   overflow: hidden;

//   .section-header {
//     display: flex;
//     align-items: center;
//     justify-content: space-between;
//     margin-bottom: 16px;
//     padding-bottom: 12px;
//     border-bottom: 1px solid var(--el-border-color-lighter);
//     flex-shrink: 0;

//     .section-title {
//       font-size: 15px;
//       font-weight: 600;
//       color: var(--el-text-color-primary);
//       position: relative;
//       padding-left: 12px;

//       &::before {
//         content: '';
//         position: absolute;
//         left: 0;
//         top: 50%;
//         transform: translateY(-50%);
//         width: 4px;
//         height: 14px;
//         background-color: var(--el-color-primary);
//         border-radius: 2px;
//       }
//     }
//   }

//   .config-content {
//     flex: 1;
//     overflow: auto;

//     /* 修复表格在 flex 容器中的高度问题 */
//     :deep(.protocol-template-wrapper) {
//       height: 100%;
//       display: flex;
//       flex-direction: column;

//       .vxe-table--render-wrapper {
//         height: 100% !important;
//       }
//     }
//   }
// }
</style>
