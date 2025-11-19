<template>
  <ZxDialog v-bind="dialogProps" v-on="dialogEvents" @close="onDialogClose">
    <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
      <el-form-item label="设备名称" prop="deviceName">
        <el-input v-model="form.deviceName" placeholder="请输入设备名称" />
      </el-form-item>
      <el-form-item label="设备分类" prop="categoryName">
        <CategorySelector v-model="form.categoryName" placeholder="请选择设备分类" />
      </el-form-item>
      <el-form-item label="设备描述" prop="remark">
        <el-input v-model="form.remark" type="textarea" :rows="3" placeholder="请输入设备描述" />
      </el-form-item>
    </el-form>
  </ZxDialog>
</template>

<script setup name="DeviceNameDialog">
import { ref, watch, toRef } from 'vue';
import { useDialog } from '@zxio/zxui';
import { CategorySelector } from './selector';

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  value: {
    type: Object,
    default: () => ({ deviceName: '', categoryName: '', remark: '' }),
  },
  isCreate: { type: Boolean, default: false },
});

const emit = defineEmits(['update:modelValue', 'submit', 'close']);

const formRef = ref();

const getDefaultForm = () => ({
  deviceName: '',
  categoryName: '',
  remark: '',
});

const rules = {
  deviceName: [{ required: true, message: '请输入设备名称', trigger: 'blur' }],
  categoryName: [{ required: true, message: '请选择设备分类', trigger: 'change' }],
};

const { dialogProps, dialogEvents, open, close, state } = useDialog({
  title: props.isCreate ? '新增设备' : '编辑设备信息',
  okText: '下一步',
  formRef,
  preValidate: true,
  autoScrollToError: true,
  autoResetForm: true,
  defaultData: getDefaultForm,
  onConfirm: async (data) => {
    emit('submit', { ...data });
    emit('update:modelValue', false);
    return data;
  },
  onConfirmError: (_e) => {},
});

const form = toRef(state, 'data');

function formatFormValue(value) {
  return {
    ...getDefaultForm(),
    ...(value || {}),
  };
}

watch(
  () => props.modelValue,
  (visible) => {
    if (visible) {
      open(formatFormValue(props.value));
    } else {
      close();
    }
  }
);

watch(
  () => props.value,
  (value) => {
    if (props.modelValue) {
      Object.assign(form.value, formatFormValue(value));
    }
  },
  { deep: true }
);

function onDialogClose() {
  formRef.value?.resetFields();
  emit('close');
  emit('update:modelValue', false);
  close();
}
</script>

<style lang="less" scoped></style>
