<template>
  <ZxGridList
    ref="gridListRef"
    :load-data="loadMenuData"
    :show-pagination="false"
    :load-on-mounted="true"
    class="zx-grid-list--page"
  >
    <template #form="{ query, loading, refresh: handleRefresh, updateState }">
      <div class="zx-grid-form-bar">
        <div class="zx-grid-form-bar__left">
          <ZxButton type="primary" @click="handleAdd" v-hasPermi="['system:menu:add']"
            >新增</ZxButton
          >
          <ZxButton type="info" @click="toggleExpandAll">展开/折叠</ZxButton>
        </div>
        <div class="zx-grid-form-bar__filters">
          <el-input
            v-model="query.menuName"
            placeholder="请输入菜单名称"
            clearable
            style="width: 200px"
            @keyup.enter="() => onSearch({ handleRefresh, updateState })"
          />
          <el-select
            v-model="query.status"
            placeholder="菜单状态"
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
            v-model="query.menuName"
            placeholder="搜索菜单名称"
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
        row-key="menuId"
        :default-expand-all="isExpandAll"
        :tree-props="{ children: 'children', hasChildren: 'hasChildren' }"
      >
        <el-table-column
          prop="menuName"
          label="菜单名称"
          :show-overflow-tooltip="true"
          width="160"
        ></el-table-column>
        <el-table-column prop="icon" label="图标" align="center" width="100">
          <template #default="scope">
            <ZxIcon v-if="scope.row.icon" :icon="scope.row.icon" :size="16" />
          </template>
        </el-table-column>
        <el-table-column prop="orderNum" label="排序" width="60"></el-table-column>
        <el-table-column
          prop="perms"
          label="权限标识"
          :show-overflow-tooltip="true"
        ></el-table-column>
        <el-table-column
          prop="component"
          label="组件路径"
          :show-overflow-tooltip="true"
        ></el-table-column>
        <el-table-column prop="status" label="状态" width="80">
          <template #default="scope">
            <dict-tag :options="sys_normal_disable" :value="scope.row.status" />
          </template>
        </el-table-column>
        <el-table-column label="创建时间" align="center" width="160" prop="createTime">
          <template #default="scope">
            <span>{{ parseTime(scope.row.createTime) }}</span>
          </template>
        </el-table-column>
        <el-table-column
          label="操作"
          align="center"
          width="210"
          class-name="small-padding fixed-width"
        >
          <template #default="scope">
            <div class="op-col__wrap">
              <zx-button
                link
                type="primary"
                @click="handleUpdate(scope.row)"
                v-hasPermi="['system:menu:edit']"
                >修改</zx-button
              >
              <zx-button
                link
                type="primary"
                @click="handleAdd(scope.row)"
                v-hasPermi="['system:menu:add']"
                >新增</zx-button
              >
              <ZxMoreAction
                :list="getMoreActionList(scope.row)"
                @select="handleMoreActionSelect($event, scope.row)"
              />
            </div>
          </template>
        </el-table-column>
      </el-table>
    </template>
  </ZxGridList>

  <MenuDrawer
    ref="menuDrawerRef"
    :sys-show-hide="sys_show_hide"
    :sys-normal-disable="sys_normal_disable"
    @success="gridListRef?.refresh()"
  />
</template>

<script setup lang="ts" name="MenuList">
import { ref, nextTick, getCurrentInstance } from 'vue';
import { listMenu, getMenu, delMenu } from '@/api/system/menu';
import MenuDrawer from './MenuDrawer.vue';

const { proxy } = getCurrentInstance()!;
const { sys_normal_disable, sys_show_hide } = (proxy as any).useDict(
  'sys_normal_disable',
  'sys_show_hide'
);
const { parseTime } = proxy as any;

const isExpandAll = ref(false);
const refreshTable = ref(true);
const gridListRef = ref<InstanceType<(typeof import('@zxio/zxui'))['ZxGridList']> | null>(null);
const menuDrawerRef = ref<InstanceType<typeof MenuDrawer> | null>(null);

async function loadMenuData(params: any) {
  const query = {
    menuName: params.query?.menuName,
    status: params.query?.status,
  };
  try {
    const response = await listMenu(query);
    const tree = (proxy as any).handleTree(response, 'menuId');
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
  const data = row?.menuId ? { parentId: row.menuId } : {};
  menuDrawerRef.value?.open(data);
}

function toggleExpandAll() {
  refreshTable.value = false;
  isExpandAll.value = !isExpandAll.value;
  nextTick(() => {
    refreshTable.value = true;
  });
}

async function handleUpdate(row: any) {
  const response = await getMenu(row.menuId).catch(() => null);
  if (!response) return;
  menuDrawerRef.value?.open(response);
}

function handleDelete(row: any) {
  (proxy as any).$modal
    .confirm('是否确认删除名称为"' + row.menuName + '"的数据项?')
    .then(() => delMenu(row.menuId))
    .then(() => {
      gridListRef.value?.refresh();
    })
    .catch(() => {});
}

function getMoreActionList(_row: any) {
  const actions = [];
  actions.push({
    label: '删除',
    eventTag: 'delete',
    icon: 'Delete',
    danger: true,
    permission: 'system:menu:remove',
  });
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
