<template>
  <ZxDialog v-bind="dialogProps" v-on="dialogEvents">
    <el-form ref="formRef" :model="state.data" :rules="formRules" v-bind="formProps">
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

import { addProject, updateProject } from '@/api/system/project';
import { FormGrid, useFormDialog } from '@/components/ui/FormDialog';

interface ProjectForm {
  projectId?: number;
  projectDesc?: string;
}

const emit = defineEmits(['success']);

const formRules = {
  projectDesc: [{ required: false, message: '工程描述不能为空', trigger: 'blur' }],
};

const { formProps, layoutProps, state, dialogProps, dialogEvents, open } =
  useFormDialog<ProjectForm>({
    columns: 1,
    formRef: formRef,
    title: (data: ProjectForm) => (data?.projectId ? '修改工程' : '添加工程'),

    defaultData: () => ({
      projectId: undefined,
      projectDesc: undefined,
    }),
    onConfirm: async (data: ProjectForm) => {
      if (data.projectId !== undefined) {
        await updateProject(data);
      } else {
        await addProject(data);
      }
      emit('success');
      return true;
    },
  });

defineExpose({ open });
</script>
