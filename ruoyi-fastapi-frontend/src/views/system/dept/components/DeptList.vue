<template>
  <ZxGridList
    ref="gridListRef"
    :load-data="loadDeptData"
    :show-pagination="false"
    :load-on-mounted="true"
    fill
  >
    <template #form="{ query, loading, refresh: handleRefresh, updateState }">
      <ZxListToolbar aria-label="列表操作与筛选">
        <template #actions>
          <ZxButton type="primary" @click="handleAdd" v-hasPermi="['system:dept:add']"
            >新增</ZxButton
          >
          <ZxButton type="info" @click="toggleExpandAll">展开/折叠</ZxButton>
        </template>
        <template #filters>
          <zx-input
            v-model="query.deptName"
            placeholder="请输入部门名称"
            clearable
            style="width: 200px"
            @keyup.enter="() => onSearch({ handleRefresh, updateState })"
          />
          <el-select
            v-model="query.status"
            placeholder="部门状态"
            clearable
            style="width: 200px"
            @change="(v: unknown) => onFilterChange('status', v, { handleRefresh, updateState })"
          >
            <el-option
              v-for="dict in sys_normal_disable"
              :key="dict.value"
              :label="dict.label"
              :value="dict.value"
            />
          </el-select>
        </template>
        <template #search>
          <ZxSearch
            v-model="query.deptName"
            placeholder="搜索部门名称"
            :loading="loading"
            search-mode="click"
            @search="() => onSearch({ handleRefresh, updateState })"
            @clear="() => onSearch({ handleRefresh, updateState })"
          />
        </template>
      </ZxListToolbar>
    </template>

    <template #table="{ grid }">
      <el-table
        v-if="refreshTable"
        v-loading="grid.loading"
        :data="grid.list || []"
        row-key="deptId"
        :default-expand-all="isExpandAll"
        :tree-props="{ children: 'children', hasChildren: 'hasChildren' }"
      >
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

  <DeptDlg ref="deptDlgRef" @success="gridListRef?.refresh()" />
</template>

<script setup lang="ts" name="DeptList">
import { getCurrentInstance, ref, nextTick } from 'vue';
import type { GridListState, ZxGridListInstance, ActionItem } from '@zxio/zxui';
import type { DeptRecord } from '@/api/system/dept';
import type { DeptQueryModel } from '@/api/_generated/types.gen';
type ListQuery = DeptQueryModel & { dateRange?: string[] | null };
type ListLoadParams = Partial<Pick<GridListState<ListQuery, never>, 'query' | 'pager'>>;
type ListActions = {
  handleRefresh: ZxGridListInstance['refresh'];
  updateState: ZxGridListInstance['updateState'];
};
import { listDept, getDept, delDept } from '@/api/system/dept';
import { parseTime } from '@/utils/ruoyi';
import DeptDlg from './DeptDlg.vue';

const proxy = getCurrentInstance()!.proxy!;
const { sys_normal_disable } = proxy.useDict('sys_normal_disable');

const isExpandAll = ref(true);
const refreshTable = ref(true);
const gridListRef = ref<ZxGridListInstance | null>(null);
const deptDlgRef = ref<InstanceType<typeof DeptDlg> | null>(null);

async function loadDeptData(params: ListLoadParams) {
  const query = {
    deptName: params.query?.deptName,
    status: params.query?.status,
  };
  try {
    const response = await listDept(query);
    const tree = proxy.handleTree(response.items, 'deptId');
    return { data: tree || [], total: 0 };
  } catch {
    return { data: [], total: 0 };
  }
}

function onFilterChange(
  field: string,
  value: unknown,
  { handleRefresh, updateState }: ListActions
) {
  updateState(`query.${field}`, value);
  handleRefresh();
}

function onSearch({
  handleRefresh,
}: {
  handleRefresh: ListActions['handleRefresh'];
  updateState?: ListActions['updateState'];
}) {
  handleRefresh();
}

function handleAdd(row?: DeptRecord) {
  const data = row ? { parentId: row.deptId } : {};
  deptDlgRef.value?.open(data);
}

function toggleExpandAll() {
  refreshTable.value = false;
  isExpandAll.value = !isExpandAll.value;
  nextTick(() => {
    refreshTable.value = true;
  });
}

async function handleUpdate(row: DeptRecord) {
  const response = await getDept(row.deptId).catch(() => null);
  if (!response) return;
  deptDlgRef.value?.open({
    deptId: response.deptId ?? undefined,
    parentId: response.parentId ?? undefined,
    deptName: response.deptName ?? undefined,
    orderNum: response.orderNum ?? undefined,
    leader: response.leader ?? undefined,
    phone: response.phone ?? undefined,
    email: response.email ?? undefined,
    status: response.status ?? undefined,
  });
}

function handleDelete(row: DeptRecord) {
  proxy.$modal
    .confirm('是否确认删除名称为"' + row.deptName + '"的数据项?')
    .then(() => delDept(row.deptId))
    .then(() => {
      gridListRef.value?.refresh();
    })
    .catch(() => {});
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
  switch (item.eventTag) {
    case 'delete':
      handleDelete(row);
      break;
    default:
      break;
  }
}
</script>
