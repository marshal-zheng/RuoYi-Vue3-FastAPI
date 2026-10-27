<template>
  <el-form ref="basicInfoForm" :model="info" :rules="rules" v-bind="formProps">
    <FormGrid v-bind="layoutProps">
      <el-form-item label="表名称" prop="tableName"
        ><zx-input v-model="info.tableName" placeholder="请输入表名称"
      /></el-form-item>
      <el-form-item label="表描述" prop="tableComment"
        ><zx-input v-model="info.tableComment" placeholder="请输入表描述"
      /></el-form-item>
      <el-form-item label="实体类名称" prop="className"
        ><zx-input v-model="info.className" placeholder="请输入实体类名称"
      /></el-form-item>
      <el-form-item label="作者" prop="functionAuthor"
        ><zx-input v-model="info.functionAuthor" placeholder="请输入作者"
      /></el-form-item>
      <el-form-item data-form-full label="备注" prop="remark"
        ><RemarkEditor
          ref="remarkRef"
          :key="aiInstance"
          v-model="info.remark"
          @edit-state="remarkEditState = $event"
      /></el-form-item>
    </FormGrid>
  </el-form>
</template>
<script setup>
import { useAIContextHost } from '@/ai-context/host';
import { computed, ref, watch } from 'vue';
import { FormGrid, useFormDialog } from '@/components/ui/FormDialog';
import RemarkEditor from '@/components/ui/Remark/RemarkEditor.vue';
import { useRemarkField } from '@/components/ui/Remark/useRemarkField';
const props = defineProps({ info: { type: Object, required: true } });
const basicInfoForm = ref();
const remarkEditState = ref({ pending: false, blocking: [] });
const { remarkRef, remarkRule } = useRemarkField();
const { formProps, layoutProps } = useFormDialog({
  columns: 2,
  formRef: basicInfoForm,
});
const rules = {
  remark: [remarkRule],
  tableName: [{ required: true, message: '请输入表名称', trigger: 'blur' }],
  tableComment: [{ required: true, message: '请输入表描述', trigger: 'blur' }],
  className: [{ required: true, message: '请输入实体类名称', trigger: 'blur' }],
  functionAuthor: [{ required: true, message: '请输入作者', trigger: 'blur' }],
};
defineExpose({
  basicInfoForm,
  hasPendingEdit: computed(
    () => remarkEditState.value.pending || remarkEditState.value.blocking.length > 0
  ),
});

const aiInstance = ref(0);
watch(
  () => props.info,
  () => {
    aiInstance.value++;
  },
  { flush: 'sync' }
);
useAIContextHost('genTable', {
  instanceKey: () => aiInstance.value,
  revisionSource: () => props.info,
  bindings: {
    tableName: { value: () => props.info.tableName },
    tableComment: { value: () => props.info.tableComment },
    className: { value: () => props.info.className },
    functionAuthor: { value: () => props.info.functionAuthor },
  },
});
</script>
