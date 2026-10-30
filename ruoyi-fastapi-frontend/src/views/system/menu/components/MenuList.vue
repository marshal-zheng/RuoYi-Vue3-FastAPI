<template>
  <ZxGridList
    ref="gridListRef"
    :load-data="loadMenuData"
    :show-pagination="false"
    :load-on-mounted="true"
    fill
  >
    <template #form="listForm">
      <template v-if="listForm.mode === 'request'">
        <DictStatus :types="['sys_normal_disable']" />
        <ZxListToolbar aria-label="列表操作与筛选">
          <template #actions>
            <ZxButton type="primary" @click="handleAdd" v-hasPermi="['system:menu:add']"
              >新增</ZxButton
            >
            <ZxButton @click="toggleExpandAll">展开/折叠</ZxButton>
          </template>
          <template #filters>
            <zx-input
              v-model="listForm.draft.menuName"
              placeholder="请输入菜单名称"
              clearable
              style="width: 200px"
              @keyup.enter="() => listForm.search()"
            />
            <DictSelect
              dict-type="sys_normal_disable"
              v-model="listForm.draft.status"
              placeholder="菜单状态"
              clearable
              style="width: 200px"
              @change="() => listForm.search()"
            />
          </template>
          <template #search>
            <ZxSearch
              v-model="listForm.draft.menuName"
              placeholder="搜索菜单名称"
              :loading="listForm.loading"
              search-mode="click"
              @search="() => listForm.search()"
              @clear="() => listForm.search()"
            />
          </template>
        </ZxListToolbar>
      </template>
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
            <ZxIcon
              v-if="scope.row.icon"
              :icon="resolveNavigationIcon(scope.row.icon)"
              :size="16"
            />
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
                :list="getMoreActionList()"
                @select="handleMoreActionSelect($event, scope.row)"
              />
            </div>
          </template>
        </el-table-column>
      </el-table>
    </template>
  </ZxGridList>

  <MenuDrawer ref="menuDrawerRef" @success="gridListRef?.reload()" />
</template>

<script setup lang="ts" name="MenuList">
import { ZxGridList } from '@zxio/zxui/grid-list';
import { useOperation } from '@/utils/operation';
import { resolveNavigationIcon } from '@/icons/navigation';
import type {
  GridListPagerState,
  GridListSortItem,
  ZxGridListRequestInstance,
  ActionItem,
} from '@zxio/zxui';
import type { MenuRecord } from '@/api/system/menu';
import type { GetSystemMenuListSystemMenuListGetData } from '@/api/_generated/types.gen';
type ListQuery = NonNullable<GetSystemMenuListSystemMenuListGetData['query']> & {
  dateRange?: string[] | null;
};
type ListLoadParams = {
  query?: ListQuery;
  pager?: GridListPagerState;
  sort?: readonly GridListSortItem[];
};
import { ref, nextTick, getCurrentInstance } from 'vue';
import { listMenu, delMenu } from '@/api/system/menu';
import MenuDrawer from './MenuDrawer.vue';

const proxy = getCurrentInstance()!.proxy!;
const { sys_normal_disable } = proxy.useDict('sys_normal_disable');
const { parseTime } = proxy;

const isExpandAll = ref(false);
const refreshTable = ref(true);
const gridListRef = ref<ZxGridListRequestInstance | null>(null);
const menuDrawerRef = ref<InstanceType<typeof MenuDrawer> | null>(null);

async function loadMenuData(params: ListLoadParams) {
  const query = {
    sort: params.sort,
    menuName: params.query?.menuName,
    status: params.query?.status,
  };
  const response = await listMenu(query);
  const tree = proxy.handleTree(response.items, 'menuId');
  return { data: tree || [], total: 0 };
}

function handleAdd(row?: MenuRecord) {
  const data = row?.menuId ? { parentId: row.menuId } : {};
  return menuDrawerRef.value?.open(data).catch(() => {
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

function handleUpdate(row: MenuRecord) {
  return menuDrawerRef.value?.open({ menuId: row.menuId }).catch(() => {
    /* 当前读取已负责反馈。 */
  });
}

const { run: handleDelete } = useOperation(async (row: MenuRecord) => {
  await proxy.$modal
    .confirm('是否确认删除名称为"' + row.menuName + '"的数据项?')
    .then(() => delMenu(row.menuId))
    .then(() => {
      gridListRef.value?.reload();
    })
    .catch(() => {});
});

function getMoreActionList() {
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

function handleMoreActionSelect(item: ActionItem, row: MenuRecord) {
  switch (item.eventTag) {
    case 'delete':
      handleDelete(row);
      break;
    default:
      break;
  }
}
</script>
