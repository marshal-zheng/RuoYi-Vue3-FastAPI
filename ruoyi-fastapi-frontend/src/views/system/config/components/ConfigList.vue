<template>
  <ZxTableRender ref="tableRef" :definition="definition" :query-context="gridQueryContext">
    <template #toolbar-extra><DictStatus :types="['sys_yes_no']" /></template>
    <template #config-type="{ logicalValue, commit, controlAttrs }">
      <DictSelect
        dict-type="sys_yes_no"
        :model-value="logicalValue ?? undefined"
        v-bind="controlAttrs"
        placeholder="系统内置"
        clearable
        @update:model-value="commit"
      />
    </template>
    <template #cell-configType="{ row }"
      ><dict-tag :options="sys_yes_no" :value="row.configType ?? undefined"
    /></template>
    <template #cell-remark="{ row }"
      ><RemarkDisplay :value="row.remark" :text="row.remarkText" summary
    /></template>
  </ZxTableRender>
  <ConfigDlg ref="configDlgRef" @confirm="tableRef?.reload()" />
</template>

<script setup lang="ts">
import { getCurrentInstance, shallowRef } from 'vue';
import { defineTableRender } from '@zxio/table-render/core';
import { ZxTableRender, type TableRenderInstance } from '@zxio/table-render/ui';
import '@zxio/table-render/style';
import { listConfig, delConfig, refreshCache, type ConfigRecord } from '@/api/system/config';
import type { ConfigPageQueryModel } from '@/api/_generated/types.gen';
import { gridQueryContext, requireQueryScope, scopeRequestOptions } from '@/queries/context';
import { checkPermi } from '@/utils/permission';
import { normalizeGridParams } from '@/utils/grid-params';
import { serializeDateRange } from '@/utils/ruoyi';
import RemarkDisplay from '@/components/ui/Remark/RemarkDisplay.vue';
import DictSelect from '@/components/business/DictSelect/index.vue';
import ConfigDlg from './ConfigDlg.vue';

type Query = Pick<ConfigPageQueryModel, 'configName' | 'configKey' | 'configType'> & {
  dateRange?: string[];
};
const proxy = getCurrentInstance()!.proxy!;
const { sys_yes_no } = proxy.useDict('sys_yes_no');
const configDlgRef = shallowRef<InstanceType<typeof ConfigDlg>>();
function open(id?: number) {
  return configDlgRef.value?.open(id).catch(() => {
    /* The editor owns read feedback. */
  });
}
const definition = defineTableRender<ConfigRecord, Query>()({
  key: 'config-management',
  title: '参数配置',
  rowKey: 'configId',
  layout: { fill: true, inlineLimit: 3 },
  selection: { mode: 'multiple' },
  pagination: { pageSize: 10 },
  search: [
    { key: 'configName', label: '参数名称', control: 'text', placement: 'keyword' },
    {
      key: 'configKey',
      label: '参数键名',
      control: 'text',
      placement: 'inline',
      placeholder: '请输入参数键名',
    },
    {
      key: 'configType',
      label: '系统内置',
      control: { slot: 'config-type' },
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
    { key: 'configId', label: '参数主键', prop: 'configId', width: 100 },
    { key: 'configName', label: '参数名称', prop: 'configName', minWidth: 180 },
    { key: 'configKey', label: '参数键名', prop: 'configKey', minWidth: 180 },
    { key: 'configValue', label: '参数键值', prop: 'configValue', minWidth: 150 },
    { key: 'configType', label: '系统内置', prop: 'configType', width: 100 },
    { key: 'remark', label: '备注', prop: 'remarkText', minWidth: 180 },
    { key: 'createTime', label: '创建时间', prop: 'createTime', type: 'datetime', width: 180 },
    {
      key: 'operations',
      label: '操作',
      type: 'actions',
      fixed: 'right',
      width: 150,
      hideable: false,
    },
  ],
  request: async ({ query, pager, sort }, { signal }) => {
    const result = await listConfig(
      normalizeGridParams({ query: serializeDateRange(query), pager, sort }),
      { signal, requestOptions: scopeRequestOptions(requireQueryScope()) }
    );
    return {
      list: result.items,
      pager: { total: result.total, page: result.page, size: result.pageSize },
    };
  },
  actions: {
    toolbar: [
      {
        id: 'add',
        label: '新增',
        tone: 'primary',
        icon: 'Plus',
        visible: () => checkPermi(['system:config:add']),
        run: () => open(),
      },
      {
        id: 'export',
        label: '导出',
        icon: 'Download',
        visible: () => checkPermi(['system:config:export']),
        disabled: ({ applied }) => !applied,
        run: ({ applied }) =>
          applied &&
          proxy.download(
            'system/config/export',
            normalizeGridParams({ query: serializeDateRange(applied.query), sort: applied.sort }),
            `config_${Date.now()}.xlsx`
          ),
      },
      {
        id: 'cache',
        label: '刷新缓存',
        icon: 'Refresh',
        visible: () => checkPermi(['system:config:remove']),
        run: () => refreshCache(),
      },
    ],
    batch: [
      {
        id: 'edit-selected',
        label: '修改',
        icon: 'Edit',
        visible: () => checkPermi(['system:config:edit']),
        disabled: ({ loadedRows, missingKeys }) =>
          loadedRows.length !== 1 || missingKeys.length > 0,
        run: ({ loadedRows }) => open(loadedRows[0].configId),
      },
      {
        id: 'delete-selected',
        label: '删除',
        tone: 'danger',
        icon: 'Delete',
        visible: () => checkPermi(['system:config:remove']),
        confirm: ({ keys }) => `是否确认删除参数编号为“${keys.join(',')}”的数据项？`,
        run: ({ keys }) => delConfig(keys.join(',')),
        reloadAfter: true,
      },
    ],
    row: [
      {
        id: 'edit',
        label: '修改',
        visible: () => checkPermi(['system:config:edit']),
        run: (row) => open(row.configId),
      },
      {
        id: 'delete',
        label: '删除',
        tone: 'danger',
        visible: () => checkPermi(['system:config:remove']),
        confirm: (row) => `是否确认删除参数编号为“${row.configId}”的数据项？`,
        run: (row) => delConfig(row.configId),
        reloadAfter: true,
      },
    ],
  },
});
const tableRef = shallowRef<TableRenderInstance<typeof definition, ConfigRecord, Query>>();
</script>
