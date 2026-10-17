<template>
  <ZxDialog v-bind="dialogProps" v-on="dialogEvents">
    <span v-if="editorQuery.isPaused.value || parentQuery.isPaused.value" aria-live="polite">
      部门读取等待网络连接
    </span>
    <el-alert
      v-if="parentQuery.error.value && !loadError"
      title="上级部门刷新失败，保留当前选项与编辑草稿"
      type="error"
      :closable="false"
    >
      <el-button link type="primary" @click="retryParentOptions">重试读取</el-button>
    </el-alert>
    <el-alert
      v-if="editorQuery.error.value && !loadError"
      title="部门详情刷新失败，保留编辑草稿"
      type="error"
      :closable="false"
    >
      <el-button link type="primary" @click="retryDetail">重试读取</el-button>
    </el-alert>
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
import {
  captureDeptCommand,
  deptCommands,
  deptDetailOptions,
  deptParentOptions,
  readDeptEditor,
} from '@/queries/system/dept';
import { queryScope, requireQueryScope, type QueryScope } from '@/queries/context';
import { useQuery } from '@tanstack/vue-query';
import { handleTree } from '@/utils/ruoyi';
import { FormGrid, useFormDialog } from '@/components/ui/FormDialog';
import { computed, ref, shallowRef, watch } from 'vue';

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

const detailLoading = ref(false);
let requestedData: Partial<DeptForm> | undefined;
const requestedId = ref<number>();
const editorScope = shallowRef<QueryScope | null>(null);

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
      const scope = editorScope.value;
      if (
        !state.visible ||
        !scope ||
        scope !== queryScope.value ||
        detailLoading.value ||
        loadError.value
      )
        return false;
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
        await deptCommands.updateDept(
          captureDeptCommand({ ...payload, deptId: data.deptId }, scope)
        );
      } else {
        if (
          payload.parentId === undefined ||
          payload.deptName === undefined ||
          payload.orderNum === undefined
        )
          return false;
        await deptCommands.createDept(
          captureDeptCommand(
            {
              ...payload,
              parentId: payload.parentId,
              deptName: payload.deptName,
              orderNum: payload.orderNum,
            },
            scope
          )
        );
      }
      if (scope !== queryScope.value || state.data !== data) return false;
      emit('success');
      return true;
    },
  });

const {
  error: loadError,
  run: runRead,
  cancel: cancelRead,
} = useEditorRead(() => state.visible, detailLoading);

const activeScope = computed(() =>
  state.visible && editorScope.value === queryScope.value ? editorScope.value : null
);
const editorQuery = useQuery(() => deptDetailOptions(activeScope.value, requestedId.value));
const parentQuery = useQuery(() => deptParentOptions(activeScope.value, requestedId.value));
const deptOptions = computed(() =>
  handleTree(
    (parentQuery.data.value?.items ?? []).map((row: DeptRecord) => ({
      ...row,
    })),
    'deptId'
  )
);
watch(
  queryScope,
  () => {
    cancelRead();
    editorScope.value = null;
    state.visible = false;
  },
  { flush: 'sync' }
);

function openDialog(seed?: Partial<DeptForm>) {
  const scope = requireQueryScope();
  editorScope.value = scope;
  requestedData = seed ? { ...seed } : undefined;
  requestedId.value = seed?.deptId;
  return runRead(async (read) => {
    open(seed);
    setDisabled(true);
    const response = await readDeptEditor(scope, seed?.deptId, read.signal);
    if (!read.isCurrent() || scope !== queryScope.value) return;
    const data = response.data;
    // Copy the initial detail once; later observer updates only affect choices and status.
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
function retryParentOptions() {
  if (parentQuery.isEnabled.value) void parentQuery.refetch({ cancelRefetch: false });
}
function retryDetail() {
  if (editorQuery.isEnabled.value) void editorQuery.refetch({ cancelRefetch: false });
}

defineExpose({ open: openDialog, close: closeDialog });
</script>
