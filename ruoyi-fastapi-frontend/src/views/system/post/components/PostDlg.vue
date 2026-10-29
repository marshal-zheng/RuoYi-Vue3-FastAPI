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
      <el-alert
        v-if="formRef?.reconciliationRequired"
        title="保存结果未知，请先读取服务端记录核对"
        type="warning"
        :closable="false"
      >
        <el-button :loading="detailLoading" @click="reconcilePost">读取并核对岗位</el-button>
      </el-alert>
      <DictStatus :types="['sys_normal_disable']" />
      <ZxSchemaForm
        :key="session.key"
        ref="formRef"
        v-bind="schemaFormProps"
        :initial="session.initial"
        :create-schema="authoring.createSchema"
        :bindings="remarkBindings"
        :assert-settled="authoring.assertSettled"
        :save="session.save"
        @saved="handleSaved(session.key)"
      />
    </template>
  </zx-dialog>
</template>

<script setup lang="ts">
import { provideAIContextScope } from '@zxio/zxui/ai-context';
import { aiContextDefinitions } from '@/ai-context/definitions';
import RemarkEditor from '@/components/ui/Remark/RemarkEditor.vue';
import { computed, markRaw, ref, shallowRef, watch } from 'vue';
import { ElMessageBox } from 'element-plus';
import type { HttpError } from '@zxio/http';
import type { ZxDialogExpose } from '@zxio/zxui/dialog';
import { ZxSchemaForm, type Save, type SchemaFormInstance } from '@zxio/schema-form/formily';
import '@zxio/schema-form/style.css';
import { useEditorRead } from '@/utils/editor-read';
import { schemaFormDialog } from '@/components/ui/FormDialog';
import DictStatus from '@/components/business/DictStatus/index.vue';
import { getPost, listPost, addPost, updatePost } from '@/api/system/post';
import { isProblemDetails, isRecord } from '@/types/http-contract';
import { presentRequestError } from '@/utils/http';
import { useDict } from '@/utils/dict';
import {
  createPostSchema,
  initialPost,
  postFieldIssues,
  toPostDto,
  type PostValues,
} from './post-form';

const remarkBindings = {
  RemarkEditor: {
    component: markRaw(RemarkEditor),
    composite: true,
    group: false,
  },
};
const emit = defineEmits<{ (e: 'confirm'): void }>();
const visible = ref(false);
const requestedId = ref<number>();
const detailLoading = ref(false);
const dialogRef = ref<ZxDialogExpose>();
const formRef = ref<SchemaFormInstance<PostValues>>();
const session = shallowRef<{
  key: number;
  initial: PostValues;
  save: Save<PostValues>;
}>();
const pending = computed(() => formRef.value?.pending ?? false);
const { dialogProps, schemaFormProps } = schemaFormDialog({ columns: 1 });
const { sys_normal_disable: sysNormalDisable } = useDict('sys_normal_disable');
const authoring = createPostSchema(() =>
  sysNormalDisable.value.flatMap((option) =>
    option.value === '0' || option.value === '1'
      ? [{ label: option.label, value: option.value }]
      : []
  )
);
provideAIContextScope(aiContextDefinitions.post, {
  instanceKey: () => session.value?.key ?? 0,
  // x-ai-context fields subscribe to the Formily runtime's monotonic clock.
  revision: () => 0,
  bindings: {
    status: {
      value: () => {
        const value = formRef.value?.read().status;
        return value === undefined ? undefined : value === '0' ? '正常' : '停用';
      },
      available: () => !!formRef.value?.ready,
    },
  },
});
const { error: loadError, run: runRead } = useEditorRead(() => visible.value, detailLoading);
let generation = 0;
let writeId: number | undefined;
let dispatchedCode = '';

let opening = 0;
let discardPending: Promise<boolean> | undefined;

// Every dismissal path and replacement checks the same active form instance.
function canDiscard(): Promise<boolean> {
  if (pending.value || formRef.value?.reconciliationRequired) return Promise.resolve(false);
  if (!formRef.value?.dirty && !formRef.value?.hasUncommittedInput && !formRef.value?.fieldPending)
    return Promise.resolve(true);
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
  if (pending.value || formRef.value?.reconciliationRequired) return;
  const intent = ++opening;
  if (visible.value && !(await canDiscard())) return;
  if (intent !== opening) return;
  const key = ++generation;
  requestedId.value = id;
  writeId = id;
  dispatchedCode = '';
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
        let dto;
        try {
          dto = toPostDto(values, writeId);
        } catch (error) {
          return {
            ok: false,
            outcome: 'rejected',
            issues: [
              {
                message: error instanceof Error ? error.message : '岗位数据无效',
              },
            ],
          };
        }
        dispatchedCode = values.postCode;
        // The existing write API has no rollback; close/replacement stays locked until it settles.
        try {
          // The form owns failed-save feedback; successful writes keep the existing HTTP feedback.
          const result =
            writeId === undefined
              ? await addPost(dto, { silentError: true })
              : await updatePost(dto, { silentError: true });
          if (signal.aborted || key !== generation || !visible.value)
            return { ok: false, outcome: 'unknown', issues: [] };
          if (result?.postId !== undefined) writeId = result.postId;
          return { ok: true, values: initialPost(result) };
        } catch (error) {
          if (signal.aborted || key !== generation || !visible.value)
            return { ok: false, outcome: 'unknown', issues: [] };
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
          const status =
            isRecord(error) && isProblemDetails(error.problem) ? error.problem.status : undefined;
          if (status && status >= 400 && status < 500)
            return {
              ok: false,
              outcome: 'rejected',
              issues: issues.length
                ? issues
                : [
                    {
                      message:
                        isRecord(error) && typeof error.message === 'string'
                          ? error.message
                          : '保存被拒绝',
                    },
                  ],
            };
          return {
            ok: false,
            outcome: 'unknown',
            issues: [{ message: '保存结果未知，请读取核对' }],
          };
        }
      },
    };
  });
}

async function reconcilePost(): Promise<void> {
  const current = generation;
  await runRead(async (read) => {
    let target = writeId;
    if (target === undefined) {
      const matches = (
        await listPost({ postCode: dispatchedCode, page: 1, pageSize: 100 })
      ).items.filter((item) => item.postCode === dispatchedCode);
      if (matches.length !== 1)
        throw new Error('尚未找到唯一的已保存岗位，请稍后再次核对；当前草稿保持锁定');
      target = matches[0].postId;
    }
    const detail = await getPost(target, {
      signal: read.signal,
      silentError: true,
    });
    if (!read.isCurrent() || current !== generation || !visible.value) return;
    if (await formRef.value?.reconcile(initialPost(detail))) {
      writeId = target;
      requestedId.value = target;
    }
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
