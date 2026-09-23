<template>
  <ZxDialog v-bind="dialogProps" v-on="dialogEvents" @close="onDialogClose">
    <el-form ref="portFormRef" :model="state.data" :rules="portFormRules" v-bind="formProps">
      <FormGrid v-bind="layoutProps">
        <el-form-item label="总线类型" prop="interfaceType">
          <InterfaceTypeSelector v-model="state.data.interfaceType" @change="handleBusTypeChange" />
        </el-form-item>
        <el-form-item label="端口位置" prop="position">
          <PositionSelector v-model="state.data.position" multiple @change="handlePositionChange" />
        </el-form-item>
        <el-form-item label="端口描述" prop="description">
          <zx-input
            v-model="state.data.description"
            type="textarea"
            :rows="3"
            placeholder="请输入端口描述"
          />
        </el-form-item>
      </FormGrid>
    </el-form>
  </ZxDialog>
</template>

<script setup name="PortEditDialog">
import { ref, watch } from 'vue';
import { FormGrid, useFormDialog } from '@/components/ui/FormDialog';
import { InterfaceTypeSelector, PositionSelector } from './selector';

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  title: { type: String, default: '添加端口' },
  value: {
    type: Object,
    default: () => ({
      interfaceId: null,
      deviceId: null,
      interfaceName: '',
      interfaceType: 'RS422',
      position: ['right'],
      description: '',
    }),
  },
});

const emit = defineEmits(['update:modelValue', 'submit', 'close']);

const portFormRef = ref();

const portFormRules = {
  interfaceType: [{ required: true, message: '请选择总线类型', trigger: 'change' }],
  position: [
    { required: true, message: '请选择端口位置', trigger: 'change' },
    {
      validator: (rule, value, callback) => {
        if (!Array.isArray(value) || value.length === 0) {
          callback(new Error('请至少选择一个端口位置'));
        } else {
          callback();
        }
      },
      trigger: 'change',
    },
  ],
};

function generatePortName(busType) {
  state.data.interfaceName = busType || '';
}

function handleBusTypeChange(busType) {
  if (!state.data.interfaceId && busType) {
    generatePortName(busType);
  }
}

function handlePositionChange() {}

const { formProps, layoutProps, dialogProps, dialogEvents, open, close, state } = useFormDialog({
  columns: 1,
  title: () => props.title,

  okText: '确定',
  formRef: portFormRef,
  preValidate: true,
  autoScrollToError: true,
  autoResetForm: true,
  defaultData: () => ({ ...props.value }),
  onConfirm: async (data) => {
    const submit = { ...data, interfaceName: data.interfaceType };
    emit('submit', submit);
    emit('update:modelValue', false);
    return submit;
  },
  onConfirmError: () => {},
});

watch(
  () => props.modelValue,
  (v) => {
    if (v) {
      Object.assign(state.data, { ...props.value });
      state.data.interfaceName = state.data.interfaceType;
      open();
    } else {
      close();
    }
  }
);

watch(
  () => props.value,
  (v) => {
    Object.assign(state.data, v || {});
  },
  { deep: true }
);

function onDialogClose() {
  portFormRef.value?.resetFields();
  emit('close');
  emit('update:modelValue', false);
  close();
}

defineExpose({ open, close });
</script>

<style lang="less" scoped></style>
