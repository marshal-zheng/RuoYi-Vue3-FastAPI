<template>
  <ZxDialog v-bind="dialogProps" v-on="dialogEvents">
    <span v-if="editorQuery.paused.value || parentQuery.paused.value" aria-live="polite">
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
    <el-alert v-if="saveError" :title="saveError" type="error" :closable="false" />
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
import { computed, onScopeDispose, ref, shallowRef, watch } from 'vue';
import { ElMessage, type FormInstance } from 'element-plus';
import { AbortError } from '@zxio/http';
import { useResourceQuery } from '@zxio/vue-query/resources';
import { useResourceCommand, useResourceDetail } from '@zxio/vue-query/ui';
import { useDict } from '@/utils/dict';
import { dataClient } from '@/queries/client';
import { departmentResource, departmentDraft } from '@/queries/system/dept';
import { queryScope, requireQueryScope, type QueryScope } from '@/queries/context';
import { handleTree } from '@/utils/ruoyi';
import { FormGrid, useFormDialog } from '@/components/ui/FormDialog';

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
const formRef = ref<FormInstance>();
const { sys_normal_disable } = useDict('sys_normal_disable');
const emit = defineEmits(['success']);
const detailLoading = ref(false);
const loadError = ref('');
const saveError = ref('');
const uncertain = ref(false);
const requestedId = ref<number>();
const editorScope = shallowRef<QueryScope | null>(null);
let requestedData: Partial<DeptForm> | undefined;
let opening: AbortController | undefined;
let snapshotCurrent: () => boolean = () => false;
const detail = useResourceDetail(departmentResource, 'detail', {
  client: dataClient,
  snapshot: departmentDraft,
});
const createCommand = useResourceCommand(departmentResource, 'create', {
  client: dataClient,
});
const updateCommand = useResourceCommand(departmentResource, 'update', {
  client: dataClient,
});
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
      pattern: /^1[3-9][0-9]\d{8}$/,
      message: '请输入正确的手机号码',
      trigger: 'blur',
    },
  ],
};
const { formProps, layoutProps, state, dialogProps, dialogEvents, open, close, setDisabled } =
  useFormDialog<DeptForm>({
    columns: 2,
    loading: detailLoading,
    formRef,
    title: (data) => (data?.deptId ? '修改部门' : '添加部门'),
    defaultData: () => ({ orderNum: 0, status: '0' }),
    onConfirm: async (data) => {
      if (
        !state.visible ||
        !snapshotCurrent() ||
        detailLoading.value ||
        loadError.value ||
        uncertain.value
      )
        return false;
      const scope = editorScope.value;
      const current = () =>
        state.visible && state.data === data && scope === queryScope.value && snapshotCurrent();
      const payload = {
        parentId: data.parentId,
        deptName: data.deptName,
        orderNum: data.orderNum,
        leader: data.leader,
        phone: data.phone,
        email: data.email,
        status: data.status,
      };
      saveError.value = '';
      const receipt =
        data.deptId !== undefined
          ? await updateCommand.run({ ...payload, deptId: data.deptId })
          : payload.parentId !== undefined &&
              payload.deptName !== undefined &&
              payload.orderNum !== undefined
            ? await createCommand.run({
                ...payload,
                parentId: payload.parentId,
                deptName: payload.deptName,
                orderNum: payload.orderNum,
              })
            : null;
      if (!current() || !receipt?.applicable) return false;
      if (receipt.kind !== 'succeeded') {
        uncertain.value = receipt.kind === 'unknown';
        saveError.value =
          receipt.kind === 'unknown'
            ? '保存结果未确认，请关闭后重新打开核对，勿重复提交。'
            : receipt.kind === 'rejected' && receipt.error instanceof Error
              ? receipt.error.message
              : '当前条件下未提交保存，请重试。';
        if (uncertain.value) setDisabled(true);
        return false;
      }
      // Refresh is a separate receipt: its failure must never turn a confirmed save into a retryable write.
      const refresh = await receipt.refresh;
      if (!current()) return false;
      if (refresh.kind === 'failed' || refresh.kind === 'paused')
        ElMessage.warning('保存已成功，部分数据未刷新，请在提示处重试读取。');
      else ElMessage.success('保存成功');
      emit('success');
      return true;
    },
  });
