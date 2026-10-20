<template>
  <zx-dialog
    ref="dialogRef"
    v-model="visible"
    v-bind="dialogProps"
    :title="requestedId === undefined ? '添加岗位' : '修改岗位'"
    :loading="detailLoading"
    :ok-disabled="detailLoading || !!loadError || !session"
    :ok-loading="pending"
    :confirm="submit"
    :handle-before-cancel="canDiscard"
  >
    <el-alert v-if="loadError" :title="loadError" type="error" :closable="false" show-icon>
      <el-button link type="primary" @click="handleRetry">重试</el-button>
    </el-alert>
    <template v-if="session">
      <DictStatus :types="['sys_normal_disable']" />
      <ZxSchemaForm
        :key="session.key"
        ref="formRef"
        v-bind="schemaFormProps"
        :initial="session.initial"
        :create-rules="createRules"
        :save="session.save"
        @saved="handleSaved(session.key)"
      />
    </template>
  </zx-dialog>
</template>

<script setup lang="ts">
import { computed, ref, shallowRef, watch } from 'vue';
import { ElMessageBox } from 'element-plus';
import type { HttpError } from '@zxio/http';
import type { ZxDialogExpose } from '@zxio/zxui/dialog';
import { ZxSchemaForm, type Save, type SchemaFormInstance } from '@zxio/schema-form/form-create';
import '@zxio/schema-form/style.css';
import { useEditorRead } from '@/utils/editor-read';
import { schemaFormDialog } from '@/components/ui/FormDialog';
import DictStatus from '@/components/business/DictStatus/index.vue';
import { getPost, addPost, updatePost } from '@/api/system/post';
import { isProblemDetails, isRecord } from '@/types/http-contract';
import { presentRequestError } from '@/utils/http';
import { useDict } from '@/utils/dict';
import {
  createPostRules,
  initialPost,
  postFieldIssues,
  toPostDto,
  type PostValues,
} from './post-form';

const emit = defineEmits<{ (e: 'confirm'): void }>();
const visible = ref(false);
const requestedId = ref<number>();
const detailLoading = ref(false);
const dialogRef = ref<ZxDialogExpose>();
const formRef = ref<SchemaFormInstance<PostValues>>();
const session = shallowRef<{ key: number; initial: PostValues; save: Save<PostValues> }>();
const pending = computed(() => formRef.value?.pending ?? false);
const { dialogProps, schemaFormProps } = schemaFormDialog({ columns: 1 });
const { sys_normal_disable: sysNormalDisable } = useDict('sys_normal_disable');
const createRules = () =>
  createPostRules(() =>
    sysNormalDisable.value.flatMap((option) =>
      option.value === '0' || option.value === '1'
        ? [{ label: option.label, value: option.value }]
        : []
    )
  );
const { error: loadError, run: runRead } = useEditorRead(() => visible.value, detailLoading);
let generation = 0;
let opening = 0;
let discardPending: Promise<boolean> | undefined;

// Every dismissal path and replacement checks the same active form instance.
function canDiscard(): Promise<boolean> {
  if (pending.value) return Promise.resolve(false);
  if (!formRef.value?.dirty) return Promise.resolve(true);
  if (discardPending) return discardPending;
  const current = generation;
  const decision = ElMessageBox.confirm('岗位信息尚未保存，是否放弃本次修改？', '未保存的修改', {
    confirmButtonText: '放弃修改',
    cancelButtonText: '继续编辑',
    type: 'warning',
  })
    .then(() => current === generation && !pending.value)
    .catch(() => false)
    .finally(() => {
      if (discardPending === decision) discardPending = undefined;
    });
  discardPending = decision;
  return decision;
}

async function openDialog(id?: number): Promise<void> {
  if (pending.value) return;
  const intent = ++opening;
  if (visible.value && !(await canDiscard())) return;
  if (intent !== opening) return;
  const key = ++generation;
  requestedId.value = id;
  session.value = undefined;
  visible.value = true;
  await runRead(async (read) => {
    const detail =
      id === undefined ? undefined : await getPost(id, { signal: read.signal, silentError: true });
    if (!read.isCurrent() || key !== generation || !visible.value) return;
    session.value = {
      key,
      initial: initialPost(detail),
      save: async (values, signal) => {
        if (signal.aborted || key !== generation || !visible.value) {
          return {
            ok: false,
            issues: [{ message: '编辑会话已结束，请重新打开岗位' }],
          };
        }
        const dto = toPostDto(values, id);
        // The existing write API has no rollback; close/replacement stays locked until it settles.
        try {
          // The form owns failed-save feedback; successful writes keep the existing HTTP feedback.
          if (id === undefined) await addPost(dto, { silentError: true });
          else await updatePost(dto, { silentError: true });
        } catch (error) {
          if (signal.aborted || key !== generation || !visible.value)
            return { ok: false, issues: [] };
          if (
            isRecord(error) &&
            isProblemDetails(error.problem) &&
            (error.problem.status === 401 ||
              [20001, 20002].includes(Number(error.problem.errorCode)))
          ) {
            presentRequestError(error as unknown as HttpError, {
              silentError: false,
              feedback: { mode: 'auto' },
            });
            return { ok: false, issues: [] };
          }
          const issues = postFieldIssues(error);
          if (issues.length) return { ok: false, issues };
          throw error;
        }
        return { ok: true };
      },
    };
  });
}

function submit(): Promise<boolean> {
  if (detailLoading.value || loadError.value || !session.value) return Promise.resolve(false);
  return formRef.value?.submit() ?? Promise.resolve(false);
}

function handleSaved(key: number): void {
  if (!visible.value || session.value?.key !== key) return;
  emit('confirm');
  visible.value = false;
}

function closeDialog(): Promise<void> {
  return dialogRef.value?.close() ?? Promise.resolve();
}

function handleRetry(): void {
  void openDialog(requestedId.value).catch(() => {
    /* The current detail read owns feedback. */
  });
}

watch(
  visible,
  (value) => {
    if (!value) {
      opening += 1;
      generation += 1;
      session.value = undefined;
    }
  },
  { flush: 'sync' }
);

defineExpose({ open: openDialog, close: closeDialog });
</script>
