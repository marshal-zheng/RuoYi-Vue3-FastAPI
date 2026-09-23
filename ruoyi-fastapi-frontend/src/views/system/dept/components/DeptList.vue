<template>
  <ZxGridList
    ref="gridListRef"
    :load-data="loadDeptData"
    :show-pagination="false"
    :load-on-mounted="true"
    fill
  >
    <template #form="{ query, loading, refresh: handleRefresh, updateState }">
      <div class="zx-grid-form-bar">
        <div class="zx-grid-form-bar__left">
          <ZxButton type="primary" @click="handleAdd" v-hasPermi="['system:dept:add']"
            >新增</ZxButton
          >
          <ZxButton type="info" @click="toggleExpandAll">展开/折叠</ZxButton>
        </div>
        <div class="zx-grid-form-bar__filters">
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
            @change="(v: any) => onFilterChange('status', v, { handleRefresh, updateState })"
          >
            <el-option
              v-for="dict in sys_normal_disable"
              :key="dict.value"
              :label="dict.label"
              :value="dict.value"
            />
          </el-select>
        </div>
        <div class="zx-grid-form-bar__right">
          <ZxSearch
            v-model="query.deptName"
            placeholder="搜索部门名称"
            :loading="loading"
            search-mode="click"
            @search="() => onSearch({ handleRefresh, updateState })"
            @clear="() => onSearch({ handleRefresh, updateState })"
          />
        </div>
      </div>
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
import { listDept, getDept, delDept } from '@/api/system/dept';
import { parseTime } from '@/utils/ruoyi';
import DeptDlg from './DeptDlg.vue';

const proxy = getCurrentInstance()?.proxy as any;
const { sys_normal_disable } = proxy.useDict('sys_normal_disable');

const isExpandAll = ref(true);
const refreshTable = ref(true);
const gridListRef = ref<any>(null);
const deptDlgRef = ref<any>(null);

async function loadDeptData(params: any) {
  const query = {
    deptName: params.query?.deptName,
    status: params.query?.status,
  };
  try {
    const response = await listDept(query);
    const tree = proxy.handleTree(response.items, 'deptId');
    return { data: tree || [], total: 0 };
  } catch (e) {
    return { data: [], total: 0 };
  }
}

function onFilterChange(field: string, value: any, { handleRefresh, updateState }: any) {
  updateState({ [field]: value });
  handleRefresh();
}

function onSearch({ handleRefresh }: any) {
  handleRefresh();
}

function handleAdd(row?: any) {
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

async function handleUpdate(row: any) {
  const response = await getDept(row.deptId).catch(() => null);
  if (!response) return;
  deptDlgRef.value?.open(response);
}

function handleDelete(row: any) {
  proxy.$modal
    .confirm('是否确认删除名称为"' + row.deptName + '"的数据项?')
    .then(() => delDept(row.deptId))
    .then(() => {
      gridListRef.value?.refresh();
    })
    .catch(() => {});
}

function getMoreActionList(row: any) {
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

function handleMoreActionSelect(item: any, row: any) {
  switch (item.eventTag) {
    case 'delete':
      handleDelete(row);
      break;
    default:
      break;
  }
}
</script>
