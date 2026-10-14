<template>
  <zx-dialog v-bind="dialogProps" :form-ref="formRef" v-on="dialogEvents">
    <el-form ref="formRef" :model="state.data" :rules="rules" v-bind="formProps">
      <FormGrid v-bind="layoutProps">
        <el-form-item label="字典名称" prop="dictName">
          <zx-input v-model="state.data.dictName" placeholder="请输入字典名称" />
        </el-form-item>
        <el-form-item label="字典类型" prop="dictType">
          <zx-input v-model="state.data.dictType" placeholder="请输入字典类型" />
        </el-form-item>
        <el-form-item label="状态" prop="status">
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
import { addType, updateType } from '@/api/system/dict/type';
import { useDict } from '@/utils/dict';

// 保留异步字典返回的 ref，避免复制请求完成前的空数组。
const { sys_normal_disable: sysNormalDisable } = useDict('sys_normal_disable');

interface DictForm {
  dictId?: number;
  dictName: string;
  dictType: string;
  status: '0' | '1';
  remark: string;
}

const formRef = ref();

const rules = {
  dictName: [{ required: true, message: '字典名称不能为空', trigger: 'blur' }],
  dictType: [{ required: true, message: '字典类型不能为空', trigger: 'blur' }],
};

const { formProps, layoutProps, state, dialogProps, dialogEvents, open } = useFormDialog<DictForm>({
  columns: 1,
  formRef: formRef,
  title: (data: DictForm) => (data.dictId ? '修改字典类型' : '添加字典类型'),

  defaultData: () => ({
    dictId: undefined,
    dictName: '',
    dictType: '',
    status: '0',
    remark: '',
  }),
  onConfirm: async (data: DictForm) => {
    if (data.dictId) {
      await updateType(data);
    } else {
      await addType(data);
    }
    return true;
  },
});

defineExpose({ open });
</script>
