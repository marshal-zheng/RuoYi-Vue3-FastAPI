<template>
  <ZxDialog
    ref="dialogRef"
    v-model="visible"
    v-bind="dialogProps"
    :title="requestedId === undefined ? '添加用户' : '修改用户'"
    :ok-text="requestedId === undefined ? '创建' : '保存'"
    :loading="detailLoading"
    :ok-loading="!!formRef?.pending"
    :ok-disabled="detailLoading || !!loadError || !session"
    :confirm="submit"
    :handle-before-cancel="canDiscard"
  >
    <span v-if="editorQuery.isPaused.value" aria-live="polite">用户详情等待网络连接</span>
    <el-alert
      v-else-if="editorQuery.error.value && !loadError"
      title="用户详情刷新失败，保留编辑草稿"
      type="error"
      :closable="false"
    >
      <el-button link type="primary" @click="retryResource">重试读取</el-button>
    </el-alert>
    <el-alert v-if="loadError" :title="loadError" type="error" :closable="false" show-icon>
      <el-button link type="primary" @click="handleRetry">重试</el-button>
    </el-alert>
    <template v-if="session">
      <span v-if="departmentQuery.paused.value" role="status">部门列表等待网络连接</span>
      <el-alert
        v-else-if="departmentQuery.error.value"
        :title="departmentQuery.data.value ? '部门列表刷新失败，保留当前选择' : '部门列表读取失败'"
        type="error"
        :closable="false"
      >
        <el-button link type="primary" @click="retryDepartments">重试</el-button>
      </el-alert>
      <el-alert
        v-if="formRef?.reconciliationRequired"
        title="保存结果未知，请先读取服务端记录核对"
        type="warning"
        :closable="false"
      >
        <el-button :loading="detailLoading" @click="reconcileUser">读取并核对用户</el-button>
      </el-alert>
      <DictStatus :types="['sys_normal_disable']" />
      <ZxSchemaForm
        :key="session.key"
        ref="formRef"
        v-bind="schemaFormProps"
        :initial="session.initial"
        :create-schema="session.createSchema"
        :save="session.save"
        :bindings="bindings"
        :disabled="detailLoading || !!loadError"
        @saved="handleSaved(session.key)"
      />
    </template>
  </ZxDialog>
</template>

<script setup lang="ts">
import { computed, markRaw, nextTick, ref, shallowRef, watch } from 'vue';
import { ElMessageBox } from 'element-plus';
import { useQuery } from '@tanstack/vue-query';
import { useResourceQuery } from '@zxio/vue-query/resources';
import { useResourceView } from '@zxio/vue-query/ui';
import { dataClient } from '@/queries/client';
import { queryRequest, type HttpError } from '@zxio/http';
import { ZxSchemaForm, type Save, type SchemaFormInstance } from '@zxio/schema-form/formily';
import '@zxio/schema-form/style.css';
import type { ZxDialogExpose } from '@zxio/zxui/dialog';
import type {
  UserCreateModel,
  UserDetailReadModel,
  UserUpdateModel,
} from '@/api/_generated/types.gen';
import { useAIContextHost } from '@/ai-context/host';
import RemarkEditor from '@/components/ui/Remark/RemarkEditor.vue';
import DictSelect from '@/components/business/DictSelect/index.vue';
import DictStatus from '@/components/business/DictStatus/index.vue';
import { schemaFormDialog } from '@/components/ui/FormDialog';
import { useEditorRead } from '@/utils/editor-read';
import { useDict } from '@/utils/dict';
import { presentRequestError } from '@/utils/http';
import { isRecord } from '@/types/http-contract';
import { getUser, listUser } from '@/api/system/user';
import {
  captureUserCommand,
  invalidateUserQueries,
  userCommands,
  readUserEditor,
  userDetailOptions,
  userCreateOptions,
} from '@/queries/system/user';
import {
  queryScope,
  requireQueryScope,
  scopeRequestOptions,
  type QueryScope,
} from '@/queries/context';
import { copyUserDeptTree, departmentResource } from '@/queries/system/dept';
import {
  createUserSchema,
  initialUser,
  toUserDto,
  userFieldIssues,
  type UserValues,
} from './user-form';

