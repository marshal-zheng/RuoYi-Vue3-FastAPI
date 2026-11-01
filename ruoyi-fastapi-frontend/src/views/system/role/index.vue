<template>
  <ZxContentWrap fill>
    <ZxTableRender
      v-if="queryScope"
      ref="tableRef"
      v-model:query="draft"
      :definition="definition"
      :domain-key="domainKey"
      :applied="applied"
      :displayed="publication?.displayed ?? null"
      :rows="roleRows"
      :pagination="pagination"
      :status="listStatus"
      @query-intent="queryIntent"
    >
      <template #role-status="{ logicalValue, commit, controlAttrs }">
        <DictSelect
          dict-type="sys_normal_disable"
          :model-value="logicalValue ?? undefined"
          v-bind="controlAttrs"
          placeholder="角色状态"
          clearable
          @update:model-value="commit"
        />
      </template>
      <template #cell-status="{ row }">
        <el-switch
          :model-value="row.status ?? undefined"
          active-value="0"
          inactive-value="1"
          :aria-label="`${row.roleName}状态`"
          :loading="statusOperations.get(row.roleId)?.pending.value"
          :disabled="!canEditRole(row) || statusOperations.has(row.roleId)"
          @change="(value: string | number | boolean) => handleStatusChange(value, row)"
        />
      </template>
    </ZxTableRender>
    <RoleFormDrawer ref="roleFormDrawerRef" @success="clearSelection" />
    <RoleDataScopeDrawer ref="roleDataScopeDrawerRef" @success="clearSelection" />
  </ZxContentWrap>
</template>

<script setup lang="ts" name="Role">
import { computed, getCurrentInstance, ref, shallowReactive, shallowRef, toRaw, watch } from 'vue';
import { useRouter } from 'vue-router';
import { useQuery } from '@tanstack/vue-query';
import {
  defineTableRender,
  type TableApplied,
  type TableDisplayed,
  type TableQueryIntent,
} from '@zxio/table-render/core';
import { ZxTableRender, type TableRenderInstance } from '@zxio/table-render/ui';
import '@zxio/table-render/style';
import type { RoleRecord } from '@/api/system/role';
import { queryScope } from '@/queries/context';
import { queryClient } from '@/queries/client';
import {
  captureRoleCommand,
  normalizeRoleFilters,
  roleCommands,
  roleListOptions,
  type RoleFilters,
} from '@/queries/system/role';
import { useSystemListNavigation } from '@/store/modules/system-list-navigation';
import { useOperation } from '@/utils/operation';
import { checkPermi } from '@/utils/permission';
import DictSelect from '@/components/business/DictSelect/index.vue';
import RoleFormDrawer from './components/RoleFormDrawer.vue';
import RoleDataScopeDrawer from './components/RoleDataScopeDrawer.vue';

