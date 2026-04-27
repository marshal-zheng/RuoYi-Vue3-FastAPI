<template>
  <ZxDialog v-bind="dialogProps" v-on="dialogEvents">
    <el-form :model="state.data" :rules="formRules" label-width="80px">
      <el-form-item label="工程描述" prop="projectDesc">
        <el-input
          v-model="state.data.projectDesc"
          type="textarea"
          :rows="4"
          placeholder="请输入工程描述"
        />
      </el-form-item>
    </el-form>
  </ZxDialog>
</template>

<script setup lang="ts" name="ProjectDlg">
import { addProject, updateProject } from '@/api/system/project';
import { useDialog } from '@zxio/zxui';

interface ProjectForm {
  projectId?: number;
  projectDesc?: string;
}

const emit = defineEmits(['success']);

const formRules = {
  projectDesc: [{ required: false, message: '工程描述不能为空', trigger: 'blur' }],
};

const { state, dialogProps, dialogEvents, open } = useDialog<ProjectForm>({
  title: (data: ProjectForm) => (data?.projectId ? '修改工程' : '添加工程'),
  width: '600px',
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
