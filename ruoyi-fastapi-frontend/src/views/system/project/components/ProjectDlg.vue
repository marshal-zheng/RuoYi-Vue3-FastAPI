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
import { ElMessage } from 'element-plus';

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
      ElMessage.success('修改成功');
    } else {
      await addProject(data);
      ElMessage.success('新增成功');
    }
    emit('success');
    return true;
  },
  onConfirmError: (e: any) => {
    ElMessage.error(e?.message || '提交失败，请重试');
  },
});

defineExpose({ open });
</script>
