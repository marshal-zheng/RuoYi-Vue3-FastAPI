<template>
  <ZxDialog v-bind="dialog.dialogProps.value" v-on="dialog.dialogEvents.value">
    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      v-bind="dialog.formProps"
      label-position="left"
    >
      <FormGrid v-bind="dialog.layoutProps">
        <el-form-item label="设备名称" prop="deviceName">
          <zx-input v-model="formData.deviceName" placeholder="请输入新设备名称" maxlength="100" />
        </el-form-item>
      </FormGrid>
    </el-form>
  </ZxDialog>
</template>

<script setup name="DeviceCloneDialog">
import { ref, toRef } from 'vue';
import { cloneDevice, checkDeviceNameUnique } from '@/api/device/device';
import { FormGrid, useFormDialog } from '@/components/ui/FormDialog';

const formRef = ref(null);

const validateDeviceName = async (rule, value, callback) => {
  if (!value) {
    callback(new Error('请输入设备名称'));
    return;
  }

  const response = await checkDeviceNameUnique(value);
  const isUnique = response;
  if (isUnique === false) {
    callback(new Error('设备名称已存在'));
  } else {
    callback();
  }
};

const rules = {
  deviceName: [
    { required: true, message: '请输入设备名称', trigger: 'blur' },
    { validator: validateDeviceName, trigger: 'blur' },
  ],
};

let onSuccessCallback = null;

const dialog = useFormDialog({
  columns: 1,
  title: '克隆设备',

  okText: '克隆',
  formRef,
  defaultData: () => ({
    sourceDeviceId: null,
    sourceDeviceName: '',
    deviceName: '',
  }),
  preValidate: true,
  autoResetForm: true,
  async onConfirm() {
    await cloneDevice({
      sourceDeviceId: formData.value.sourceDeviceId,
      deviceName: formData.value.deviceName,
    });

    if (onSuccessCallback) {
      onSuccessCallback();
    }

    return true;
  },
});

const formData = toRef(dialog.state, 'data');

const open = (sourceDevice, onSuccess) => {
  onSuccessCallback = onSuccess;
  dialog.open({
    sourceDeviceId: sourceDevice.deviceId,
    sourceDeviceName: sourceDevice.deviceName,
    deviceName: `${sourceDevice.deviceName}_副本`,
  });
};

const close = () => {
  dialog.close();
};

defineExpose({
  open,
  close,
});
</script>

<style scoped lang="less"></style>