type Query = Pick<RoleFilters, 'roleName' | 'roleKey' | 'status'> & { dateRange?: string[] };
function logicalFilters(filters: RoleFilters): Query {
  return {
    ...(filters.roleName ? { roleName: filters.roleName } : {}),
    ...(filters.roleKey ? { roleKey: filters.roleKey } : {}),
    ...(filters.status ? { status: filters.status } : {}),
    ...(filters.beginTime || filters.endTime
      ? { dateRange: [filters.beginTime ?? '', filters.endTime ?? ''] }
      : {}),
  };
}
const router = useRouter();
const proxy = getCurrentInstance()!.proxy!;
const roleFormDrawerRef = shallowRef<InstanceType<typeof RoleFormDrawer>>();
const roleDataScopeDrawerRef = shallowRef<InstanceType<typeof RoleDataScopeDrawer>>();
const listNavigation = useSystemListNavigation();
const restored = listNavigation.take('roles');
const submitted = ref(normalizeRoleFilters(restored?.filters));
const draft = ref<Query>(logicalFilters(submitted.value));
const currentPage = ref(restored?.page ?? 1);
const pageSize = ref(restored?.size ?? 10);
const queryOptions = computed(() =>
  roleListOptions(queryScope.value, {
    ...submitted.value,
    page: currentPage.value,
    pageSize: pageSize.value,
  })
);
const roleQuery = useQuery(queryOptions);
const domainKey = computed(() => queryScope.value?.key ?? 'unavailable');
const applied = computed<TableApplied<Query>>(() => ({
  domainKey: domainKey.value,
  query: logicalFilters(submitted.value),
  pager: { page: currentPage.value, size: pageSize.value },
  sort: [],
}));
const publication = shallowRef<{
  rows: readonly RoleRecord[];
  total: number;
  displayed: TableDisplayed<Query>;
} | null>(null);
let revision = 0;
let lastPublication: { key: string; updatedAt: number; result: unknown } | undefined;
watch(
  [roleQuery.data, roleQuery.dataUpdatedAt, queryOptions],
  ([result]) => {
    if (
      !queryScope.value ||
      !result ||
      toRaw(queryClient.getQueryData(queryOptions.value.queryKey)) !== toRaw(result)
    ) {
      publication.value = null;
      return;
    }
    const key = JSON.stringify(queryOptions.value.queryKey);
    const updatedAt = roleQuery.dataUpdatedAt.value;
    if (
      publication.value &&
      lastPublication?.key === key &&
      lastPublication.updatedAt === updatedAt &&
      lastPublication.result === toRaw(result)
    )
      return;
    lastPublication = { key, updatedAt, result: toRaw(result) };
    publication.value = {
      rows: result.items,
      total: result.total,
      displayed: {
        domainKey: domainKey.value,
        revision: ++revision,
        input: {
          query: logicalFilters(submitted.value),
          pager: { page: currentPage.value, size: pageSize.value },
          sort: [],
        },
      },
    };
    const lastPage = Math.max(1, Math.ceil(result.total / pageSize.value));
    if (currentPage.value > lastPage) currentPage.value = lastPage;
  },
  { immediate: true, flush: 'post' }
);
const roleRows = computed(() => publication.value?.rows ?? []);
const pagination = computed(() => ({
  page: currentPage.value,
  size: pageSize.value,
  total: publication.value?.total ?? 0,
}));
const listStatus = computed(() => ({
  loading: roleQuery.isLoading.value,
  refreshing: roleQuery.isFetching.value && publication.value !== null,
  error: roleQuery.error.value,
  paused: roleQuery.fetchStatus.value === 'paused',
}));
const statusOperations = shallowReactive(new Map<number, ReturnType<typeof useOperation>>());
watch(
  queryScope,
  () => {
    draft.value = {};
    submitted.value = {};
    currentPage.value = 1;
    pageSize.value = 10;
    publication.value = null;
    statusOperations.clear();
    clearSelection();
  },
  { flush: 'sync' }
);
function queryIntent(intent: TableQueryIntent<Query>) {
  if (!queryScope.value || intent.domainKey !== domainKey.value) return;
  const next = normalizeRoleFilters(intent.input.query);
  const page = intent.input.pager?.page ?? 1;
  const size = intent.input.pager?.size ?? pageSize.value;
  const unchanged =
    page === currentPage.value &&
    size === pageSize.value &&
    JSON.stringify(next) === JSON.stringify(submitted.value);
  submitted.value = next;
  currentPage.value = page;
  pageSize.value = size;
  if (unchanged) refreshList();
}
function refreshList() {
  if (queryScope.value) void roleQuery.refetch({ cancelRefetch: false });
}
function clearSelection() {
  tableRef.value?.clearSelection();
}
function canEditRole(row: Pick<RoleRecord, 'roleId'>) {
  return row.roleId !== 1 && checkPermi(['system:role:edit']);
}
function handleStatusChange(status: string | number | boolean, row: RoleRecord) {
  const scope = queryScope.value;
  if (!scope || !canEditRole(row) || status === row.status || (status !== '0' && status !== '1'))
    return Promise.resolve();
  const existing = statusOperations.get(row.roleId);
  if (existing) return existing.run();
  const command = captureRoleCommand({ roleId: row.roleId, status } as const, scope);
  const operation = useOperation(async () => {
    try {
      await proxy.$modal.confirm(
        `确认${status === '0' ? '启用' : '停用'}角色“${row.roleName}”吗？`
      );
      if (!canEditRole(row)) return;
      await roleCommands.changeStatus(command);
    } catch {
      // Confirmation cancellation and HTTP feedback leave server-owned rows intact.
    } finally {
      if (statusOperations.get(row.roleId) === operation) statusOperations.delete(row.roleId);
    }
  });
  statusOperations.set(row.roleId, operation);
  return operation.run();
}
function handleAuthUser(row: RoleRecord) {
  if (!canEditRole(row)) return;
  listNavigation.remember('roles', {
    filters: Object.fromEntries(
      Object.entries(submitted.value).filter(
        (entry): entry is [string, string] => typeof entry[1] === 'string'
      )
    ),
    page: currentPage.value,
    size: pageSize.value,
  });
  return router.push('/system/role-auth/user/' + row.roleId);
}
function openRole(id?: number) {
  return roleFormDrawerRef.value?.open(id).catch(() => {
    /* The editor owns read feedback. */
  });
}
function openDataScope(row: RoleRecord) {
  return roleDataScopeDrawerRef.value?.open(row.roleId).catch(() => {
    /* The editor owns read feedback. */
  });
}
const definition = defineTableRender<RoleRecord, Query>()({
  key: 'role-management',
  title: '角色管理',
  rowKey: 'roleId',
  layout: { fill: true, inlineLimit: 3 },
  selection: { mode: 'multiple', selectable: (row) => row.roleId !== 1 },
  pagination: { pageSize: 10 },
  search: [
    { key: 'roleName', label: '角色名称', control: 'text', placement: 'keyword' },
    {
      key: 'roleKey',
      label: '权限字符',
      control: 'text',
      placement: 'inline',
      placeholder: '请输入权限字符',
    },
    {
      key: 'status',
      label: '角色状态',
      control: { slot: 'role-status' },
      placement: 'inline',
      trigger: 'change',
    },
    {
      key: 'dateRange',
      label: '创建日期',
      control: 'date-range',
      placement: 'inline',
      trigger: 'change',
    },
  ],
  columns: [
    { key: 'roleId', label: '角色编号', prop: 'roleId', width: 120 },
    { key: 'roleName', label: '角色名称', prop: 'roleName', minWidth: 150 },
    { key: 'roleKey', label: '权限字符', prop: 'roleKey', minWidth: 150 },
    { key: 'roleSort', label: '显示顺序', prop: 'roleSort', width: 100 },
    { key: 'status', label: '状态', prop: 'status', width: 100 },
    { key: 'createTime', label: '创建时间', prop: 'createTime', type: 'datetime', width: 180 },
    {
      key: 'operations',
      label: '操作',
      type: 'actions',
      fixed: 'right',
      width: 220,
      hideable: false,
    },
  ],
  actions: {
    toolbar: [
      {
        id: 'add',
        label: '新增',
        icon: 'Plus',
        tone: 'primary',
        visible: () => checkPermi(['system:role:add']),
        run: () => openRole(),
      },
      {
        id: 'export',
        label: '导出',
        icon: 'Download',
        visible: () => checkPermi(['system:role:export']),
        run: ({ applied }) =>
          applied &&
          proxy.download(
            'system/role/export',
            normalizeRoleFilters(applied.query),
            `role_${Date.now()}.xlsx`
          ),
      },
    ],
    batch: [
      {
        id: 'edit-selected',
        label: '修改',
        icon: 'Edit',
        visible: () => checkPermi(['system:role:edit']),
        disabled: ({ loadedRows, missingKeys }) =>
          loadedRows.length !== 1 || missingKeys.length > 0 || !canEditRole(loadedRows[0]),
        run: ({ loadedRows }) => openRole(loadedRows[0].roleId),
      },
      {
        id: 'delete-selected',
        label: '删除',
        icon: 'Delete',
        tone: 'danger',
        visible: () => checkPermi(['system:role:remove']),
        disabled: ({ keys }) => keys.some((id) => Number(id) === 1),
        confirm: ({ keys }) => `是否确认删除角色编号为“${keys.join(',')}”的数据项？`,
        run: ({ keys }) => roleCommands.deleteRoles(captureRoleCommand(keys)),
      },
    ],
    row: [
      { id: 'edit', label: '修改', visible: canEditRole, run: (row) => openRole(row.roleId) },
      { id: 'auth-user', label: '分配用户', visible: canEditRole, run: handleAuthUser },
      {
        id: 'data-scope',
        label: '数据权限',
        visible: canEditRole,
        overflow: true,
        run: openDataScope,
      },
      {
        id: 'delete',
        label: '删除',
        tone: 'danger',
        overflow: true,
        visible: (row) => row.roleId !== 1 && checkPermi(['system:role:remove']),
        confirm: (row) => `是否确认删除角色编号为“${row.roleId}”的数据项？`,
        run: (row) => roleCommands.deleteRoles(captureRoleCommand(row.roleId)),
      },
    ],
  },
});
const tableRef = shallowRef<TableRenderInstance<typeof definition, RoleRecord, Query>>();
</script>
