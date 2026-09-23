<template>
  <zx-dialog v-bind="dialogProps" :form-ref="formRef" v-on="dialogEvents">
    <el-form ref="formRef" :model="state.data" :rules="rules" v-bind="formProps">
      <FormGrid v-bind="layoutProps">
        <el-form-item label="参数名称" prop="configName">
          <zx-input v-model="state.data.configName" placeholder="请输入参数名称" />
        </el-form-item>
        <el-form-item label="参数键名" prop="configKey">
          <zx-input v-model="state.data.configKey" placeholder="请输入参数键名" />
        </el-form-item>
        <el-form-item label="参数键值" prop="configValue">
          <zx-input v-model="state.data.configValue" type="textarea" placeholder="请输入参数键值" />
        </el-form-item>
        <el-form-item label="系统内置" prop="configType">
          <el-radio-group v-model="state.data.configType">
            <el-radio v-for="dict in sysYesNo" :key="dict.value" :value="dict.value">
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
import { addConfig, updateConfig } from '@/api/system/config';
import { useDict } from '@/utils/dict';

const emit = defineEmits<{ confirm: [] }>();

// 保留异步字典返回的 ref，避免复制请求完成前的空数组。
const { sys_yes_no: sysYesNo } = useDict('sys_yes_no');

interface ConfigForm {
  configId?: number;
  configName: string;
  configKey: string;
  configValue: string;
  configType: string;
  remark: string;
}

const formRef = ref();

const rules = {
  configName: [{ required: true, message: '参数名称不能为空', trigger: 'blur' }],
  configKey: [{ required: true, message: '参数键名不能为空', trigger: 'blur' }],
  configValue: [{ required: true, message: '参数键值不能为空', trigger: 'blur' }],
};

const { formProps, layoutProps, state, dialogProps, dialogEvents, open } =
  useFormDialog<ConfigForm>({
    columns: 1,
    formRef: formRef,
    title: (data: ConfigForm) => (data.configId ? '修改参数配置' : '添加参数配置'),
    defaultData: () => ({
      configId: undefined,
      configName: '',
      configKey: '',
      configValue: '',
      configType: 'Y',
      remark: '',
    }),
    onConfirm: async (data: ConfigForm) => {
      if (data.configId) {
        await updateConfig(data);
      } else {
        await addConfig(data);
      }
      emit('confirm');
      return true;
    },
  });

defineExpose({ open });
</script>
