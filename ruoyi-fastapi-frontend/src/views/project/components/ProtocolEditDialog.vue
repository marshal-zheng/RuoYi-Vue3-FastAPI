<template>
  <ZxDialog v-bind="dialog.dialogProps.value" v-on="dialog.dialogEvents.value">
    <MessageConfigTab ref="messageConfigRef" :port-info="currentPortInfo">
      <template #toolbar>
        <div class="toolbar-left flex items-center gap-2">
          <zx-button type="primary" icon="Plus" size="medium" @click="handleAddField"
            >添加字段</zx-button
          >
          <zx-button type="danger" icon="Delete" size="medium" @click="handleDeleteSelected"
            >删除选中</zx-button
          >
        </div>
        <div class="toolbar-right flex items-center">
          <ProtocolTemplateSelector
            style="width: 200px"
            v-model="selectedProtocolId"
            :protocolType="currentPortInfo?.interfaceType?.toLowerCase()"
            placeholder="选择协议"
            clearable
            size="medium"
            @entity="handleProtocolChange"
          />
        </div>
      </template>
    </MessageConfigTab>
  </ZxDialog>
</template>

<script setup>
import { ref, computed } from 'vue';
import { ElMessage } from 'element-plus';
import { useDialog } from '@zxio/zxui';
import MessageConfigTab from '@/components/business/Device/MessageConfigTab.vue';
import ProtocolTemplateSelector from '@/components/business/Protocol/selector/ProtocolTemplateSelector.vue';

const emit = defineEmits(['submit']);

const messageConfigRef = ref(null);
const selectedProtocolId = ref(null);
const currentPortInfo = ref(null);

// 使用 useDialog
const dialog = useDialog({
  title: () => `配置协议 - ${currentPortInfo.value?.interfaceName || ''}`,
  width: '80%',
  hegiht: '90%',
  okText: '保存',
  cancelText: '取消',
  async onConfirm() {
    if (!messageConfigRef.value) {
      return false;
    }

    // 验证表单
    const valid = await messageConfigRef.value.validate();
    if (!valid) {
      return false;
    }

    // 获取表单数据
    const formData = messageConfigRef.value.getFormData();

    // 触发提交事件
    emit('submit', {
      messageConfig: {
        header: formData.header,
        fields: formData.fields,
      },
      protocolId: formData.protocolId,
    });

    ElMessage.success('协议配置已更新');
    return true;
  },
});

// 打开对话框
const open = (portInfo = {}) => {
  currentPortInfo.value = portInfo;
  selectedProtocolId.value = portInfo?.protocolId || null;
  dialog.open();
};

// 关闭对话框
const close = () => {
  dialog.close();
};

// 添加字段（代理到 MessageConfigTab）
const handleAddField = () => {
  messageConfigRef.value?.handleAddField?.();
};

// 删除选中（代理到 MessageConfigTab）
const handleDeleteSelected = () => {
  messageConfigRef.value?.handleDeleteSelected?.();
};

// 协议模板选择（代理到 MessageConfigTab）
const handleProtocolChange = entity => {
  messageConfigRef.value?.handleProtocolChange?.(entity);
};

defineExpose({
  open,
  close,
});
</script>

<style lang="less" scoped>
.toolbar-left {
  column-gap: 8px;
  display: flex;
  align-items: center;
}

.toolbar-right {
  column-gap: 8px;
  display: flex;
  align-items: center;
}
</style>
