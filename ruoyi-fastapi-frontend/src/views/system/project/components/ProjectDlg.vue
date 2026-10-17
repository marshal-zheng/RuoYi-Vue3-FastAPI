<template>
  <ZxDialog v-bind="dialogProps" v-on="dialogEvents">
    <el-alert v-if="loadError" :title="loadError" type="error" :closable="false" show-icon>
      <el-button link type="primary" @click="handleRetry">重试</el-button>
    </el-alert>
    <el-form
      v-show="!loadError"
      ref="formRef"
      :model="state.data"
      :rules="formRules"
      v-bind="formProps"
    >
      <FormGrid v-bind="layoutProps">
        <el-form-item label="工程描述" prop="projectDesc">
          <zx-input
            v-model="state.data.projectDesc"
            type="textarea"
            :rows="4"
            placeholder="请输入工程描述"
          />
        </el-form-item>
      </FormGrid>
    </el-form>
  </ZxDialog>
</template>

<script setup lang="ts" name="ProjectDlg">
import { ref } from 'vue';

import type { FormInstance } from 'element-plus';
const formRef = ref<FormInstance>();

import { getProject, addProject, updateProject } from '@/api/system/project';
import { useEditorRead } from '@/utils/editor-read';
import { FormGrid, useFormDialog } from '@/components/ui/FormDialog';

interface ProjectForm {
  projectId?: number;
  projectDesc?: string;
}

const detailLoading = ref(false);
let requestedId: number | undefined;

const emit = defineEmits(['success']);

const formRules = {
  projectDesc: [{ required: false, message: '工程描述不能为空', trigger: 'blur' }],
};

const { formProps, layoutProps, state, dialogProps, dialogEvents, open, close, setDisabled } =
  useFormDialog<ProjectForm>({
    loading: detailLoading,
    columns: 1,
    formRef: formRef,
    title: (data: ProjectForm) => (data?.projectId ? '修改工程' : '添加工程'),

    defaultData: () => ({
      projectId: undefined,
      projectDesc: undefined,
    }),
    onConfirm: async (data: ProjectForm) => {
      if (detailLoading.value || loadError.value || data.projectId !== requestedId) return false;
      if (data.projectId !== undefined) {
        await updateProject(data);
      } else {
        await addProject(data);
      }
      emit('success');
      return true;
    },
  });

const {
  error: loadError,
  run: runRead,
  cancel: cancelRead,
} = useEditorRead(() => state.visible, detailLoading);

function openDialog(id?: number) {
  requestedId = id;
  return runRead(async (read) => {
    open(id ? { projectId: id } : undefined);
    setDisabled(true);
    if (!id) {
      setDisabled(false);
      return;
    }
    const data = await getProject(id, { signal: read.signal, silentError: true });
    if (!read.isCurrent()) return;
    open({
      projectId: data.projectId ?? undefined,
      projectDesc: data.projectDesc ?? undefined,
    });
    setDisabled(false);
  });
}
function closeDialog() {
  cancelRead();
  return close();
}
function handleRetry() {
  return openDialog(requestedId).catch(() => {
    /* 当前读取已负责反馈。 */
  });
}

defineExpose({ open: openDialog, close: closeDialog });
</script>
