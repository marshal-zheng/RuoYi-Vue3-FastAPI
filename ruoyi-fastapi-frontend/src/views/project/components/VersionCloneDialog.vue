<template>
  <ZxDialog
    v-bind="dialog.dialogProps.value"
    v-on="dialogEvents"
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
      label-width="100px"
      label-position="left"
    >
      <el-form-item label="版本号" prop="versionNumber">
        <el-input
          v-model="formData.versionNumber"
          data-testid="version-clone-number"
          aria-label="版本号"
          placeholder="请输入新版本号，如：v1.0.1"
          maxlength="50"
        />
      </el-form-item>
      <el-form-item label="版本名称" prop="versionName">
        <el-input
          v-model="formData.versionName"
          data-testid="version-clone-name"
          aria-label="版本名称"
          placeholder="请输入新版本名称"
          maxlength="100"
        />
      </el-form-item>
      <el-form-item label="版本描述">
        <el-input
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
    </el-form>
  </ZxDialog>
</template>

<script setup name="VersionCloneDialog">
import { ref, reactive, computed } from 'vue';
import { cloneProjectVersion } from '@/api/project/version';
import { useDialog } from '@zxio/zxui';

const formRef = ref(null);

const formData = reactive({
  sourceVersionId: null,
  sourceVersionName: '',
  versionNumber: '',
  versionName: '',
  description: '',
});

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
      sourceVersionId: formData.sourceVersionId,
      versionNumber: formData.versionNumber,
      versionName: formData.versionName,
      description: formData.description,
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

const dialog = useDialog({
  title: '克隆版本',
  width: '600px',
  okText: '克隆',
  formRef,
  formModel: formData,
  preValidate: true,
  autoResetForm: true,
  onConfirmError(error) {
    cloneError.value = resolveCloneError(error);
  },
});

const dialogEvents = computed(() => {
  const events = { ...dialog.dialogEvents.value };
  delete events.confirm;
  return events;
});

const open = (sourceVersion, onSuccess) => {
  cloneError.value = '';
  formData.sourceVersionId = sourceVersion.versionId;
  formData.sourceVersionName = sourceVersion.versionName;
  formData.versionNumber = '';
  formData.versionName = `${sourceVersion.versionName}_副本`;
  formData.description = sourceVersion.description;
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

<style scoped lang="less">
.mb-4 {
  margin-bottom: 16px;
}

.p-3 {
  padding: 12px;
}

.bg-gray-50 {
  background-color: #f9fafb;
}

.rounded {
  border-radius: 4px;
}

.text-sm {
  font-size: 14px;
}

.text-gray-600 {
  color: #6b7280;
}

.mb-1 {
  margin-bottom: 4px;
}

.font-medium {
  font-weight: 500;
}
</style>
