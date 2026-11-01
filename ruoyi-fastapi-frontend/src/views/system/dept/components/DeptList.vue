<template>
  <ZxTableRender
    v-if="queryScope"
    ref="refTable"
    v-model:query="draft"
    :definition="definition"
    :domain-key="domainKey"
    :applied="applied"
    :displayed="publication?.displayed ?? null"
    :rows="deptRows"
    :status="listStatus"
    @query-intent="queryIntent"
  >
    <template #toolbar-extra>
      <DictStatus :types="['sys_normal_disable']" />
      <ZxButton type="primary" @click="handleAdd()" v-hasPermi="['system:dept:add']">新增</ZxButton>
      <ZxButton @click="toggleExpandAll">展开/折叠</ZxButton>
    </template>
    <template #department-status="{ logicalValue, commit, controlAttrs }">
      <DictSelect
        dict-type="sys_normal_disable"
        :model-value="logicalValue"
        v-bind="controlAttrs"
        placeholder="部门状态"
        clearable
        style="width: 200px"
        @update:model-value="commit"
      />
    </template>
    <template #cell-status="{ row }"
      ><dict-tag :options="sys_normal_disable" :value="row.status ?? undefined"
    /></template>
    <template #cell-operations="{ row }">
      <div class="op-col__wrap">
        <zx-button link type="primary" @click="handleUpdate(row)" v-hasPermi="['system:dept:edit']"
          >修改</zx-button
        >
        <zx-button link type="primary" @click="handleAdd(row)" v-hasPermi="['system:dept:add']"
          >新增</zx-button
        >
        <ZxMoreAction
          v-if="row.parentId != 0"
          :list="getMoreActionList(row)"
          @select="handleMoreActionSelect($event, row)"
        />
      </div>
    </template>
  </ZxTableRender>
  <DeptDlg ref="deptDlgRef" />
</template>

<script setup lang="ts" name="DeptList">
import { defineTableRender } from '@zxio/table-render/core';
import { ZxTableRender } from '@zxio/table-render/ui';
import '@zxio/table-render/style';
import type { TableApplied, TableDisplayed, TableQueryIntent } from '@zxio/table-render/core';
import type { TableRenderInstance } from '@zxio/table-render/ui';
import { queryClient } from '@/queries/client';
import { computed, getCurrentInstance, ref, shallowRef, toRaw, watch } from 'vue';
import { useQuery } from '@tanstack/vue-query';
import type { ActionItem } from '@zxio/zxui';
import type { DeptRecord } from '@/api/system/dept';
import { useOperation } from '@/utils/operation';
import { handleTree } from '@/utils/ruoyi';
import { queryScope, type QueryScope } from '@/queries/context';
import {
  captureDeptCommand,
  deptCommands,
  deptListOptions,
  normalizeDeptFilters,
  type DeptFilters,
} from '@/queries/system/dept';
import DeptDlg from './DeptDlg.vue';

