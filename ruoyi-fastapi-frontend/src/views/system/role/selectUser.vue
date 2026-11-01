<template>
  <ZxDialog
    dialog-size="lg"
    :draggable="false"
    :show-full-screen="false"
    :destroy-on-close="false"
    :close-on-click-modal="true"
    title="选择用户"
    v-model="visible"
  >
    <DictStatus :types="['sys_normal_disable']" />
    <ZxTableRender
      v-if="visible"
      ref="refTable"
      v-model:query="queryParams"
      :definition="definition"
      :domain-key="domainKey"
      :applied="applied"
      :displayed="publication?.displayed ?? null"
      :rows="userList"
      :pagination="pagination"
      :status="listStatus"
      :selection-scope-key="String(opening)"
      :table-props="{ height: 260 }"
      @query-intent="queryIntent"
      @selection-change="handleSelectionChange"
    >
      <template #cell-status="{ row }"
        ><dict-tag :options="sys_normal_disable" :value="row.status ?? undefined"
      /></template>
    </ZxTableRender>
    <p v-if="writeError" role="alert">{{ writeError }}</p>
    <template #footer>
      <div class="dialog-footer">
        <el-button
          type="primary"
          :disabled="!canEdit || !userIds.length"
          @click="handleSelectUser"
          :loading="handleSelectUserPending"
          >确 定</el-button
        >
        <el-button @click="visible = false">取 消</el-button>
      </div>
    </template>
  </ZxDialog>
</template>

<script setup lang="ts" name="SelectUser">
import { computed, getCurrentInstance, ref, shallowRef, toRaw, watch } from 'vue';
import { useQuery } from '@tanstack/vue-query';
import { defineTableRender } from '@zxio/table-render/core';
import { ZxTableRender } from '@zxio/table-render/ui';
import '@zxio/table-render/style';
import type {
  Selection,
  TableApplied,
  TableDisplayed,
  TableQueryIntent,
} from '@zxio/table-render/core';
import type { TableRenderInstance } from '@zxio/table-render/ui';
import type { UserInfoModel } from '@/api/_generated/types.gen';
import type { QueryScope } from '@/queries/context';
import { useOperation } from '@/utils/operation';
import { ElMessage } from 'element-plus';
import { captureUserCommand, roleUsersOptions, userCommands } from '@/queries/system/user';
import { queryScope, requireQueryScope } from '@/queries/context';
import { queryClient } from '@/queries/client';
import { checkPermi } from '@/utils/permission';

