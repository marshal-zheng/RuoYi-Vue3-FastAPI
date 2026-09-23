<template>
  <ZxDialog
    v-bind="dialog.dialogProps.value"
    v-on="dialog.dialogEvents.value"
    :confirm="confirmCloneVersion"
    data-testid="version-clone-dialog"
  >
    <el-alert
      v-if="cloneError"
      class="mb-4"
      data-testid="version-clone-error"
      type="error"
      :title="cloneError"
      show-icon
      :closable="false"
    />
    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      v-bind="dialog.formProps"
      label-position="left"
    >
      <FormGrid v-bind="dialog.layoutProps">
        <el-form-item label="版本号" prop="versionNumber">
          <zx-input
            v-model="formData.versionNumber"
            data-testid="version-clone-number"
            aria-label="版本号"
            placeholder="请输入新版本号，如：v1.0.1"
            maxlength="50"
          />
        </el-form-item>
        <el-form-item label="版本名称" prop="versionName">
          <zx-input
            v-model="formData.versionName"
            data-testid="version-clone-name"
            aria-label="版本名称"
            placeholder="请输入新版本名称"
            maxlength="100"
          />
        </el-form-item>
        <el-form-item label="版本描述">
          <zx-input
            v-model="formData.description"
            data-testid="version-clone-desc"
            aria-label="版本描述"
            type="textarea"
            :rows="4"
            placeholder="请输入版本描述"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
      </FormGrid>
    </el-form>
  </ZxDialog>
</template>

<script setup name="VersionCloneDialog">
import { ref, toRef } from 'vue';
import { cloneProjectVersion } from '@/api/project/version';
import { FormGrid, useFormDialog } from '@/components/ui/FormDialog';

const formRef = ref(null);

const rules = {
  versionNumber: [{ required: true, message: '请输入版本号', trigger: 'blur' }],
  versionName: [{ required: true, message: '请输入版本名称', trigger: 'blur' }],
};

const cloneError = ref('');
let onSuccessCallback = null;

function resolveCloneError(error) {
  return error?.problem?.detail || error?.detail || error?.message || '克隆版本失败';
}

async function confirmCloneVersion() {
  cloneError.value = '';
  try {
    await cloneProjectVersion({
      sourceVersionId: formData.value.sourceVersionId,
      versionNumber: formData.value.versionNumber,
      versionName: formData.value.versionName,
      description: formData.value.description,
    });
  } catch (error) {
    cloneError.value = resolveCloneError(error);
    return false;
  }

  if (onSuccessCallback) {
    onSuccessCallback();
  }

  return true;
}

const dialog = useFormDialog({
  columns: 1,
  title: '克隆版本',

  okText: '克隆',
  formRef,
  defaultData: () => ({
    sourceVersionId: null,
    sourceVersionName: '',
    versionNumber: '',
    versionName: '',
    description: '',
  }),
  preValidate: true,
  autoResetForm: true,
  onConfirmError(error) {
    cloneError.value = resolveCloneError(error);
  },
});

const formData = toRef(dialog.state, 'data');

const open = (sourceVersion, onSuccess) => {
  cloneError.value = '';
  onSuccessCallback = onSuccess;
  dialog.open({
    sourceVersionId: sourceVersion.versionId,
    sourceVersionName: sourceVersion.versionName,
    versionNumber: '',
    versionName: `${sourceVersion.versionName}_副本`,
    description: sourceVersion.description,
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

<style scoped>
.mb-4 {
  margin-bottom: 16px;
}
</style>
