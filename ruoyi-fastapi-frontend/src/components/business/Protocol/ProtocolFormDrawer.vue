<template>
  <ZxDrawer
    v-bind="drawer.drawerProps.value"
    v-on="drawer.drawerEvents.value"
    :title="isEdit ? '编辑协议' : '新增协议'"
    size="70%"
    placement="right"
    :loading="drawerLoading"
    :noContentPadding="false"
    loadingType="skeleton"
    class="protocol-drawer"
  >
    <el-form
      ref="formRef"
      :model="drawer.state.data"
      :rules="formRules"
      label-position="top"
      class="protocol-form"
    >
      <el-form-item label="协议名称" prop="protocolName">
        <el-input
          v-model="drawer.state.data.protocolName"
          placeholder="请输入协议名称"
          maxlength="50"
          show-word-limit
          clearable
        />
      </el-form-item>

      <el-form-item label="协议类型" prop="protocolType">
        <ProtocolTypeSelector
          v-model="drawer.state.data.protocolType"
          placeholder="请选择协议类型"
          style="width: 100%"
          defaultFirst
          @change="handleProtocolTypeChange"
        />
      </el-form-item>

      <el-form-item label="协议描述" prop="description">
        <el-input
          v-model="drawer.state.data.description"
          type="textarea"
          placeholder="请输入备注信息"
          :rows="3"
          maxlength="200"
          show-word-limit
        />
      </el-form-item>

      <div v-if="drawer.state.data.protocolType" class="protocol-config-section">
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
            v-model="drawer.state.data.protocolConfig"
            :protocol-type="drawer.state.data.protocolType"
            :sender-editable="senderEditable"
            :receiver-editable="receiverEditable"
            v-bind="currentTemplateProps"
          />
        </div>
      </div>
    </el-form>
    <ImportFileDialog
      ref="importDialogRef"
      :protocol-type="drawer.state.data.protocolType?.toLowerCase()"
      :protocol-id="drawer.state.data.protocolId"
      @confirm="handleImportConfirm"
    />
  </ZxDrawer>
</template>

<script setup name="ProtocolFormDrawer">
import { ref, computed } from 'vue';
import { useDrawer } from '@zxio/zxui';
import ProtocolTypeSelector from './selector/ProtocolTypeSelector.vue';
import EthernetProtocolTemplate from './templates/EthernetProtocolTemplate.vue';
import RS422ProtocolTemplate from './templates/RS422ProtocolTemplate.vue';
import RS485ProtocolTemplate from './templates/RS422ProtocolTemplate.vue';
import CANProtocolTemplate from './templates/CANProtocolTemplate.vue';
import Protocol1553BTemplate from './templates/Protocol1553BTemplate.vue';

import ImportFileDialog from './ImportFileDialog.vue';

const emit = defineEmits(['success']);
const props = defineProps({
  senderEditable: {
    type: Boolean,
    default: false,
  },
  receiverEditable: {
    type: Boolean,
    default: false,
  },
});

const formRef = ref(null);
const drawerLoading = ref(false);
const importDialogRef = ref(null);
const senderEditable = computed(() => props.senderEditable !== false);
const receiverEditable = computed(() => props.receiverEditable !== false);

const drawer = useDrawer({
  width: '600px', // Consistent width with other drawers
  placement: 'right',
  okText: '保存',
  formRef,
  formModel: computed(() => drawer.state.data),
  preValidate: true,
  autoScrollToError: true,
  autoResetForm: true,
  defaultData: () => ({
    protocolId: null,
    protocolName: '',
    protocolType: '',
    description: '',
    remark: '',
    protocolConfig: {},
  }),
  async onConfirm() {
    const submitData = { ...drawer.state.data };
    emit('success', submitData);
    return true;
  },
  onConfirmError: () => {},
});

