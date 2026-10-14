<template>
  <zx-dialog v-bind="dialogProps" :form-ref="formRef" v-on="dialogEvents">
    <el-form ref="formRef" :model="state.data" :rules="rules" v-bind="formProps">
      <FormGrid v-bind="layoutProps">
        <el-form-item label="岗位名称" prop="postName">
          <zx-input v-model="state.data.postName" placeholder="请输入岗位名称" />
        </el-form-item>
        <el-form-item label="岗位编码" prop="postCode">
          <zx-input v-model="state.data.postCode" placeholder="请输入编码名称" />
        </el-form-item>
        <el-form-item label="岗位顺序" prop="postSort">
          <el-input-number v-model="state.data.postSort" controls-position="right" :min="0" />
        </el-form-item>
        <el-form-item label="岗位状态" prop="status">
          <el-radio-group v-model="state.data.status">
            <el-radio v-for="dict in sysNormalDisable" :key="dict.value" :value="dict.value">
              {{ dict.label }}
            </el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="备注" prop="remark">
          <zx-input v-model="state.data.remark" type="textarea" placeholder="请输入内容" />
        </el-form-item>
      </FormGrid>
    </el-form>
  </zx-dialog>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { FormGrid, useFormDialog } from '@/components/ui/FormDialog';
import { addPost, updatePost } from '@/api/system/post';
import { useDict } from '@/utils/dict';

const emit = defineEmits<{
  (e: 'confirm'): void;
}>();

// 保留异步字典返回的 ref，避免复制请求完成前的空数组。
const { sys_normal_disable: sysNormalDisable } = useDict('sys_normal_disable');

interface PostForm {
  postId?: number;
  postName: string;
  postCode: string;
  postSort: number;
  status: '0' | '1';
  remark: string;
}

const formRef = ref();

const rules = {
  postName: [{ required: true, message: '岗位名称不能为空', trigger: 'blur' }],
  postCode: [{ required: true, message: '岗位编码不能为空', trigger: 'blur' }],
  postSort: [{ required: true, message: '岗位顺序不能为空', trigger: 'blur' }],
};

const { formProps, layoutProps, state, dialogProps, dialogEvents, open } = useFormDialog<PostForm>({
  columns: 1,
  formRef: formRef,
  title: (data: PostForm) => (data.postId ? '修改岗位' : '添加岗位'),

  defaultData: () => ({
    postId: undefined,
    postName: '',
    postCode: '',
    postSort: 0,
    status: '0',
    remark: '',
  }),
  onConfirm: async (data: PostForm) => {
    if (data.postId) {
      await updatePost(data);
    } else {
      await addPost(data);
    }
    emit('confirm');
    return true;
  },
});

defineExpose({ open });
</script>