const emit = defineEmits<{ success: [] }>();
const { dialogProps, schemaFormProps } = schemaFormDialog({ columns: 2 });
const bindings = {
  RemarkEditor: {
    component: markRaw(RemarkEditor),
    composite: true,
    group: false,
  },
  UserDictSelect: { component: markRaw(DictSelect) },
};
const { sys_normal_disable: statusOptions } = useDict('sys_normal_disable');
const visible = ref(false);
const requestedId = ref<number>();
const dialogRef = ref<ZxDialogExpose>();
const formRef = ref<SchemaFormInstance<UserValues>>();
const detailLoading = ref(false);
const editorScope = shallowRef<QueryScope | null>(null);
const postOptions = ref<NonNullable<UserDetailReadModel['posts']>>([]);
const roleOptions = ref<NonNullable<UserDetailReadModel['roles']>>([]);
const selectedDepartment = shallowRef<{ id: number; label: string } | null>(null);
const session = shallowRef<{
  key: number;
  initial: UserValues;
  createSchema: ReturnType<typeof createUserSchema>;
  save: Save<UserValues>;
}>();
const values = computed(() => formRef.value?.read());
const {
  error: loadError,
  run: runRead,
  cancel: cancelRead,
} = useEditorRead(() => visible.value, detailLoading);
const createQuery = useQuery(() =>
  userCreateOptions(visible.value && requestedId.value === undefined ? editorScope.value : null)
);
const detailQuery = useQuery(() =>
  userDetailOptions(
    visible.value && requestedId.value !== undefined ? editorScope.value : null,
    requestedId.value
  )
);
const editorQuery = computed(() => (requestedId.value === undefined ? createQuery : detailQuery));
const departmentQuery = useResourceQuery(departmentResource, 'userTree', undefined, {
  client: dataClient,
  active: () => visible.value && editorScope.value === queryScope.value,
});
const departmentView = useResourceView(departmentQuery, {
  isEmpty: (items) => items.length === 0,
});
const deptOptions = computed(() => copyUserDeptTree(departmentQuery.data.value ?? []));
const selectedDeptCache = computed(() =>
  selectedDepartment.value && selectedDepartment.value.id === values.value?.deptId
    ? [selectedDepartment.value]
    : []
);
function findDepartment(
  nodes: typeof deptOptions.value,
  id: number | null | undefined
): (typeof nodes)[number] | undefined {
  for (const node of nodes) {
    if (String(node.id) === String(id)) return node;
    const found = node.children && findDepartment(node.children, id);
    if (found) return found;
  }
  return undefined;
}
watch(
  [() => values.value?.deptId, deptOptions],
  ([id, options]) => {
    if (!visible.value || id === undefined) return;
    const current = findDepartment(options, id);
    if (current && id !== null) selectedDepartment.value = { id, label: current.label };
    else if (selectedDepartment.value?.id !== id) selectedDepartment.value = null;
  },
  { flush: 'sync' }
);
let generation = 0;
let openingIntent = 0;
let discardPending: Promise<boolean> | undefined;
let writeId: number | undefined;
let dispatchedName = '';
watch(
  queryScope,
  () => {
    ++openingIntent;
    ++generation;
    cancelRead();
    visible.value = false;
    session.value = undefined;
    editorScope.value = null;
    selectedDepartment.value = null;
  },
  { flush: 'sync' }
);
const edited = () =>
  !!(formRef.value?.dirty || formRef.value?.hasUncommittedInput || formRef.value?.fieldPending);
