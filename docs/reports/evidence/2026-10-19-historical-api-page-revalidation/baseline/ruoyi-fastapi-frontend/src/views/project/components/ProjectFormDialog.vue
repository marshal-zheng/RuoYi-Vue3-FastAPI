<template>
  <ZxDialog v-bind="dialogProps" v-on="dialogEvents" data-testid="project-form-dialog">
    <el-alert v-if="loadError" :title="loadError" type="error" :closable="false" show-icon>
      <el-button link type="primary" @click="handleRetry">重试</el-button>
    </el-alert>
    <div v-show="!loadError" class="py-4">
      <el-form ref="formRef" :model="state.data" :rules="formRules" v-bind="formProps">
        <FormGrid v-bind="layoutProps">
          <el-form-item label="工程名称" prop="projectName">
            <zx-input
              v-model="state.data.projectName"
              data-testid="project-form-name"
              aria-label="工程名称"
              placeholder="请输入工程名称"
            />
          </el-form-item>
          <el-form-item label="工程描述" prop="projectDesc">
            <zx-input
              v-model="state.data.projectDesc"
              data-testid="project-form-desc"
              aria-label="工程描述"
              type="textarea"
              :rows="4"
              placeholder="请输入工程描述"
            />
          </el-form-item>
        </FormGrid>
      </el-form>
    </div>
  </ZxDialog>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useEditorRead } from '@/utils/editor-read';
import { FormGrid, useFormDialog } from '@/components/ui/FormDialog';
import { getProject, addProject, updateProject } from '@/api/project/project';

const emit = defineEmits(['success']);

const formRef = ref();
const detailLoading = ref(false);
let requestedId = null;

const formRules = computed(() => ({
  projectName: [{ required: true, message: '工程名称不能为空', trigger: 'blur' }],
}));

const { formProps, layoutProps, state, dialogProps, dialogEvents, open, close, setDisabled } =
  useFormDialog({
    columns: 1,
    loading: detailLoading,
    title: (data) => (data?.projectId ? '编辑工程' : '添加工程'),

    okText: computed(() => (state.data.projectId ? '保存' : '下一步')),
    formRef,
    preValidate: true,
    autoScrollToError: true,
    autoResetForm: true,
    defaultData: () => ({
      projectId: null,
      projectName: '',
      projectDesc: '',
    }),
    onConfirm: async (data) => {
      if (detailLoading.value || loadError.value || data.projectId !== requestedId) return false;
      if (data.projectId) {
        const res = await updateProject(data);
        emit('success', { mode: 'edit', data: res });
        return res;
      }
      const res = await addProject(data);
      // http 客户端已解包 payload.data，res 直接是项目数据
      const newId = res?.projectId || res?.id || null;
      emit('success', { mode: 'create', projectId: newId, versionId: res.versionId, data: res });
      return res;
    },
  });

const {
  error: loadError,
  run: runRead,
  cancel: cancelRead,
} = useEditorRead(() => state.visible, detailLoading);

function openDialog(payload) {
  const id =
    payload?.projectId ||
    (typeof payload === 'number' || typeof payload === 'string' ? payload : null);
  requestedId = id === null ? null : Number(id);
  return runRead(async (read) => {
    open(id ? { projectId: requestedId } : undefined);
    setDisabled(true);
    if (!id) {
      setDisabled(false);
      return;
    }
    const detail = await getProject(id, { signal: read.signal, silentError: true });
    if (!read.isCurrent()) return;
    open({
      projectId: detail.projectId,
      projectName: detail.projectName ?? '',
      projectDesc: detail.projectDesc ?? '',
    });
    setDisabled(false);
  });
}
function closeDialog() {
  cancelRead();
  return close();
}
function handleRetry() {
  return openDialog(requestedId).catch(() => {
    /* 当前读取已负责反馈。 */
  });
}

defineExpose({ open: openDialog, close: closeDialog });
</script>

<style scoped></style>
