<template>
  <ZxDialog
    v-bind="dialog.dialogProps.value"
    v-on="dialog.dialogEvents.value"
    class="simulation-dialog"
  >
    <template #header>
      <div class="flex items-center gap-2.5 font-semibold text-base">
        <el-icon :size="20" class="text-zx-accent-on-surface"><Lightning /></el-icon>
        <span>{{ dialog.state.data?.eventId ? '编辑事件' : '添加事件' }}</span>
      </div>
    </template>

    <el-form ref="formRef" :model="formData" :rules="formRules" label-width="90px">
      <el-form-item label="事件名称" prop="name">
        <el-input
          v-model="formData.name"
          placeholder="请输入事件名称，如：A设备给B设备发自检指令"
        />
      </el-form-item>

      <el-divider>触发条件</el-divider>

      <el-form-item label="条件类型" prop="conditionType">
        <ConditionTypeSelector
          v-model="formData.conditionType"
          style="width: 100%"
          popper-class="sim-popper-dark"
        />
      </el-form-item>

      <el-form-item v-if="formData.conditionType === 'time'" label="触发时间">
        <el-input-number v-model="formData.conditionValue.time" :min="0" style="width: 120px" />
        <span class="ml-2 text-zx-text-secondary">秒</span>
      </el-form-item>

      <el-form-item v-if="formData.conditionType === 'message_count'" label="报文数量">
        <el-input-number v-model="formData.conditionValue.count" :min="1" style="width: 120px" />
      </el-form-item>

      <el-form-item v-if="formData.conditionType === 'bandwidth_threshold'" label="阈值">
        <el-input-number
          v-model="formData.conditionValue.threshold"
          :min="0"
          :max="100"
          style="width: 120px"
        />
        <span class="ml-2 text-zx-text-secondary">%</span>
      </el-form-item>

      <el-divider>触发动作</el-divider>

      <el-form-item label="动作类型" prop="actionType">
        <ActionTypeSelector
          v-model="formData.actionType"
          style="width: 100%"
          popper-class="sim-popper-dark"
        />
      </el-form-item>

      <!-- 发送指令表单 -->
      <template v-if="formData.actionType === 'send_command'">
        <el-form-item label="源设备" prop="actionParams.sourceNodeId">
          <NodeSelector
            v-model="formData.actionParams.sourceNodeId"
            :nodes="nodes"
            placeholder="选择发送指令的设备"
            style="width: 100%"
            popper-class="sim-popper-dark"
          />
        </el-form-item>
        <el-form-item label="目标设备" prop="actionParams.targetNodeId">
          <NodeSelector
            v-model="formData.actionParams.targetNodeId"
            :nodes="nodes"
            placeholder="选择接收指令的设备"
            style="width: 100%"
            popper-class="sim-popper-dark"
          />
        </el-form-item>
        <el-form-item label="指令类型">
          <CommandTypeSelector
            v-model="formData.actionParams.commandType"
            style="width: 100%"
            popper-class="sim-popper-dark"
          />
        </el-form-item>
        <el-form-item v-if="formData.actionParams.commandType === 'custom'" label="报文内容">
          <el-input
            v-model="formData.actionParams.payload"
            placeholder="十六进制，如: AA55010100"
          />
        </el-form-item>
        <el-form-item label="协议类型">
          <ProtocolTypeSelector
            v-model="formData.actionParams.protocolType"
            style="width: 100%"
            popper-class="sim-popper-dark"
          />
        </el-form-item>
      </template>

      <!-- 发送报文表单 -->
      <template v-if="formData.actionType === 'send_message'">
        <el-form-item label="源节点">
          <NodeSelector
            v-model="formData.actionParams.sourceNodeId"
            :nodes="nodes"
            placeholder="选择源节点"
            style="width: 100%"
            popper-class="sim-popper-dark"
          />
        </el-form-item>
        <el-form-item label="目标节点">
          <NodeSelector
            v-model="formData.actionParams.targetNodeId"
            :nodes="nodes"
            placeholder="选择目标节点"
            style="width: 100%"
            popper-class="sim-popper-dark"
          />
        </el-form-item>
        <el-form-item label="报文内容">
          <el-input
            v-model="formData.actionParams.payload"
            placeholder="十六进制，如: AA55010100"
          />
        </el-form-item>
        <el-form-item label="协议类型">
          <ProtocolTypeSelector
            v-model="formData.actionParams.protocolType"
            style="width: 100%"
            popper-class="sim-popper-dark"
          />
        </el-form-item>
      </template>

      <!-- 注入故障表单 -->
      <template v-if="formData.actionType === 'inject_fault'">
        <el-form-item label="故障类型">
          <FaultTypeSelector
            v-model="formData.actionParams.faultType"
            style="width: 100%"
            popper-class="sim-popper-dark"
          />
        </el-form-item>
        <el-form-item label="目标ID">
          <el-input v-model="formData.actionParams.targetId" placeholder="链路ID或节点ID" />
        </el-form-item>
      </template>

      <!-- 记录日志表单 -->
      <template v-if="formData.actionType === 'log'">
        <el-form-item label="日志内容">
          <el-input v-model="formData.actionParams.message" placeholder="请输入日志内容" />
        </el-form-item>
        <el-form-item label="日志级别">
          <LogLevelSelector
            v-model="formData.actionParams.level"
            style="width: 100%"
            popper-class="sim-popper-dark"
          />
        </el-form-item>
      </template>
    </el-form>
  </ZxDialog>