function canDiscard(): Promise<boolean> {
  if (!visible.value) return Promise.resolve(true);
  if (formRef.value?.pending || formRef.value?.reconciliationRequired)
    return Promise.resolve(false);
  if (detailLoading.value || loadError.value || !edited()) return Promise.resolve(true);
  if (discardPending) return discardPending;
  const key = generation,
    scope = editorScope.value;
  const decision = ElMessageBox.confirm('用户信息尚未保存，是否放弃本次修改？', '未保存的修改', {
    confirmButtonText: '放弃修改',
    cancelButtonText: '继续编辑',
    type: 'warning',
  })
    .then(
      () =>
        visible.value && key === generation && scope === queryScope.value && !formRef.value?.pending
    )
    .catch(() => false)
    .finally(() => {
      if (discardPending === decision) discardPending = undefined;
    });
  discardPending = decision;
  return decision;
}
function acceptCatalogs(response: UserDetailReadModel) {
  postOptions.value = [...(response.posts ?? [])];
  roleOptions.value = [...(response.roles ?? [])];
  const user = response.data;
  selectedDepartment.value =
    user?.deptId && typeof user.dept?.deptName === 'string'
      ? { id: user.deptId, label: user.dept.deptName }
      : null;
}
function saveFor(key: number, scope: QueryScope): Save<UserValues> {
  return async (snapshot, signal) => {
    const current = () =>
      !signal.aborted && visible.value && key === generation && scope === queryScope.value;
    if (!current())
      return {
        ok: false,
        outcome: 'rejected',
        issues: [{ message: '用户编辑会话已结束' }],
      };
    let dto: UserCreateModel | UserUpdateModel;
    try {
      dto = toUserDto(snapshot, writeId);
    } catch (error) {
      return {
        ok: false,
        outcome: 'rejected',
        issues: [
          {
            message: error instanceof Error ? error.message : '用户数据格式不正确',
          },
        ],
      };
    }
    dispatchedName = snapshot.userName;
    try {
      const response =
        writeId === undefined
          ? await userCommands.createUser(
              captureUserCommand(dto as UserCreateModel, scope, {
                silentError: true,
              })
            )
          : await userCommands.updateUser(
              captureUserCommand(dto as UserUpdateModel, scope, {
                silentError: true,
              })
            );
      if (!current()) return { ok: false, outcome: 'unknown', issues: [] };
      const id = response?.data?.userId;
      if (
        !Number.isSafeInteger(id) ||
        !id ||
        id <= 0 ||
        (writeId !== undefined && id !== writeId) ||
        (writeId === undefined && response.data?.userName !== dispatchedName)
      )
        throw new Error('保存返回的用户身份无法确认');
      writeId = id;
      return { ok: true, values: initialUser(response) };
    } catch (error) {
      if (!current()) return { ok: false, outcome: 'unknown', issues: [] };
      const problem = isRecord(error) && isRecord(error.problem) ? error.problem : undefined;
      const status = Number(problem?.status);
      if (status === 401 || [20001, 20002].includes(Number(problem?.errorCode)))
        presentRequestError(error as HttpError, {
          silentError: false,
          feedback: { mode: 'auto' },
        });
      const issues = userFieldIssues(error);
      return {
        ok: false,
        outcome: status >= 400 && status < 500 ? 'rejected' : 'unknown',
        issues: issues.length
          ? issues
          : [
              {
                message:
                  status >= 400 && status < 500
                    ? error instanceof Error
                      ? error.message
                      : '用户保存被拒绝'
                    : '保存结果未知，请读取核对',
              },
            ],
      };
    }
  };
}
function createSession(
  key: number,
  userId: number | undefined,
  response: UserDetailReadModel,
  scope: QueryScope
) {
  return {
    key,
    initial: initialUser(response),
    createSchema: createUserSchema({
      creating: userId === undefined,
      departments: () => deptOptions.value,
      departmentCache: () => selectedDeptCache.value,
      departmentLoading: () => departmentView.loading.value,
      posts: () => postOptions.value,
      roles: () => roleOptions.value,
      statuses: () => statusOptions.value,
      active: () => visible.value,
    }),
    save: saveFor(key, scope),
  };
}
async function openDialog(userId?: number) {
  const intent = ++openingIntent;
  if (visible.value && !(await canDiscard())) return;
  if (intent !== openingIntent) return;
  const scope = requireQueryScope(),
    key = ++generation;
  editorScope.value = scope;
  requestedId.value = userId;
  writeId = userId;
  dispatchedName = '';
  session.value = undefined;
  selectedDepartment.value = null;
  postOptions.value = [];
  roleOptions.value = [];
  visible.value = true;
  return runRead(async (read) => {
    const response = await readUserEditor(scope, userId, read.signal);
    if (!read.isCurrent() || intent !== openingIntent || scope !== queryScope.value) return;
    acceptCatalogs(response);
    session.value = createSession(key, userId, response, scope);
    await nextTick();
  });
}
async function closeDialog() {
  if (!(await canDiscard())) return;
  ++openingIntent;
  cancelRead();
  visible.value = false;
}
watch(
  visible,
  (value) => {
    if (!value) {
      ++openingIntent;
      ++generation;
      session.value = undefined;
    }
  },
  { flush: 'sync' }
);
async function reconcileUser() {
  const scope = editorScope.value,
    key = generation;
  if (!scope || scope !== queryScope.value || !formRef.value?.reconciliationRequired) return;
  return runRead(async (read) => {
    let id = writeId;
    if (id === undefined) {
      const response = await listUser(
        { userName: dispatchedName, page: 1, pageSize: 100 },
        queryRequest(read.signal, scopeRequestOptions(scope))
      );
      const matches = response.items.filter((user) => user.userName === dispatchedName);
      if (
        matches.length !== 1 ||
        !Number.isSafeInteger(matches[0].userId) ||
        !matches[0].userId ||
        matches[0].userId <= 0
      )
        throw new Error('尚未找到唯一的已保存用户，请稍后再次核对');
      id = matches[0].userId;
    }
    // Reconciliation must begin a new read after the write; an opening query may still hold a pre-write request.
    const response = await getUser(id, {
      signal: read.signal,
      requestOptions: scopeRequestOptions(scope),
      silentError: true,
    });
    if (
      response.data?.userId !== id ||
      (writeId === undefined && response.data?.userName !== dispatchedName)
    ) {
      throw new Error('读取的用户身份与本次保存不符，请再次核对');
    }
    if (!read.isCurrent() || scope !== queryScope.value || key !== generation || !visible.value)
      return;
    if (
      (await formRef.value?.reconcile(initialUser(response))) &&
      read.isCurrent() &&
      scope === queryScope.value &&
      key === generation
    ) {
      const wasCreating = writeId === undefined;
      writeId = id;
      requestedId.value = id;
      acceptCatalogs(response);
      invalidateUserQueries(scope);
      if (wasCreating) session.value = createSession(++generation, id, response, scope);
    }
  }).catch(() => {
    /* Current read owns inline failure and retry. */
  });
}
function handleRetry() {
  if (formRef.value?.reconciliationRequired) return reconcileUser();
  return openDialog(requestedId.value).catch(() => {
    /* Current read owns feedback. */
  });
}
function retryResource() {
  if (editorQuery.value.isEnabled.value)
    void editorQuery.value.refetch({ cancelRefetch: false, throwOnError: true }).catch(() => {});
}
function retryDepartments() {
  if (departmentQuery.enabled.value) void departmentQuery.refresh().catch(() => {});
}
function submit() {
  if (
    !visible.value ||
    editorScope.value !== queryScope.value ||
    detailLoading.value ||
    loadError.value
  )
    return Promise.resolve(false);
  return formRef.value?.submit() ?? Promise.resolve(false);
}
function handleSaved(key: number) {
  if (!visible.value || key !== generation || editorScope.value !== queryScope.value) return;
  emit('success');
  visible.value = false;
}
defineExpose({ open: openDialog, close: closeDialog });
useAIContextHost('user', {
  instanceKey: () => session.value?.key ?? generation,
  revisionSource: () => [
    values.value,
    selectedDepartment.value,
    postOptions.value,
    roleOptions.value,
  ],
  bindings: {
    userName: {
      value: () => values.value?.userName,
      available: () => !!formRef.value?.ready,
    },
    deptName: { value: () => selectedDepartment.value?.label },
    postNames: {
      value: () =>
        postOptions.value
          .filter((item) => values.value?.postIds.includes(item.postId!))
          .map((item) => item.postName),
    },
    roleNames: {
      value: () =>
        roleOptions.value
          .filter((item) => values.value?.roleIds.includes(item.roleId!))
          .map((item) => item.roleName),
    },
    status: { value: () => (values.value?.status === '0' ? '正常' : '停用') },
  },
});
</script>
