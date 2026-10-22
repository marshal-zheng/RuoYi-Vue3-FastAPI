<template>
  <zx-dialog v-bind="dialogProps" :form-ref="formRef" v-on="dialogEvents">
    <el-alert v-if="loadError" :title="loadError" type="error" :closable="false" show-icon>
      <el-button link type="primary" @click="handleRetry">重试</el-button>
    </el-alert>
    <el-form
      v-show="!loadError"
      ref="formRef"
      :model="state.data"
      :rules="rules"
      v-bind="formProps"
    >
      <FormGrid v-bind="layoutProps">
        <el-form-item label="字典名称" prop="dictName">
          <zx-input v-model="state.data.dictName" placeholder="请输入字典名称" />
        </el-form-item>
        <el-form-item label="字典类型" prop="dictType">
          <zx-input v-model="state.data.dictType" placeholder="请输入字典类型" />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <DictStatus :types="['sys_normal_disable']" />
          <el-radio-group v-model="state.data.status">
            <el-radio v-for="dict in sysNormalDisable" :key="dict.value" :value="dict.value">
              {{ dict.label }}
            </el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item data-form-full label="备注" prop="remark">
          <RemarkEditor
            v-if="state.visible"
            ref="remarkRef"
            :key="remarkSession"
            v-model="state.data.remark"
          />
        </el-form-item>
      </FormGrid>
    </el-form>
  </zx-dialog>
</template>

<script setup lang="ts">
import RemarkEditor from '@/components/ui/Remark/RemarkEditor.vue';
import { useRemarkField } from '@/components/ui/Remark/useRemarkField';
import { readRemark, type RemarkValue } from '@/components/ui/Remark/contract';
import { ref, watch } from 'vue';
import { ElMessageBox } from 'element-plus';
import { useEditorRead } from '@/utils/editor-read';
import { FormGrid, useFormDialog } from '@/components/ui/FormDialog';
import { getType } from '@/api/system/dict/type';
import { useMutation } from '@tanstack/vue-query';
import { dictCommands, captureDictCommand } from '@/queries/system/dict';
import { queryScope } from '@/queries/context';
import { useDict } from '@/utils/dict';

const emit = defineEmits<{ confirm: [] }>();

// 保留异步字典返回的 ref，避免复制请求完成前的空数组。
const { sys_normal_disable: sysNormalDisable } = useDict('sys_normal_disable');

interface DictForm {
  dictId?: number;
  dictName: string;
  dictType: string;
  status: '0' | '1';
  remark: RemarkValue;
}

const createMutation = useMutation({ mutationFn: dictCommands.createType, retry: false });
const updateMutation = useMutation({ mutationFn: dictCommands.updateType, retry: false });
const formRef = ref();
const { remarkRef, remarkRule } = useRemarkField();
const remarkSession = ref(0);
const detailLoading = ref(false);
let requestedId: number | undefined;
let editorScope = queryScope.value;

const rules = {
  remark: [remarkRule],
  dictName: [{ required: true, message: '字典名称不能为空', trigger: 'blur' }],
  dictType: [{ required: true, message: '字典类型不能为空', trigger: 'blur' }],
};

const { formProps, layoutProps, state, isDirty, dialogProps, dialogEvents, open, setDisabled } =
  useFormDialog<DictForm>({
    columns: 1,
    onBeforeClose: canDiscard,
    loading: detailLoading,
    formRef: formRef,
    title: (data: DictForm) => (data.dictId ? '修改字典类型' : '添加字典类型'),

    defaultData: () => ({
      dictId: undefined,
      dictName: '',
      dictType: '',
      status: '0',
      remark: null as RemarkValue,
    }),
    onConfirm: async (data: DictForm) => {
      if (detailLoading.value || loadError.value || editorScope !== queryScope.value) return false;
      const scope = queryScope.value;
      if (data.dictId) {
        await updateMutation.mutateAsync(captureDictCommand(data));
      } else {
        await createMutation.mutateAsync(captureDictCommand(data));
      }
      if (scope !== queryScope.value) return false;
      emit('confirm');
      return true;
    },
  });

const {
  error: loadError,
  run: runRead,
  cancel: cancelRead,
} = useEditorRead(() => state.visible, detailLoading);

let opening = 0;
let discardPending: Promise<boolean> | undefined;
function canDiscard(): Promise<boolean> {
  if (state.loading) return Promise.resolve(false);
  if (!isDirty.value && remarkRef.value?.validate() !== false) return Promise.resolve(true);
  if (discardPending) return discardPending;
  const data = state.data;
  const decision = ElMessageBox.confirm('字典类型尚未保存，是否放弃本次修改？', '未保存的修改', {
    confirmButtonText: '放弃修改',
    cancelButtonText: '继续编辑',
    type: 'warning',
  })
    .then(() => data === state.data && !state.loading)
    .catch(() => false)
    .finally(() => {
      if (discardPending === decision) discardPending = undefined;
    });
  discardPending = decision;
  return decision;
}
async function openDialog(id?: number) {
  const intent = ++opening;
  if (state.visible && !(await canDiscard())) return;
  if (intent !== opening) return;
  remarkSession.value++;
  editorScope = queryScope.value;
  requestedId = id;
  return runRead(async (read) => {
    open(id ? { dictId: id } : undefined);
    setDisabled(true);
    if (!id) {
      setDisabled(false);
      return;
    }
    const data = await getType(id, { signal: read.signal, silentError: true });
    if (!read.isCurrent()) return;
    open({
      dictId: data.dictId ?? undefined,
      dictName: data.dictName ?? '',
      dictType: data.dictType ?? '',
      status: data.status ?? '0',
      remark: readRemark(data.remark),
    });
    setDisabled(false);
  });
}
async function closeDialog() {
  opening++;
  if (!(await canDiscard())) return;
  cancelRead();
  state.visible = false;
}
function handleRetry() {
  return openDialog(requestedId).catch(() => {
    /* 当前读取已负责反馈。 */
  });
}

watch(
  queryScope,
  () => {
    opening++;
    cancelRead();
    state.visible = false;
  },
  { flush: 'sync' }
);

defineExpose({ open: openDialog, close: closeDialog });
watch(
  () => state.visible,
  (visible) => {
    if (visible) remarkSession.value++;
  }
);
</script>
