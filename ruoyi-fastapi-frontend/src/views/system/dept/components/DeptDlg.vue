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
        <template v-if="state.data.parentId !== 0">
          <el-form-item data-form-full label="上级部门" prop="parentId">
            <el-tree-select
              v-model="state.data.parentId"
              :data="deptOptions"
              :props="{
                value: 'deptId',
                label: 'deptName',
                children: 'children',
              }"
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
          <DictStatus :types="['sys_normal_disable']" />
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
import { useEditorRead } from '@/utils/editor-read';
import { useDict } from '@/utils/dict';
import type { FormInstance } from 'element-plus';
const formRef = ref<FormInstance>();

import type { DeptRecord } from '@/api/system/dept';
import { getDept, addDept, updateDept, listDept, listDeptExcludeChild } from '@/api/system/dept';
import { FormGrid, useFormDialog } from '@/components/ui/FormDialog';
import { ref, getCurrentInstance } from 'vue';

const proxy = getCurrentInstance()!.proxy!;

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
  status?: '0' | '1';
}

const emit = defineEmits(['success']);

const deptOptions = ref<DeptRecord[]>([]);
const detailLoading = ref(false);
let requestedData: Partial<DeptForm> | undefined;

const formRules = {
  parentId: [{ required: true, message: '上级部门不能为空', trigger: 'blur' }],
  deptName: [{ required: true, message: '部门名称不能为空', trigger: 'blur' }],
  orderNum: [{ required: true, message: '显示排序不能为空', trigger: 'blur' }],
  email: [
    {
      type: 'email',
      message: '请输入正确的邮箱地址',
      trigger: ['blur', 'change'],
    },
  ],
  phone: [
    {
      pattern: /^1[3|4|5|6|7|8|9][0-9]\d{8}$/,
      message: '请输入正确的手机号码',
      trigger: 'blur',
    },
  ],
};

const { formProps, layoutProps, state, dialogProps, dialogEvents, open, close, setDisabled } =
  useFormDialog<DeptForm>({
    columns: 2,
    loading: detailLoading,
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
    onConfirm: async (data: DeptForm) => {
      if (detailLoading.value || loadError.value) return false;
      const payload = {
        parentId: data.parentId,
        deptName: data.deptName,
        orderNum: data.orderNum,
        leader: data.leader,
        phone: data.phone,
        email: data.email,
        status: data.status,
      };
      if (data.deptId !== undefined) {
        await updateDept({ ...payload, deptId: data.deptId });
      } else {
        if (
          payload.parentId === undefined ||
          payload.deptName === undefined ||
          payload.orderNum === undefined
        )
          return false;
        await addDept({
          ...payload,
          parentId: payload.parentId,
          deptName: payload.deptName,
          orderNum: payload.orderNum,
        });
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

function openDialog(seed?: Partial<DeptForm>) {
  requestedData = seed ? { ...seed } : undefined;
  return runRead(async (read) => {
    open(seed);
    deptOptions.value = [];
    setDisabled(true);
    const config = { signal: read.signal, silentError: true };
    const [data, options] = seed?.deptId
      ? await Promise.all([getDept(seed.deptId, config), listDeptExcludeChild(seed.deptId, config)])
      : [seed, await listDept(undefined, config)];
    if (!read.isCurrent()) return;
    deptOptions.value = proxy.handleTree(options.items, 'deptId');
    open(
      seed?.deptId && data
        ? {
            deptId: data.deptId ?? undefined,
            parentId: data.parentId ?? undefined,
            deptName: data.deptName ?? undefined,
            orderNum: data.orderNum ?? undefined,
            leader: data.leader ?? undefined,
            phone: data.phone ?? undefined,
            email: data.email ?? undefined,
            status: data.status ?? undefined,
          }
        : seed
    );
    setDisabled(false);
  });
}
function closeDialog() {
  cancelRead();
  return close();
}
function handleRetry() {
  return openDialog(requestedData).catch(() => {
    /* 当前读取已负责反馈。 */
  });
}

defineExpose({ open: openDialog, close: closeDialog });
</script>
