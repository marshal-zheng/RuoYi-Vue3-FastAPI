<template>
  <ZxDialog v-bind="dialogProps" v-on="dialogEvents">
    <el-form ref="formRef" :model="state.data" :rules="formRules" v-bind="formProps">
      <FormGrid v-bind="layoutProps">
        <template v-if="state.data.parentId !== 0">
          <el-form-item data-form-full label="上级部门" prop="parentId">
            <el-tree-select
              v-model="state.data.parentId"
              :data="deptOptions"
              :props="{ value: 'deptId', label: 'deptName', children: 'children' }"
              value-key="deptId"
              placeholder="选择上级部门"
              check-strictly
            />
          </el-form-item>
        </template>

        <el-form-item label="部门名称" prop="deptName">
          <zx-input v-model="state.data.deptName" placeholder="请输入部门名称" />
        </el-form-item>

        <el-form-item label="显示排序" prop="orderNum">
          <el-input-number v-model="state.data.orderNum" controls-position="right" :min="0" />
        </el-form-item>

        <el-form-item label="负责人" prop="leader">
          <zx-input v-model="state.data.leader" placeholder="请输入负责人" maxlength="20" />
        </el-form-item>

        <el-form-item label="联系电话" prop="phone">
          <zx-input v-model="state.data.phone" placeholder="请输入联系电话" maxlength="11" />
        </el-form-item>

        <el-form-item label="邮箱" prop="email">
          <zx-input v-model="state.data.email" placeholder="请输入邮箱" maxlength="50" />
        </el-form-item>

        <el-form-item label="部门状态">
          <el-radio-group v-model="state.data.status">
            <el-radio v-for="dict in sys_normal_disable" :key="dict.value" :value="dict.value">{{
              dict.label
            }}</el-radio>
          </el-radio-group>
        </el-form-item>
      </FormGrid>
    </el-form>
  </ZxDialog>
</template>

<script setup lang="ts" name="DeptDlg">
import { useDict } from '@/utils/dict';
import type { FormInstance } from 'element-plus';
const formRef = ref<FormInstance>();

import { addDept, updateDept, listDept, listDeptExcludeChild } from '@/api/system/dept';
import { FormGrid, useFormDialog } from '@/components/ui/FormDialog';
import { ref } from 'vue';

const proxy = getCurrentInstance()?.proxy as any;

// 保留异步字典返回的 ref，避免复制请求完成前的空数组。
const { sys_normal_disable: sys_normal_disable } = useDict('sys_normal_disable');

interface DeptForm {
  deptId?: number;
  parentId?: number;
  deptName?: string;
  orderNum?: number;
  leader?: string;
  phone?: string;
  email?: string;
  status?: string;
}

const emit = defineEmits(['success']);

const deptOptions = ref<any[]>([]);

const formRules = {
  parentId: [{ required: true, message: '上级部门不能为空', trigger: 'blur' }],
  deptName: [{ required: true, message: '部门名称不能为空', trigger: 'blur' }],
  orderNum: [{ required: true, message: '显示排序不能为空', trigger: 'blur' }],
  email: [{ type: 'email', message: '请输入正确的邮箱地址', trigger: ['blur', 'change'] }],
  phone: [
    { pattern: /^1[3|4|5|6|7|8|9][0-9]\d{8}$/, message: '请输入正确的手机号码', trigger: 'blur' },
  ],
};

const { formProps, layoutProps, state, dialogProps, dialogEvents, open } = useFormDialog<DeptForm>({
  columns: 2,
  formRef: formRef,
  title: (data: DeptForm) => (data?.deptId ? '修改部门' : '添加部门'),

  defaultData: () => ({
    deptId: undefined,
    parentId: undefined,
    deptName: undefined,
    orderNum: 0,
    leader: undefined,
    phone: undefined,
    email: undefined,
    status: '0',
  }),
  onOpen: async (data: DeptForm) => {
    if (data?.deptId) {
      const response = await listDeptExcludeChild(data.deptId);
      deptOptions.value = proxy.handleTree(response.items, 'deptId');
    } else {
      const response = await listDept();
      deptOptions.value = proxy.handleTree(response.items, 'deptId');
    }
  },
  onConfirm: async (data: DeptForm) => {
    if (data.deptId !== undefined) {
      await updateDept(data);
    } else {
      await addDept(data);
    }
    emit('success');
    return true;
  },
});

defineExpose({ open });
</script>
