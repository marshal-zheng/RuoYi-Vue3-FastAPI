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
          <DictStatus :types="['sys_yes_no']" />
          <el-radio-group v-model="state.data.configType">
            <el-radio v-for="dict in sysYesNo" :key="dict.value" :value="dict.value">
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
import { useAIContextHost } from '@/ai-context/host';
import RemarkEditor from '@/components/ui/Remark/RemarkEditor.vue';
import { useRemarkField } from '@/components/ui/Remark/useRemarkField';
import { readRemark, type RemarkValue } from '@/components/ui/Remark/contract';
import { ref, watch } from 'vue';
import { ElMessageBox } from 'element-plus';
import { useEditorRead } from '@/utils/editor-read';
import { FormGrid, useFormDialog } from '@/components/ui/FormDialog';
import { getConfig, addConfig, updateConfig } from '@/api/system/config';
import { useDict } from '@/utils/dict';

const emit = defineEmits<{ confirm: [] }>();

// 保留异步字典返回的 ref，避免复制请求完成前的空数组。
const { sys_yes_no: sysYesNo } = useDict('sys_yes_no');

interface ConfigForm {
  configId?: number;
  configName: string;
  configKey: string;
  configValue: string;
  configType: 'Y' | 'N';
  remark: RemarkValue;
}

const formRef = ref();
const { remarkRef, remarkRule } = useRemarkField();
const remarkSession = ref(0);
const detailLoading = ref(false);
let requestedId: number | undefined;

const rules = {
  remark: [remarkRule],
  configName: [{ required: true, message: '参数名称不能为空', trigger: 'blur' }],
  configKey: [{ required: true, message: '参数键名不能为空', trigger: 'blur' }],
  configValue: [{ required: true, message: '参数键值不能为空', trigger: 'blur' }],
};

const { formProps, layoutProps, state, isDirty, dialogProps, dialogEvents, open, setDisabled } =
  useFormDialog<ConfigForm>({
    columns: 1,
    onBeforeClose: canDiscard,
    loading: detailLoading,
    formRef: formRef,
    title: (data: ConfigForm) => (data.configId ? '修改参数配置' : '添加参数配置'),
    defaultData: () => ({
      configId: undefined,
      configName: '',
      configKey: '',
      configValue: '',
      configType: 'Y',
      remark: null as RemarkValue,
    }),
    onConfirm: async (data: ConfigForm) => {
      if (detailLoading.value || loadError.value) return false;
      if (data.configId) {
        await updateConfig(data);
      } else {
        await addConfig(data);
      }
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
  const decision = ElMessageBox.confirm('参数配置尚未保存，是否放弃本次修改？', '未保存的修改', {
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
  requestedId = id;
  return runRead(async (read) => {
    open(id ? { configId: id } : undefined);
    setDisabled(true);
    if (!id) {
      setDisabled(false);
      return;
    }
    const data = await getConfig(id, {
      signal: read.signal,
      silentError: true,
    });
    if (!read.isCurrent()) return;
    open({
      configId: data.configId ?? undefined,
      configName: data.configName ?? '',
      configKey: data.configKey ?? '',
      configValue: data.configValue ?? '',
      configType: data.configType ?? 'N',
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

defineExpose({ open: openDialog, close: closeDialog });
watch(
  () => state.visible,
  (visible) => {
    if (visible) remarkSession.value++;
  }
);

useAIContextHost('config', {
  instanceKey: () => remarkSession.value,
  revisionSource: () => state.data,
  bindings: {
    configName: { value: () => state.data.configName },
    configKey: { value: () => state.data.configKey },
    configType: {
      value: () => (state.data.configType === 'Y' ? '系统内置' : '自定义'),
    },
  },
});
</script>
