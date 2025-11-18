<template>
  <ZxDrawer
    v-bind="drawer.drawerProps.value"
    v-on="drawer.drawerEvents.value"
    :title="isEdit ? '编辑协议' : '新增协议'"
    :size="'65%'"
    :placement="'right'"
    :loading="drawerLoading"
    :noContentPadding="false"
    loadingType="skeleton"
  >
    <el-form
      ref="formRef"
      :model="drawer.state.data"
      :rules="formRules"
      label-position="right"
      label-width="100px"
      class="space-y-4"
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
    </el-form>

    <div v-if="drawer.state.data.protocolType" class="protocol-template-section mt-6">
      <el-divider content-position="left">
        <span class="template-title text-[16px] font-semibold text-[#303133]">协议格式配置</span>
      </el-divider>
      <component
        :is="currentTemplateComponent"
        v-if="currentTemplateComponent"
        v-model="drawer.state.data.protocolConfig"
        :protocol-type="drawer.state.data.protocolType"
      />
    </div>
  </ZxDrawer>
</template>

<script setup name="ProtocolFormDrawer">
import { ref, computed } from 'vue';
import { useDrawer } from '@zxio/zxui';
import ProtocolTypeSelector from './selector/ProtocolTypeSelector.vue';
import EthernetProtocolTemplate from './templates/EthernetProtocolTemplate.vue';
import RS422ProtocolTemplate from './templates/RS422ProtocolTemplate.vue';
import CANProtocolTemplate from './templates/CANProtocolTemplate.vue';
import Protocol1553BTemplate from './templates/Protocol1553BTemplate.vue';

const emit = defineEmits(['success']);

const formRef = ref(null);
const drawerLoading = ref(false);

const drawer = useDrawer({
  width: '75%',
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
  const t = String(drawer.state.data.protocolType || '').toLowerCase();
  switch (t) {
    case 'ethernet':
      return EthernetProtocolTemplate;
    case 'rs422':
      return RS422ProtocolTemplate;
    case 'can':
      return CANProtocolTemplate;
    case '1553b':
      return Protocol1553BTemplate;
    default:
      return null;
  }
});

const handleProtocolTypeChange = () => {
  drawer.state.data.protocolConfig = {};
};

const openDrawer = async protocolData => {
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
        protocolConfig: protocolData.protocolConfig || {},
      };
    } finally {
      drawerLoading.value = false;
    }
  } else {
    drawer.open();
  }
};

defineExpose({
  open: openDrawer,
  close: drawer.close,
});
</script>

<style lang="less" scoped>
.protocol-form-container {
  padding: 20px;
  min-height: 400px;

  .version-tip {
    margin-left: 8px;
    font-size: 12px;
    color: #909399;
  }

  .protocol-template-section {
    margin-top: 24px;

    .template-title {
      font-size: 16px;
      font-weight: 600;
      color: #303133;
    }
  }
}

.drawer-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 20px;
  border-top: 1px solid #e4e7ed;
}
</style>
