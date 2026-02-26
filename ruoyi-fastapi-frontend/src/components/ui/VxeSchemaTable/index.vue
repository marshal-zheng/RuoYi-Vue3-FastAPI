<template>
  <vxe-table ref="tableRef" v-bind="normalizedTableProps" v-on="tableListeners">
    <SchemaColumn
      v-for="column in normalizedColumns"
      :key="column.field || column.type"
      :column="column"
    />
  </vxe-table>
</template>

<script setup lang="ts">
import {
  computed,
  defineComponent,
  h,
  inject,
  onMounted,
  provide,
  ref,
  resolveComponent,
  useSlots,
} from 'vue';
import type { PropType, Slots } from 'vue';
import type { VxeTableDefines, VxeTableProps, VxeTableInstance } from 'vxe-table';
import { mergeColumnOptions, resolveWidgetColumn } from './widgetRegistry';
import type { VxeWidgetResolverMap } from './widgetRegistry';
import { useDataSource } from './dataSource';

const SLOT_KEY = Symbol('vxe-schema-table-slots');

export type VxeSchemaColumn = VxeTableDefines.ColumnOptions & {
  slot?: string;
  headerSlot?: string;
  children?: VxeSchemaColumn[];
  render?: (scope: any) => any;
  widget?: string;
  widgetProps?: Record<string, any>;
  dataSource?: DataSourceOptions;
};

export type VxeSchemaHooks = {
  onTableReady?: (table: VxeTableInstance) => void;
  onCellClick?: (params: any) => void;
  onCellDblclick?: (params: any) => void;
  onEditClosed?: (params: any) => void;
  onValueChange?: (payload: { row: any; field: string; value: any; params: any }) => void;
};

const props = defineProps({
  columns: {
    type: Array as PropType<VxeSchemaColumn[]>,
    required: true,
  },
  data: {
    type: Array as PropType<any[]>,
    default: () => [],
  },
  tableProps: Object as PropType<VxeTableProps>,
  spanMethod: Function as PropType<VxeTableProps['spanMethod']>,
  footerMethod: Function as PropType<VxeTableProps['footerMethod']>,
  editConfig: Object as PropType<VxeTableProps['editConfig']>,
  editRules: Object as PropType<VxeTableProps['editRules']>,
  widgets: Object as PropType<VxeWidgetResolverMap>,
  hooks: Object as PropType<VxeSchemaHooks>,
});

const tableSlots = useSlots();
provide(SLOT_KEY, tableSlots);
const tableRef = ref<VxeTableInstance>();

const normalizedTableProps = computed(() => ({
  ...props.tableProps,
  data: props.data ?? props.tableProps?.data ?? [],
  spanMethod: props.spanMethod ?? props.tableProps?.spanMethod,
  footerMethod: props.footerMethod ?? props.tableProps?.footerMethod,
  editConfig: props.editConfig ?? props.tableProps?.editConfig,
  editRules: props.editRules ?? props.tableProps?.editRules,
}));

const normalizedColumns = computed(() => normalizeColumns(props.columns || [], props.widgets));
const tableListeners = computed(() => buildTableListeners(props.hooks));

onMounted(() => {
  if (props.hooks?.onTableReady && tableRef.value) {
    props.hooks.onTableReady(tableRef.value);
  }
});

const SchemaColumn = defineComponent({
  name: 'SchemaColumn',
  props: {
    column: {
      type: Object as PropType<VxeSchemaColumn>,
      required: true,
    },
  },
  setup(columnProps) {
    const parentSlots = inject<Slots>(SLOT_KEY, {});
    const dataSourceCtx = columnProps.column.dataSource
      ? useDataSource(columnProps.column.dataSource)
      : null;

    const resolvedColumn = computed(() => {
      const column = { ...columnProps.column };

      if (dataSourceCtx) {
        const baseEdit = column.editRender || { name: 'select' };
        const baseProps = baseEdit.props || {};
        column.editRender = {
          ...baseEdit,
          props: {
            ...baseProps,
            options: baseProps.options ?? dataSourceCtx.options.value,
            loading: baseProps.loading ?? dataSourceCtx.loading.value,
          },
          options: baseEdit.options ?? dataSourceCtx.options.value,
        };
      }

      return column;
    });

    return () => {
      const column = resolvedColumn.value;

      const children = column.children?.map((child, idx) =>
        h(SchemaColumn, {
          column: child,
          key: child.field || child.type || idx,
        })
      );

      const defaultSlot =
        children && children.length
          ? () => children
          : column.slot
            ? (scope: any) => parentSlots?.[column.slot]?.({ ...scope, dataSource: dataSourceCtx })
            : column.render
              ? (scope: any) => column.render?.({ ...scope, dataSource: dataSourceCtx })
              : undefined;

      const headerSlot = column.headerSlot
        ? (scope: any) =>
            parentSlots?.[column.headerSlot]?.({ ...scope, dataSource: dataSourceCtx })
        : undefined;

      return h(resolveComponent('vxe-column') as any, column, {
        default: defaultSlot,
        header: headerSlot,
      });
    };
  },
});

function normalizeColumns(columns: VxeSchemaColumn[], widgets?: VxeWidgetResolverMap) {
  return columns.map((column) => {
    const widgetColumn = resolveWidgetColumn(column, widgets);
    const merged = mergeColumnOptions(widgetColumn, column);

    if (merged.children) {
      merged.children = normalizeColumns(merged.children, widgets);
    }

    return merged;
  });
}

type DataSourceOptions = Parameters<typeof useDataSource>[0];

function buildTableListeners(hooks?: VxeSchemaHooks) {
  if (!hooks) return {};
  const listeners: Record<string, any> = {};

  if (hooks.onCellClick) listeners['cell-click'] = hooks.onCellClick;
  if (hooks.onCellDblclick) listeners['cell-dblclick'] = hooks.onCellDblclick;
  if (hooks.onEditClosed || hooks.onValueChange) {
    listeners['edit-closed'] = (params: any) => {
      hooks.onEditClosed?.(params);
      if (hooks.onValueChange && params?.row && params?.column?.field) {
        const field = params.column.field;
        hooks.onValueChange({
          row: params.row,
          field,
          value: params.row[field],
          params,
        });
      }
    };
  }

  return listeners;
}
</script>
