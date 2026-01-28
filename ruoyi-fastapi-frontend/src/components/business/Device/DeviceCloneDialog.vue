<template>
  <ZxDialog v-bind="dialog.dialogProps.value" v-on="dialog.dialogEvents.value">
    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="100px"
      label-position="left"
    >
      <el-form-item label="设备名称" prop="deviceName">
        <el-input v-model="formData.deviceName" placeholder="请输入新设备名称" maxlength="100" />
      </el-form-item>
    </el-form>
  </ZxDialog>
</template>

<script setup name="DeviceCloneDialog">
import { ref, reactive, getCurrentInstance } from 'vue';
import { cloneDevice, checkDeviceNameUnique } from '@/api/device/device';
import { useDialog } from '@zxio/zxui';

const { proxy } = getCurrentInstance();

const formRef = ref(null);

const formData = reactive({
  sourceDeviceId: null,
  sourceDeviceName: '',
  deviceName: '',
});

const validateDeviceName = async (rule, value, callback) => {
  if (!value) {
    callback(new Error('请输入设备名称'));
    return;
  }

  const response = await checkDeviceNameUnique(value);
  const isUnique = response?.data ?? response;
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

const dialog = useDialog({
  title: '克隆设备',
  width: '600px',
  okText: '克隆',
  formRef,
  formModel: formData,
  preValidate: true,
  autoResetForm: true,
  async onConfirm() {
    await cloneDevice({
      sourceDeviceId: formData.sourceDeviceId,
      deviceName: formData.deviceName,
    });

    proxy.$modal.msgSuccess('设备克隆成功');

    if (onSuccessCallback) {
      onSuccessCallback();
    }

    return true;
  },
});

const open = (sourceDevice, onSuccess) => {
  formData.sourceDeviceId = sourceDevice.deviceId;
  formData.sourceDeviceName = sourceDevice.deviceName;
  formData.deviceName = `${sourceDevice.deviceName}_副本`;
  onSuccessCallback = onSuccess;
  dialog.open();
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