const active = () => state.visible && editorScope.value === queryScope.value;
const editorQuery = useResourceQuery(departmentResource, 'detail', requestedId, {
  client: dataClient,
  active: () => active() && requestedId.value !== undefined,
});
const createParents = useResourceQuery(
  departmentResource,
  'list',
  {},
  {
    client: dataClient,
    active: () => active() && requestedId.value === undefined,
  }
);
const editParents = useResourceQuery(departmentResource, 'excludeChild', requestedId, {
  client: dataClient,
  active: () => active() && requestedId.value !== undefined,
});
const parentQuery = computed(() => (requestedId.value === undefined ? createParents : editParents));
const deptOptions = computed(() =>
  handleTree(
    (parentQuery.value.data.value?.items ?? []).map((row) => ({ ...row })),
    'deptId'
  )
);
function cancelOpening() {
  opening?.abort();
  opening = undefined;
  detail.close();
  snapshotCurrent = () => false;
  detailLoading.value = false;
}
onScopeDispose(cancelOpening);
watch(
  () => state.visible,
  (visible) => {
    if (!visible) cancelOpening();
  },
  { flush: 'sync' }
);
watch(
  queryScope,
  () => {
    cancelOpening();
    editorScope.value = null;
    state.visible = false;
  },
  { flush: 'sync' }
);
async function openDialog(seed?: Partial<DeptForm>) {
  const scope = requireQueryScope();
  cancelOpening();
  const abort = new AbortController();
  opening = abort;
  editorScope.value = scope;
  requestedData = seed ? { ...seed } : undefined;
  requestedId.value = seed?.deptId;
  loadError.value = '';
  saveError.value = '';
  uncertain.value = false;
  open(seed);
  const model = state.data;
  const current = () =>
    !abort.signal.aborted && state.visible && state.data === model && scope === queryScope.value;
  setDisabled(true);
  detailLoading.value = true;
  try {
    const [loaded, parents] = await Promise.all([
      seed?.deptId !== undefined
        ? detail.loadSnapshot(seed.deptId)
        : Promise.resolve({
            kind: 'loaded' as const,
            draft: seed ?? {},
            isCurrent: current,
          }),
      seed?.deptId !== undefined
        ? dataClient.read(departmentResource, 'excludeChild', seed.deptId, {
            signal: abort.signal,
          })
        : dataClient.read(departmentResource, 'list', {}, { signal: abort.signal }),
    ]);
    if (!current()) throw new AbortError({ message: '编辑读取已结束' });
    for (const result of [loaded, parents]) {
      if (result.kind === 'failed') throw result.error;
      if (result.kind !== 'loaded')
        throw new Error(
          result.kind === 'paused' ? '部门读取等待网络连接，请重试' : '部门读取已中断，请重试'
        );
    }
    if (loaded.kind !== 'loaded') return;
    Object.assign(model, loaded.draft);
    snapshotCurrent = () => current() && loaded.isCurrent();
    setDisabled(false);
  } catch (error) {
    if (current())
      loadError.value = error instanceof Error ? error.message : '部门读取失败，请重试';
    throw error;
  } finally {
    if (current()) detailLoading.value = false;
  }
}
function closeDialog() {
  cancelOpening();
  return close();
}
function handleRetry() {
  return openDialog(requestedData).catch(() => {});
}
function retryParentOptions() {
  void parentQuery.value.refresh();
}
function retryDetail() {
  void editorQuery.refresh();
}
defineExpose({ open: openDialog, close: closeDialog });
</script>
