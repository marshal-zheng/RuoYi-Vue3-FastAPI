<template>
  <el-drawer
    v-model="visible"
    :title="`配置协议 - ${portData?.interfaceName || '端口'}`"
    :size="800"
    :before-close="handleClose"
    destroy-on-close
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="100px"
      label-position="left"
    >
      <!-- 端口信息展示 -->
      <el-form-item label="端口名称">
        <el-input v-model="formData.interfaceName" disabled />
      </el-form-item>

      <el-form-item label="总线类型">
        <el-tag :type="getInterfaceTypeTag(formData.interfaceType)">
          {{ formData.interfaceType }}
        </el-tag>
      </el-form-item>

      <!-- 协议选择 -->
      <el-form-item label="协议类型" prop="protocolType">
        <ProtocolTypeSelector
          v-model="formData.protocolType"
          placeholder="请选择协议类型"
          style="width: 100%"
          :bus-type="formData.interfaceType"
          @change="handleProtocolTypeChange"
        />
      </el-form-item>

      <!-- 数据速率 -->
      <el-form-item label="数据速率" prop="dataRate">
        <el-input
          v-model="formData.dataRate"
          placeholder="例如：9600bps, 1Mbps"
          clearable
          maxlength="50"
        />
      </el-form-item>

      <!-- 协议描述 -->
      <el-form-item label="协议描述">
        <el-input
          v-model="formData.description"
          type="textarea"
          placeholder="请输入协议描述"
          :rows="3"
          maxlength="200"
          show-word-limit
        />
      </el-form-item>
    </el-form>

    <!-- 协议格式配置 -->
    <div v-if="formData.protocolType" class="protocol-template-section">
      <el-divider content-position="left">
        <span class="template-title text-[16px] font-semibold text-[#303133]">协议格式配置</span>
      </el-divider>
      <component
        :is="currentTemplateComponent"
        v-if="currentTemplateComponent"
        v-model="formData.protocolConfig"
        :protocol-type="formData.protocolType"
      />
      <el-alert
        v-else
        title="暂不支持该协议类型的详细配置"
        type="info"
        :closable="false"
        show-icon
      />
    </div>

    <template #footer>
      <div class="drawer-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitLoading"> 确定 </el-button>
      </div>
    </template>
  </el-drawer>
</template>

<script setup>
import { ref, reactive, watch, nextTick, computed } from 'vue';
import { ElMessage } from 'element-plus';
import ProtocolTypeSelector from '@/components/business/Protocol/selector/ProtocolTypeSelector.vue';
import EthernetProtocolTemplate from '@/components/business/Protocol/templates/EthernetProtocolTemplate.vue';
import RS422ProtocolTemplate from '@/components/business/Protocol/templates/RS422ProtocolTemplate.vue';
import CANProtocolTemplate from '@/components/business/Protocol/templates/CANProtocolTemplate.vue';
import Protocol1553BTemplate from '@/components/business/Protocol/templates/Protocol1553BTemplate.vue';

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
  portData: {
    type: Object,
    default: () => ({}),
  },
});

const emit = defineEmits(['update:modelValue', 'submit']);

const visible = ref(false);
const formRef = ref(null);
const submitLoading = ref(false);

// 表单数据
const formData = reactive({
  interfaceId: null,
  interfaceName: '',
  interfaceType: '',
  busType: '',
  protocolType: '',
  dataRate: '',
  description: '',
  protocolConfig: {},
});

// 表单验证规则
const rules = {
  protocolType: [{ required: true, message: '请选择协议类型', trigger: 'change' }],
  dataRate: [{ max: 50, message: '数据速率不能超过50个字符', trigger: 'blur' }],
};

// 监听 modelValue 变化
watch(
  () => props.modelValue,
  (newVal) => {
    visible.value = newVal;
    if (newVal && props.portData) {
      initFormData();
    }
  },
  { immediate: true }
);

// 监听 visible 变化
watch(visible, (newVal) => {
  emit('update:modelValue', newVal);
});

// 初始化表单数据
const initFormData = () => {
  nextTick(() => {
    const port = props.portData || {};
    formData.interfaceId = port.interfaceId || port.id;
    formData.interfaceName = port.interfaceName || '';
    formData.interfaceType = port.interfaceType || port.busType || '';
    formData.busType = port.busType || port.interfaceType || '';
    formData.protocolType = port.protocolType || '';
    formData.dataRate = port.dataRate || '';
    formData.description = port.description || '';
    formData.protocolConfig = port.protocolConfig || {};

    // 清除验证状态
    if (formRef.value) {
      formRef.value.clearValidate();
    }
  });
};

// 获取当前协议模板组件
const currentTemplateComponent = computed(() => {
  const type = String(formData.protocolType || '').toLowerCase();
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
  formData.protocolConfig = {};
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

// 关闭抽屉
const handleClose = () => {
  visible.value = false;
};

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return;

  try {
    await formRef.value.validate();

    submitLoading.value = true;

    // 组装协议数据
    const protocolData = {
      interfaceId: formData.interfaceId,
      interfaceName: formData.interfaceName,
      interfaceType: formData.interfaceType,
      busType: formData.busType,
      protocolType: formData.protocolType,
      dataRate: formData.dataRate,
      description: formData.description,
      protocolConfig: formData.protocolConfig,
    };

    emit('submit', protocolData);

    // 不在这里显示成功消息，由父组件处理
    handleClose();
  } catch (error) {
    console.error('表单验证失败:', error);
  } finally {
    submitLoading.value = false;
  }
};
</script>

<style lang="less" scoped>
.drawer-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

:deep(.el-drawer__body) {
  padding: 20px;
}

:deep(.el-drawer__footer) {
  padding: 16px 20px;
  border-top: 1px solid var(--el-border-color-light);
}

.protocol-template-section {
  margin-top: 24px;

  .template-title {
    font-size: 16px;
    font-weight: 600;
    color: #303133;
  }
}
</style>
