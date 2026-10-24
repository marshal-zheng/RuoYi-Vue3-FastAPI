<template>
  <ZxDrawer
    v-bind="drawer.drawerProps.value"
    v-on="drawer.drawerEvents.value"
    :title="`配置协议 - ${portData?.interfaceName || '端口'}`"
    :size="800"
    placement="right"
  >
    <el-form
      ref="formRef"
      :model="drawer.state.data"
      :rules="rules"
      label-width="100px"
      label-position="left"
    >
      <!-- 端口信息展示 -->
      <el-form-item label="端口名称">
        <zx-input v-model="drawer.state.data.interfaceName" disabled />
      </el-form-item>

      <el-form-item label="总线类型">
        <el-tag :type="getInterfaceTypeTag(drawer.state.data.interfaceType)">
          {{ drawer.state.data.interfaceType }}
        </el-tag>
      </el-form-item>

      <!-- 协议选择 -->
      <el-form-item label="协议类型" prop="protocolType">
        <ProtocolTypeSelector
          v-model="drawer.state.data.protocolType"
          placeholder="请选择协议类型"
          style="width: 100%"
          :bus-type="drawer.state.data.interfaceType"
          @change="handleProtocolTypeChange"
        />
      </el-form-item>

      <!-- 数据速率 -->
      <el-form-item label="数据速率" prop="dataRate">
        <zx-input
          v-model="drawer.state.data.dataRate"
          placeholder="例如：9600bps, 1Mbps"
          clearable
          maxlength="50"
        />
      </el-form-item>

      <!-- 协议描述 -->
      <el-form-item label="协议描述">
        <zx-input
          v-model="drawer.state.data.description"
          type="textarea"
          placeholder="请输入协议描述"
          :rows="3"
          maxlength="200"
          show-word-limit
        />
      </el-form-item>
    </el-form>

    <!-- 协议格式配置 -->
    <div v-if="drawer.state.data.protocolType" class="protocol-template-section">
      <el-divider content-position="left">
        <span class="template-title text-[16px] font-semibold">协议格式配置</span>
      </el-divider>
      <component
        :is="currentTemplateComponent"
        ref="templateRef"
        v-if="currentTemplateComponent"
        v-model="drawer.state.data.protocolConfig"
        :protocol-type="drawer.state.data.protocolType"
      />
      <el-alert
        v-else
        title="暂不支持该协议类型的详细配置"
        type="info"
        :closable="false"
        show-icon
      />
    </div>
  </ZxDrawer>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useDrawer } from '@zxio/zxui/hooks';
import ProtocolTypeSelector from '@/components/business/Protocol/selector/ProtocolTypeSelector.vue';
import EthernetProtocolTemplate from '@/components/business/Protocol/templates/EthernetProtocolTemplate.vue';
import RS422ProtocolTemplate from '@/components/business/Protocol/templates/RS422ProtocolTemplate.vue';
import CANProtocolTemplate from '@/components/business/Protocol/templates/CANProtocolTemplate.vue';
import Protocol1553BTemplate from '@/components/business/Protocol/templates/Protocol1553BTemplate.vue';

const props = defineProps({
  portData: {
    type: Object,
    default: () => ({}),
  },
});

const emit = defineEmits(['submit']);

const formRef = ref(null);
const templateRef = ref(null);

const drawer = useDrawer({
  divider: true,
  size: 800,
  placement: 'right',
  okText: '确定',
  formRef,
  preValidate: true,
  autoScrollToError: true,
  autoResetForm: true,
  defaultData: () => ({
    interfaceId: null,
    interfaceName: '',
    interfaceType: '',
    busType: '',
    protocolType: '',
    dataRate: '',
    description: '',
    protocolConfig: {},
  }),
  async onConfirm() {
    // 校验协议模板（VXE-Table 表格校验）
    if (templateRef.value?.validateBeforeSave) {
      const templateValid = await templateRef.value.validateBeforeSave();
      if (!templateValid) {
        return false;
      }
    }

    const protocolData = { ...drawer.state.data };
    emit('submit', protocolData);
    return true;
  },
});

// 表单验证规则
const rules = {
  protocolType: [{ required: true, message: '请选择协议类型', trigger: 'change' }],
  dataRate: [{ max: 50, message: '数据速率不能超过50个字符', trigger: 'blur' }],
};

// 获取当前协议模板组件
const currentTemplateComponent = computed(() => {
  const type = String(drawer.state.data.protocolType || '').toLowerCase();
  switch (type) {
    case 'ethernet':
      return EthernetProtocolTemplate;
    case 'rs422':
    case 'rs485':
      return RS422ProtocolTemplate;
    case 'can':
      return CANProtocolTemplate;
    case '1553b':
      return Protocol1553BTemplate;
    default:
      return null;
  }
});

// 协议类型改变时清空配置
const handleProtocolTypeChange = () => {
  drawer.state.data.protocolConfig = {};
};

// 获取接口类型标签
const getInterfaceTypeTag = (type) => {
  const typeMap = {
    RS422: 'success',
    RS485: 'warning',
    CAN: 'danger',
    Ethernet: 'primary',
    '1553B': 'info',
  };
  return typeMap[type] || 'info';
};

// 打开抽屉
const open = (portData) => {
  const port = portData || props.portData || {};
  drawer.open({
    interfaceId: port.interfaceId || port.id,
    interfaceName: port.interfaceName || '',
    interfaceType: port.interfaceType || port.busType || '',
    busType: port.busType || port.interfaceType || '',
    protocolType: port.protocolType || '',
    dataRate: port.dataRate || '',
    description: port.description || '',
    protocolConfig: port.protocolConfig || {},
  });
};

defineExpose({
  open,
  close: drawer.close,
});
</script>

<style lang="less" scoped>
:deep(.el-drawer__body) {
  padding: 20px;
}

.protocol-template-section {
  margin-top: 24px;

  .template-title {
    font-size: 16px;
    font-weight: 600;
    color: var(--zx-semantic-text-primary);
  }
}
</style>
