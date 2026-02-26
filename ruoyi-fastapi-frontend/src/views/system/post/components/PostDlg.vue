<template>
  <zx-dialog v-bind="dialogProps" :form-ref="formRef" v-on="dialogEvents">
    <el-form ref="formRef" :model="state.data" :rules="rules" label-width="80px">
      <el-form-item label="岗位名称" prop="postName">
        <el-input v-model="state.data.postName" placeholder="请输入岗位名称" />
      </el-form-item>
      <el-form-item label="岗位编码" prop="postCode">
        <el-input v-model="state.data.postCode" placeholder="请输入编码名称" />
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
        <el-input v-model="state.data.remark" type="textarea" placeholder="请输入内容" />
      </el-form-item>
    </el-form>
  </zx-dialog>
</template>

<script setup lang="ts">
import { ref, getCurrentInstance } from 'vue';
import { useDialog } from '@zxio/zxui';
import { addPost, updatePost } from '@/api/system/post';
import { useDict } from '@/utils/dict';

const emit = defineEmits<{
  (e: 'confirm'): void;
}>();

const { proxy } = getCurrentInstance() as any;

// 延迟加载字典数据
const sysNormalDisable = ref<any[]>([]);
let dictLoaded = false;

interface PostForm {
  postId?: number;
  postName: string;
  postCode: string;
  postSort: number;
  status: string;
  remark: string;
}

const formRef = ref();

const rules = {
  postName: [{ required: true, message: '岗位名称不能为空', trigger: 'blur' }],
  postCode: [{ required: true, message: '岗位编码不能为空', trigger: 'blur' }],
  postSort: [{ required: true, message: '岗位顺序不能为空', trigger: 'blur' }],
};

const { state, dialogProps, dialogEvents, open } = useDialog<PostForm>({
  title: (data: PostForm) => (data.postId ? '修改岗位' : '添加岗位'),
  width: '500px',
  defaultData: () => ({
    postId: undefined,
    postName: '',
    postCode: '',
    postSort: 0,
    status: '0',
    remark: '',
  }),
  onOpen: () => {
    // 只在第一次打开时加载字典
    if (!dictLoaded) {
      const dict = useDict('sys_normal_disable');
      sysNormalDisable.value = dict.sys_normal_disable?.value || [];
      dictLoaded = true;
    }
  },
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