const proxy = getCurrentInstance()!.proxy!;
const { sys_normal_disable } = proxy.useDict('sys_normal_disable');
type DeptRow = DeptRecord & { children?: DeptRow[] };
const deptDlgRef = ref<InstanceType<typeof DeptDlg> | null>(null);
const draft = ref<DeptFilters>({});
const submitted = ref(normalizeDeptFilters({}));
const queryOptions = computed(() => deptListOptions(queryScope.value, submitted.value));
const departmentQuery = useQuery(queryOptions);
const domainKey = computed(() => queryScope.value?.key ?? 'unavailable');
const applied = computed<TableApplied<DeptFilters> | null>(() =>
  queryScope.value
    ? {
        domainKey: domainKey.value,
        query: submitted.value,
        pager: null,
        sort: [],
      }
    : null
);
const publication = shallowRef<{
  rows: DeptRow[];
  displayed: TableDisplayed<DeptFilters>;
} | null>(null);
let revision = 0;
let lastPublication: { key: string; updatedAt: number; result: unknown } | undefined;
watch(
  [departmentQuery.data, departmentQuery.dataUpdatedAt, queryOptions],
  ([result]) => {
    if (
      !result ||
      !applied.value ||
      toRaw(queryClient.getQueryData(queryOptions.value.queryKey)) !== toRaw(result)
    )
      return;
    const key = JSON.stringify([domainKey.value, queryOptions.value.queryKey]);
    const updatedAt = departmentQuery.dataUpdatedAt.value;
    if (
      publication.value &&
      lastPublication?.key === key &&
      lastPublication.updatedAt === updatedAt &&
      lastPublication.result === toRaw(result)
    )
      return;
    lastPublication = { key, updatedAt, result: toRaw(result) };
    // handleTree attaches children in place; native cache records stay flat and immutable.
    publication.value = {
      rows: handleTree(
        result.items.map((row) => ({ ...row })),
        'deptId'
      ),
      displayed: {
        domainKey: domainKey.value,
        revision: ++revision,
        input: { query: { ...submitted.value }, pager: null, sort: [] },
      },
    };
  },
  { immediate: true, flush: 'post' }
);
const deptRows = computed(() => publication.value?.rows ?? []);
const listStatus = computed(() => ({
  loading: departmentQuery.isLoading.value,
  refreshing: departmentQuery.isFetching.value && publication.value !== null,
  error: departmentQuery.error.value,
  paused: departmentQuery.fetchStatus.value === 'paused',
}));
const definition = defineTableRender<DeptRow, DeptFilters>()({
  key: 'department-management',
  title: '部门管理',
  rowKey: 'deptId',
  pagination: false,
  tree: { children: 'children', defaultExpandAll: true },
  layout: { fill: true },
  search: [
    {
      key: 'deptName',
      label: '部门名称',
      control: 'text',
      placement: 'keyword',
      toLogical: (value) => String(value ?? '').trim() || undefined,
    },
    {
      key: 'status',
      label: '部门状态',
      control: { slot: 'department-status' },
      placement: 'inline',
      trigger: 'change',
    },
  ],
  columns: [
    {
      key: 'deptName',
      label: '部门名称',
      prop: 'deptName',
      minWidth: 200,
      hideable: false,
    },
    { key: 'orderNum', label: '排序', prop: 'orderNum', width: 90 },
    { key: 'status', label: '状态', prop: 'status', width: 100 },
    {
      key: 'createTime',
      label: '创建时间',
      prop: 'createTime',
      type: 'datetime',
      width: 200,
    },
    {
      key: 'operations',
      label: '操作',
      type: 'custom',
      width: 200,
      fixed: 'right',
      hideable: false,
    },
  ],
});
const refTable = shallowRef<TableRenderInstance<typeof definition, DeptRow, DeptFilters>>();
watch(
  queryScope,
  () => {
    draft.value = {};
    submitted.value = normalizeDeptFilters({});
    publication.value = null;
  },
  { flush: 'sync' }
);
function queryIntent(intent: TableQueryIntent<DeptFilters>) {
  if (!queryScope.value || intent.domainKey !== domainKey.value) return;
  const nextFilters = normalizeDeptFilters(intent.input.query);
  const unchanged =
    nextFilters.deptName === submitted.value.deptName &&
    nextFilters.status === submitted.value.status;
  submitted.value = nextFilters;
  if (unchanged) refreshList();
}
function refreshList() {
  if (queryScope.value) void departmentQuery.refetch({ cancelRefetch: false });
}
function handleAdd(row?: DeptRecord) {
  const data = row ? { parentId: row.deptId } : {};
  return deptDlgRef.value?.open(data).catch(() => {
    /* 当前读取已负责反馈。 */
  });
}
function toggleExpandAll() {
  const keys: number[] = [];
  function visit(rows: readonly DeptRow[]) {
    for (const row of rows) {
      if (row.children?.length) {
        keys.push(row.deptId);
        visit(row.children);
      }
    }
  }
  visit(deptRows.value);
  const expanded = refTable.value?.expandedKeys ?? [];
  refTable.value?.setExpandedKeys(keys.every((key) => expanded.includes(key)) ? [] : keys);
}
function handleUpdate(row: DeptRecord) {
  return deptDlgRef.value?.open({ deptId: row.deptId }).catch(() => {
    /* 当前读取已负责反馈。 */
  });
}

const deleteOperation = useOperation(async (id: number, name: string, scope: QueryScope) => {
  const command = captureDeptCommand(id, scope);
  try {
    await proxy.$modal.confirm('是否确认删除名称为"' + name + '"的数据项?');
    await deptCommands.deleteDept(command);
  } catch {
    // Confirmation cancellation and write errors leave the server-owned rows intact.
  }
});
function handleDelete(row: DeptRecord) {
  const scope = queryScope.value;
  if (!scope) return;
  return deleteOperation.run(row.deptId, row.deptName ?? '', scope);
}
function getMoreActionList(row: DeptRecord) {
  const actions = [];
  if (row.parentId != 0) {
    actions.push({
      label: '删除',
      eventTag: 'delete',
      icon: 'Delete',
      danger: true,
      permission: 'system:dept:remove',
    });
  }
  return actions;
}
function handleMoreActionSelect(item: ActionItem, row: DeptRecord) {
  if (item.eventTag === 'delete') return handleDelete(row);
  return undefined;
}
</script>
