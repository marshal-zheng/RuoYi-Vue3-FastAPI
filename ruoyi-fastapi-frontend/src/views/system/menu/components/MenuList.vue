<template>
  <ZxTableRender ref="tableRef" :definition="definition" :query-context="gridQueryContext">
    <template #toolbar-extra>
      <DictStatus :types="['sys_normal_disable']" />
      <ZxButton @click="toggleExpandAll">展开/折叠</ZxButton>
    </template>
    <template #menu-status="{ logicalValue, commit, controlAttrs }">
      <DictSelect
        dict-type="sys_normal_disable"
        :model-value="logicalValue"
        v-bind="controlAttrs"
        placeholder="菜单状态"
        clearable
        @update:model-value="commit"
      />
    </template>
    <template #cell-icon="{ row }"
      ><ZxIcon v-if="row.icon" :icon="resolveNavigationIcon(row.icon)" :size="16"
    /></template>
    <template #cell-status="{ row }"
      ><dict-tag :options="sys_normal_disable" :value="row.status ?? undefined"
    /></template>
  </ZxTableRender>
  <MenuDrawer ref="menuDrawerRef" @success="tableRef?.reload()" />
</template>

<script setup lang="ts" name="MenuList">
import { getCurrentInstance, shallowRef } from 'vue';
import { defineTableRender } from '@zxio/table-render/core';
import { ZxTableRender, type TableRenderInstance } from '@zxio/table-render/ui';
import '@zxio/table-render/style';
import { listMenu, delMenu, type MenuRecord } from '@/api/system/menu';
import { gridQueryContext, requireQueryScope, scopeRequestOptions } from '@/queries/context';
import { checkPermi } from '@/utils/permission';
import { handleTree } from '@/utils/ruoyi';
import { resolveNavigationIcon } from '@/icons/navigation';
import DictSelect from '@/components/business/DictSelect/index.vue';
import MenuDrawer from './MenuDrawer.vue';

type MenuRow = MenuRecord & { children?: MenuRow[] };
type Query = { menuName?: string; status?: '0' | '1' };
const proxy = getCurrentInstance()!.proxy!;
const { sys_normal_disable } = proxy.useDict('sys_normal_disable');
const menuDrawerRef = shallowRef<InstanceType<typeof MenuDrawer>>();
const expandableKeys = shallowRef<number[]>([]);
function open(data: { menuId?: number; parentId?: number } = {}) {
  return menuDrawerRef.value?.open(data).catch(() => {
    /* The editor owns read feedback. */
  });
}
const definition = defineTableRender<MenuRow, Query>()({
  key: 'menu-management',
  title: '菜单管理',
  rowKey: 'menuId',
  pagination: false,
  tree: { children: 'children' },
  layout: { fill: true },
  search: [
    { key: 'menuName', label: '菜单名称', control: 'text', placement: 'keyword' },
    {
      key: 'status',
      label: '菜单状态',
      control: { slot: 'menu-status' },
      placement: 'inline',
      trigger: 'change',
    },
  ],
  columns: [
    { key: 'menuName', label: '菜单名称', prop: 'menuName', minWidth: 220, hideable: false },
    { key: 'icon', label: '图标', prop: 'icon', align: 'center', width: 80 },
    { key: 'orderNum', label: '排序', prop: 'orderNum', width: 80 },
    { key: 'perms', label: '权限标识', prop: 'perms', minWidth: 180 },
    { key: 'component', label: '组件路径', prop: 'component', minWidth: 180 },
    { key: 'status', label: '状态', prop: 'status', width: 100 },
    { key: 'createTime', label: '创建时间', prop: 'createTime', type: 'datetime', width: 180 },
    {
      key: 'operations',
      label: '操作',
      type: 'actions',
      fixed: 'right',
      width: 210,
      hideable: false,
    },
  ],
  request: async ({ query }, { signal }) => {
    const response = await listMenu(query, {
      signal,
      requestOptions: scopeRequestOptions(requireQueryScope()),
    });
    const tree: MenuRow[] = handleTree(
      response.items.map((row) => ({ ...row })),
      'menuId'
    );
    if (!signal.aborted) {
      const keys: number[] = [];
      function visit(rows: MenuRow[]) {
        for (const row of rows)
          if (row.children?.length) {
            keys.push(row.menuId);
            visit(row.children);
          }
      }
      visit(tree);
      expandableKeys.value = keys;
    }
    return { list: tree };
  },
  actions: {
    toolbar: [
      {
        id: 'add',
        label: '新增',
        tone: 'primary',
        visible: () => checkPermi(['system:menu:add']),
        run: () => open(),
      },
    ],
    row: [
      {
        id: 'edit',
        label: '修改',
        visible: () => checkPermi(['system:menu:edit']),
        run: (row) => open({ menuId: row.menuId }),
      },
      {
        id: 'add-child',
        label: '新增',
        visible: () => checkPermi(['system:menu:add']),
        run: (row) => open({ parentId: row.menuId }),
      },
      {
        id: 'delete',
        label: '删除',
        tone: 'danger',
        overflow: true,
        visible: () => checkPermi(['system:menu:remove']),
        confirm: (row) => `是否确认删除名称为“${row.menuName}”的数据项？`,
        run: (row) => delMenu(row.menuId),
        reloadAfter: true,
      },
    ],
  },
});
const tableRef = shallowRef<TableRenderInstance<typeof definition, MenuRow, Query>>();
function toggleExpandAll() {
  const expanded = tableRef.value?.expandedKeys ?? [];
  tableRef.value?.setExpandedKeys(
    expandableKeys.value.every((key) => expanded.includes(key)) ? [] : expandableKeys.value
  );
}
</script>