// 协议模板组件映射表，键为字典的 dictValue（统一转小写）
const TEMPLATE_COMPONENTS = {
  lan: EthernetProtocolTemplate,
  rs422: RS422ProtocolTemplate,
  rs485: RS485ProtocolTemplate,
  can: CANProtocolTemplate,
  '1553b': Protocol1553BTemplate,
};

const isEdit = computed(() => !!drawer.state.data.protocolId);

const formRules = {
  protocolName: [
    { required: true, message: '请输入协议名称', trigger: 'blur' },
    { min: 2, max: 50, message: '协议名称长度在 2 到 50 个字符', trigger: 'blur' },
  ],
  protocolType: [{ required: true, message: '请选择协议类型', trigger: 'change' }],
  description: [{ max: 200, message: '备注信息不能超过 200 个字符', trigger: 'blur' }],
};

const currentTemplateComponent = computed(() => {
  const rawValue = drawer.state.data.protocolType;
  if (!rawValue) return null;

  const valueStr = String(rawValue).toLowerCase();
  return TEMPLATE_COMPONENTS[valueStr] || null;
});

const currentProtocolLabel = computed(() => {
  const rawValue = drawer.state.data.protocolType;
  if (!rawValue) return '';
  return String(rawValue).toUpperCase();
});

const currentTemplateProps = computed(() => {
  const valueStr = String(drawer.state.data.protocolType || '').toLowerCase();
  if (valueStr === 'rs422') return { protocolLabel: 'RS422' };
  if (valueStr === 'rs485') return { protocolLabel: 'RS485' };
  return {};
});

const handleProtocolTypeChange = () => {
  drawer.state.data.protocolConfig = {};
};

const handleImport = () => {
  importDialogRef.value?.open();
};

const handleImportConfirm = (data) => {
  if (!data) return;

  if (data.switchProtocolType) {
    drawer.state.data.protocolType = data.switchProtocolType;
    drawer.state.data.protocolConfig = {};
  }

  const config = { ...drawer.state.data.protocolConfig };

  if (data.header) {
    Object.assign(config, normalizeHeader(data.header));
  }

  if (data.fields && data.fields.length > 0) {
    config.fields = data.fields.map((field) => ({
      ...field,
      id: field.id || Date.now().toString() + Math.random(),
      parentId: field.parentId || null,
    }));
  }

  drawer.state.data.protocolConfig = config;
};

const openDrawer = async (protocolData) => {
  if (protocolData && protocolData.protocolId) {
    drawer.open();
    drawerLoading.value = true;
    try {
      drawer.state.data = {
        protocolId: protocolData.protocolId,
        protocolName: protocolData.protocolName || '',
        protocolType: protocolData.protocolType || '',
        description: protocolData.description || '',
        remark: protocolData.remark || '',
        protocolConfig: normalizeHeader(protocolData.protocolConfig || {}),
      };
    } finally {
      drawerLoading.value = false;
    }
  } else {
    drawer.open();
  }
};

// 兼容后端 header 字段命名（errorHandling -> errorHandle 等）
const normalizeHeader = (rawConfig = {}) => {
  const cfg = { ...rawConfig };
  if (cfg.errorHandle === undefined && cfg.errorHandling !== undefined) {
    cfg.errorHandle = cfg.errorHandling;
  }
  if (cfg.sendDuration === undefined && cfg.duration !== undefined) {
    cfg.sendDuration = cfg.duration;
  }
  return cfg;
};

defineExpose({
  open: openDrawer,
  close: drawer.close,
});
</script>

<style lang="less" scoped>
.protocol-form {
  padding: 0 4px;
}

.protocol-config-section {
  margin-top: 24px;
  background-color: var(--el-fill-color-light);
  border-radius: 8px;
  padding: 16px;
  border: 1px solid var(--el-border-color-lighter);

  .section-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--el-border-color-lighter);

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
    :deep(.el-form-item) {
      margin-bottom: 18px;

      &:last-child {
        margin-bottom: 0;
      }
    }
  }
}
</style>