interface Query {
  userName?: string;
  phonenumber?: string;
}
const props = defineProps<{ roleId?: number | string }>();
const emit = defineEmits<{ ok: [] }>();
const proxy = getCurrentInstance()!.proxy!;
const { sys_normal_disable } = proxy.useDict('sys_normal_disable');
const visible = ref(false);
const userIds = ref<number[]>([]);
const openingScope = shallowRef<QueryScope | null>(null);
const openingRoleId = ref(0);
const opening = ref(0);
const writeError = ref('');
const queryParams = ref<Partial<Query>>({});
const submitted = ref<Partial<Query>>({});
const currentPage = ref(1);
const pageSize = ref(10);
const canRead = computed(() => visible.value && openingScope.value === queryScope.value);
const domainKey = computed(
  () => `${openingScope.value?.key ?? 'closed'}:${openingRoleId.value}:${opening.value}`
);
const canEdit = computed(
  () =>
    canRead.value &&
    checkPermi(['system:role:edit']) &&
    (openingRoleId.value !== 1 || openingScope.value?.userId === '1')
);
const userOptions = computed(() =>
  roleUsersOptions(canRead.value ? openingScope.value : null, openingRoleId.value, 'unallocated', {
    ...submitted.value,
    page: currentPage.value,
    pageSize: pageSize.value,
  })
);
const usersQuery = useQuery(userOptions);
const applied = computed<TableApplied<Query> | null>(() =>
  canRead.value
    ? {
        domainKey: domainKey.value,
        query: submitted.value,
        pager: { page: currentPage.value, size: pageSize.value },
        sort: [],
      }
    : null
);
const publication = shallowRef<{
  rows: readonly UserInfoModel[];
  total: number;
  displayed: TableDisplayed<Query>;
} | null>(null);
let revision = 0;
let lastPublication: { key: string; updatedAt: number; result: unknown } | undefined;
watch(
  [usersQuery.data, usersQuery.dataUpdatedAt, userOptions],
  ([result]) => {
    if (
      !result ||
      !applied.value ||
      toRaw(queryClient.getQueryData(userOptions.value.queryKey)) !== toRaw(result)
    )
      return;
    const lastPage = Math.max(1, Math.ceil(result.total / pageSize.value));
    if (currentPage.value > lastPage) {
      currentPage.value = lastPage;
      return;
    }
    const key = JSON.stringify([domainKey.value, userOptions.value.queryKey]);
    const updatedAt = usersQuery.dataUpdatedAt.value;
    if (
      publication.value &&
      lastPublication?.key === key &&
      lastPublication.updatedAt === updatedAt &&
      lastPublication.result === toRaw(result)
    )
      return;
    lastPublication = { key, updatedAt, result: toRaw(result) };
    // Publish only the cache entry for the accepted key, never an old observer value.
    publication.value = {
      rows: result.items,
      total: result.total,
      displayed: {
        domainKey: domainKey.value,
        revision: ++revision,
        input: {
          query: { ...submitted.value },
          pager: { page: currentPage.value, size: pageSize.value },
          sort: [],
        },
      },
    };
  },
  { immediate: true, flush: 'post' }
);
const userList = computed(() => publication.value?.rows ?? []);
const pagination = computed(() => ({
  ...(publication.value?.displayed.input.pager ?? { page: 1, size: 10 }),
  total: publication.value?.total ?? 0,
}));
const listStatus = computed(() => ({
  loading: usersQuery.isLoading.value,
  refreshing: usersQuery.isFetching.value && publication.value !== null,
  error: usersQuery.error.value,
  paused: usersQuery.fetchStatus.value === 'paused',
}));
function canSelectUser(row: UserInfoModel) {
  return canEdit.value && Number(row.userId) !== 1;
}
const definition = defineTableRender<UserInfoModel, Query>()({
  key: 'role-unallocated-users',
  title: '选择授权用户',
  rowKey: (row) => Number(row.userId),
  selection: {
    mode: 'multiple',
    scope: 'explicit',
    selectable: canSelectUser,
    rowClick: true,
  },
  search: [
    {
      key: 'userName',
      label: '用户名称',
      control: 'text',
      placement: 'keyword',
      toLogical: (value) => String(value ?? '').trim() || undefined,
    },
    {
      key: 'phonenumber',
      label: '手机号码',
      control: 'text',
      placement: 'inline',
      toLogical: (value) => String(value ?? '').trim() || undefined,
    },
  ],
  columns: [
    {
      key: 'userName',
      label: '用户名称',
      prop: 'userName',
      overflow: 'tooltip',
      minWidth: 120,
    },
    {
      key: 'nickName',
      label: '用户昵称',
      prop: 'nickName',
      overflow: 'tooltip',
      minWidth: 120,
    },
    {
      key: 'email',
      label: '邮箱',
      prop: 'email',
      overflow: 'tooltip',
      minWidth: 150,
    },
    { key: 'phonenumber', label: '手机', prop: 'phonenumber', minWidth: 140 },
    { key: 'status', label: '状态', prop: 'status', width: 80 },
    {
      key: 'createTime',
      label: '创建时间',
      prop: 'createTime',
      type: 'datetime',
      width: 180,
    },
  ],
});
const refTable = shallowRef<TableRenderInstance<typeof definition, UserInfoModel, Query>>();
watch(
  [queryScope, () => props.roleId],
  () => {
    visible.value = false;
  },
  { flush: 'sync' }
);
watch(
  visible,
  (value) => {
    if (!value) {
      opening.value++;
      userIds.value = [];
      writeError.value = '';
      publication.value = null;
    }
  },
  { flush: 'sync' }
);
function show() {
  opening.value++;
  openingScope.value = requireQueryScope();
  openingRoleId.value = Number(props.roleId);
  queryParams.value = {};
  submitted.value = {};
  currentPage.value = 1;
  pageSize.value = 10;
  userIds.value = [];
  writeError.value = '';
  publication.value = null;
  visible.value = true;
}
function handleSelectionChange(selection: Selection<UserInfoModel>) {
  userIds.value = selection.keys.filter((key): key is number => typeof key === 'number');
}
function getList() {
  if (canRead.value) void usersQuery.refetch({ cancelRefetch: false });
}
function queryIntent(intent: TableQueryIntent<Query>) {
  if (!canRead.value || intent.domainKey !== domainKey.value) return;
  const next = { ...intent.input.query };
  const pager = intent.input.pager!;
  const unchanged =
    JSON.stringify(next) === JSON.stringify(submitted.value) &&
    pager.page === currentPage.value &&
    pager.size === pageSize.value;
  submitted.value = next;
  currentPage.value = pager.page;
  pageSize.value = pager.size;
  if (unchanged) getList();
}
const { run: handleSelectUser, pending: handleSelectUserPending } = useOperation(async () => {
  const scope = openingScope.value;
  if (!canEdit.value || !scope) return;
  if (!userIds.value.length) {
    ElMessage.error('请选择要分配的用户');
    return;
  }
  const generation = opening.value;
  const command = captureUserCommand(
    { roleId: openingRoleId.value, userIds: userIds.value },
    scope
  );
  writeError.value = '';
  try {
    await userCommands.assignRoleUsers(command);
    if (generation !== opening.value || command.scope !== queryScope.value) return;
    visible.value = false;
    emit('ok');
  } catch {
    if (generation === opening.value && command.scope === queryScope.value)
      writeError.value = '分配失败，已保留所选用户，请重试。';
  }
});
defineExpose({ show });
</script>
