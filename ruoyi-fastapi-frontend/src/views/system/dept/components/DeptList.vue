<template>
  <ZxGridList
    v-if="queryScope"
    :key="queryScope.key"
    mode="controlled"
    :rows="deptRows"
    :status="listStatus"
    :show-pagination="false"
    fill
    @refresh="refreshList"
  >
    <template #form>
      <DictStatus :types="['sys_normal_disable']" />
      <ZxListToolbar aria-label="列表操作与筛选">
        <template #actions>
          <ZxButton type="primary" @click="handleAdd" v-hasPermi="['system:dept:add']"
            >新增</ZxButton
          >
          <ZxButton type="info" @click="toggleExpandAll">展开/折叠</ZxButton>
        </template>
        <template #filters>
          <zx-input
            v-model="draft.deptName"
            placeholder="请输入部门名称"
            clearable
            style="width: 200px"
            @keyup.enter="onSearch"
          />
          <DictSelect
            dict-type="sys_normal_disable"
            v-model="draft.status"
            placeholder="部门状态"
            clearable
            style="width: 200px"
            @change="onSearch"
          />
        </template>
        <template #search>
          <ZxSearch
            v-model="draft.deptName"
            placeholder="搜索部门名称"
            :loading="listStatus.loading"
            search-mode="click"
            @search="onSearch"
            @clear="onSearch"
          />
        </template>
      </ZxListToolbar>
    </template>

    <template #table="{ grid, renderEmpty }">
      <el-table
        v-if="refreshTable"
        :data="grid.list || []"
        row-key="deptId"
        :default-expand-all="isExpandAll"
        :tree-props="{ children: 'children', hasChildren: 'hasChildren' }"
      >
        <template #empty>
          <component :is="renderEmpty" />
        </template>
        <el-table-column prop="deptName" label="部门名称"></el-table-column>
        <el-table-column prop="orderNum" label="排序"></el-table-column>
        <el-table-column prop="status" label="状态">
          <template #default="scope">
            <dict-tag :options="sys_normal_disable" :value="scope.row.status" />
          </template>
        </el-table-column>
        <el-table-column label="创建时间" prop="createTime" width="200">
          <template #default="scope">
            <span>{{ parseTime(scope.row.createTime) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" class-name="small-padding fixed-width">
          <template #default="scope">
            <div class="op-col__wrap">
              <zx-button
                link
                type="primary"
                @click="handleUpdate(scope.row)"
                v-hasPermi="['system:dept:edit']"
                >修改</zx-button
              >
              <zx-button
                link
                type="primary"
                @click="handleAdd(scope.row)"
                v-hasPermi="['system:dept:add']"
                >新增</zx-button
              >
              <ZxMoreAction
                v-if="scope.row.parentId != 0"
                :list="getMoreActionList(scope.row)"
                @select="handleMoreActionSelect($event, scope.row)"
              />
            </div>
          </template>
        </el-table-column>
      </el-table>
    </template>
  </ZxGridList>

  <DeptDlg ref="deptDlgRef" />
</template>

<script setup lang="ts" name="DeptList">
import { computed, getCurrentInstance, nextTick, reactive, ref, watch } from 'vue';
import { useQuery } from '@tanstack/vue-query';
import type { ActionItem } from '@zxio/zxui';
import type { DeptRecord } from '@/api/system/dept';
import { useOperation } from '@/utils/operation';
import { handleTree, parseTime } from '@/utils/ruoyi';
import { queryScope, type QueryScope } from '@/queries/context';
import {
  captureDeptCommand,
  deptCommands,
  deptListOptions,
  normalizeDeptFilters,
} from '@/queries/system/dept';
import DeptDlg from './DeptDlg.vue';

const proxy = getCurrentInstance()!.proxy!;
const { sys_normal_disable } = proxy.useDict('sys_normal_disable');
const isExpandAll = ref(true);
const refreshTable = ref(true);
const deptDlgRef = ref<InstanceType<typeof DeptDlg> | null>(null);
const draft = reactive<{ deptName?: string; status?: '0' | '1' }>({});
const submitted = ref(normalizeDeptFilters({}));
const departmentQuery = useQuery(() => deptListOptions(queryScope.value, submitted.value));
// handleTree attaches children in place; native cache records stay flat and immutable.
const deptRows = computed(() =>
  handleTree(
    (departmentQuery.data.value?.items ?? []).map((row) => ({ ...row })),
    'deptId'
  )
);
const listStatus = computed(() => ({
  loading: departmentQuery.isLoading.value,
  refreshing: departmentQuery.isFetching.value && departmentQuery.data.value !== undefined,
  error: departmentQuery.error.value,
  paused: departmentQuery.fetchStatus.value === 'paused',
}));
watch(
  queryScope,
  () => {
    draft.deptName = undefined;
    draft.status = undefined;
    submitted.value = normalizeDeptFilters({});
  },
  { flush: 'sync' }
);

function onSearch() {
  const nextFilters = normalizeDeptFilters(draft);
  const unchanged =
    Object.keys(nextFilters).length === Object.keys(submitted.value).length &&
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
  refreshTable.value = false;
  isExpandAll.value = !isExpandAll.value;
  nextTick(() => {
    refreshTable.value = true;
  });
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
