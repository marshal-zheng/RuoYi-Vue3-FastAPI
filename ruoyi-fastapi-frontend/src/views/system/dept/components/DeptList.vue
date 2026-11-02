<template>
  <ZxTableRender
    v-if="queryScope"
    ref="refTable"
    v-model:query="draft"
    :definition="definition"
    :domain-key="resourceList.domainKey.value"
    :applied="resourceList.applied.value"
    :displayed="resourceList.displayed.value"
    :rows="deptRows"
    :status="resourceList.status.value"
    @query-intent="resourceList.onQueryIntent"
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
  <el-alert v-if="deleteError" :title="deleteError" type="error" :closable="false" />
  <DeptDlg ref="deptDlgRef" />
</template>

<script setup lang="ts" name="DeptList">
import { defineTableRender } from '@zxio/table-render/core';
import { ZxTableRender } from '@zxio/table-render/ui';
import '@zxio/table-render/style';
import type { TableRenderInstance } from '@zxio/table-render/ui';
import { computed, getCurrentInstance, ref, shallowRef } from 'vue';
import { useResourceCommand, useResourceList } from '@zxio/vue-query/ui';
import type { ActionItem } from '@zxio/zxui';
import { ElMessage } from 'element-plus';
import type { DeptRecord } from '@/api/system/dept';
import { dataClient } from '@/queries/client';
import { handleTree } from '@/utils/ruoyi';
import { queryScope } from '@/queries/context';
import { departmentResource, normalizeDeptFilters, type DeptFilters } from '@/queries/system/dept';
import DeptDlg from './DeptDlg.vue';

const proxy = getCurrentInstance()!.proxy!;
const { sys_normal_disable } = proxy.useDict('sys_normal_disable');
type DeptRow = DeptRecord & { children?: DeptRow[] };
const deptDlgRef = ref<InstanceType<typeof DeptDlg> | null>(null);
const draft = ref<DeptFilters>({});
const resourceList = useResourceList(departmentResource, 'list', {
  client: dataClient,
  initialInput: { query: {} as DeptFilters, pager: null, sort: [] },
  input: (input) => normalizeDeptFilters(input.query),
  project: (data, input) => ({
    // handleTree mutates its argument; rows belong to this table, never the shared cache.
    rows: handleTree(
      data.items.map((row) => ({ ...row })),
      'deptId'
    ) as DeptRow[],
    pagination: {
      page: 1,
      size: Math.max(1, data.items.length),
      total: data.items.length,
    },
    logicalInput: { ...input, query: normalizeDeptFilters(input.query) },
  }),
});
const deptRows = resourceList.rows;
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

const deleteCommand = useResourceCommand(departmentResource, 'delete', {
  client: dataClient,
  beforeExecute: async (id) => {
    try {
      await proxy.$modal.confirm(`是否确认删除部门（ID ${id}）？`);
      return true;
    } catch {
      return false;
    }
  },
});
const deleteError = computed(() => {
  const receipt = deleteCommand.receipt.value;
  if (receipt?.kind === 'unknown') return '删除结果未确认，请刷新核对，勿重复删除。';
  if (receipt?.kind === 'rejected')
    return receipt.error instanceof Error ? receipt.error.message : '删除被拒绝';
  return '';
});
async function handleDelete(row: DeptRecord) {
  const receipt = await deleteCommand.run(row.deptId);
  if (receipt?.kind !== 'succeeded' || !receipt.applicable) return;
  const refresh = await receipt.refresh;
  if (!dataClient.isCurrent(receipt.scope)) return;
  if (refresh.kind === 'failed' || refresh.kind === 'paused')
    ElMessage.warning('删除已成功，部分数据未刷新，请重试读取。');
  else ElMessage.success('删除成功');
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