</template>

<script setup name="EventFormDialog">
import { ref, reactive, watch } from 'vue';
import { Lightning } from '@element-plus/icons-vue';
import { useDialog } from '@zxio/zxui';
import {
  ConditionTypeSelector,
  ActionTypeSelector,
  CommandTypeSelector,
  ProtocolTypeSelector,
  FaultTypeSelector,
  LogLevelSelector,
  NodeSelector,
} from './selector';

const props = defineProps({
  nodes: {
    type: Array,
    default: () => [],
  },
});

const emit = defineEmits(['submit']);

const formRef = ref(null);

const formData = reactive({
  name: '',
  conditionType: 'manual',
  conditionValue: {},
  actionType: 'send_command',
  actionParams: {
    commandType: 'self_check',
    protocolType: 'LAN',
    level: 'info',
  },
});

const formRules = {
  name: [{ required: true, message: '请输入事件名称', trigger: 'blur' }],
  conditionType: [{ required: true, message: '请选择条件类型', trigger: 'change' }],
  actionType: [{ required: true, message: '请选择动作类型', trigger: 'change' }],
};

const dialog = useDialog({
  title: '添加事件',
  width: '560px',
  okText: '保存',
  formRef,
  formModel: formData,
  preValidate: true,
  // useDialog 约定 onConfirm 回调，返回 true 关闭弹窗
  onConfirm: handleSubmit,
});

async function handleSubmit() {
  // 兜底校验（preValidate 依赖 formRef，但加上显式校验更安全）
  if (formRef.value) {
    const valid = await formRef.value.validate();
    if (!valid) return false;
  }

  const config = {
    name: formData.name,
    condition: {
      type: formData.conditionType,
      value: formData.conditionType === 'manual' ? {} : formData.conditionValue,
    },
    action: {
      type: formData.actionType,
      params: { ...formData.actionParams },
    },
  };

  if (dialog.state.data?.eventId) {
    emit('submit', dialog.state.data.eventId, config);
  } else {
    emit('submit', null, config);
  }

  dialog.close();
  resetForm();
  return true;
}

function resetForm() {
  formData.name = '';
  formData.conditionType = 'manual';
  formData.conditionValue = {};
  formData.actionType = 'send_command';
  formData.actionParams = {
    commandType: 'self_check',
    protocolType: 'LAN',
    level: 'info',
  };
}

function open(eventData = null) {
  if (eventData) {
    formData.name = eventData.name || '';
    formData.conditionType = eventData.condition?.type || 'manual';
    formData.conditionValue = { ...eventData.condition?.value };
    formData.actionType = eventData.action?.type || 'send_command';
    formData.actionParams = {
      commandType: 'self_check',
      protocolType: 'LAN',
      level: 'info',
      ...eventData.action?.params,
    };
    dialog.open({ eventId: eventData.eventId });
  } else {
    resetForm();
    dialog.open();
  }
}

watch(
  () => formData.conditionType,
  (type) => {
    switch (type) {
      case 'manual':
        formData.conditionValue = {};
        break;
      case 'time':
        formData.conditionValue = { time: 10 };
        break;
      case 'message_count':
        formData.conditionValue = { count: 100 };
        break;
      case 'bandwidth_threshold':
        formData.conditionValue = { threshold: 80 };
        break;
    }
  }
);

watch(
  () => formData.actionType,
  (type) => {
    const defaults = {
      send_command: { commandType: 'self_check', protocolType: 'LAN' },
      send_message: { protocolType: 'LAN' },
      inject_fault: { faultType: 'packet_loss' },
      log: { level: 'info' },
      pause: {},
    };
    formData.actionParams = defaults[type] || {};
  }
);

defineExpose({
  open,
});
</script>

<style lang="less" scoped>
@import (reference) '../styles/simulation-dialog-theme.less';

:deep(.el-form) {
  .el-form-item__label {
    color: var(--sim-text-primary, var(--zx-semantic-text-primary));
  }

  .el-input__inner,
  .el-input-number__decrease,
  .el-input-number__increase {
    background: var(--sim-fill-light, var(--zx-semantic-surface-card-fill));
    border-color: var(--sim-border-base, color-mix(in srgb, var(--zx-semantic-border-default) 12%, transparent));
    color: var(--sim-text-primary, var(--zx-semantic-text-primary));
  }

  .el-select .el-input__wrapper {
    background: var(--sim-fill-light, var(--zx-semantic-surface-card-fill));
    border-color: var(--sim-border-base, color-mix(in srgb, var(--zx-semantic-border-default) 12%, transparent));
  }
}

:deep(.el-divider__text) {
  background: var(--sim-bg-main, var(--zx-semantic-surface-canvas-fill));
  color: var(--sim-text-primary, var(--zx-semantic-text-primary));
}
</style>
