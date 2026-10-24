<template>
  <vxe-table ref="tableRef" v-bind="normalizedTableProps" v-on="tableListeners">
    <SchemaColumn
      v-for="column in normalizedColumns"
      :key="String(column.field || column.type || '')"
      :column="column"
    />
  </vxe-table>
</template>

<script lang="ts">
export type { VxeSchemaColumn, VxeSchemaHooks } from './types';
</script>

<script setup lang="ts" generic="Row extends object = Record<string, unknown>">
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
import type { VxeTableProps, VxeTableInstance, VxeTableEvents } from 'vxe-table';
import { useVXETable } from '@/plugins/vxe-table';
import { mergeColumnOptions, resolveWidgetColumn } from './widgetRegistry';
import type { VxeWidgetResolverMap } from './widgetRegistry';
import { useDataSource } from './dataSource';
import type {
  VxeSchemaColumn,
  VxeSchemaHooks,
  SchemaCellScope,
  SchemaHeaderScope,
  SchemaEditClosedParams,
} from './types';

useVXETable();

const SLOT_KEY = Symbol('vxe-schema-table-slots');

defineSlots<
  Record<
    string,
    (
      props: Partial<SchemaCellScope<Row>> & {
        dataSource?: ReturnType<typeof useDataSource> | null;
      }
    ) => import('vue').VNode[]
  >
>();

const props = defineProps({
  columns: {
    type: Array as PropType<VxeSchemaColumn<Row>[]>,
    required: true,
  },
  data: {
    type: Array as PropType<Row[]>,
    default: () => [],
  },
  tableProps: Object as PropType<VxeTableProps<Row>>,
  spanMethod: Function as PropType<VxeTableProps<Row>['spanMethod']>,
  footerMethod: Function as PropType<VxeTableProps<Row>['footerMethod']>,
  editConfig: Object as PropType<VxeTableProps<Row>['editConfig']>,
  editRules: Object as PropType<VxeTableProps<Row>['editRules']>,
  widgets: Object as PropType<VxeWidgetResolverMap>,
  hooks: Object as PropType<VxeSchemaHooks<Row>>,
});

const tableSlots = useSlots();
provide(SLOT_KEY, tableSlots);
const tableRef = ref<VxeTableInstance<Row>>();

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
      type: Object as PropType<VxeSchemaColumn<Row>>,
      required: true,
    },
  },
  setup(columnProps) {
    const parentSlots = inject<Slots>(SLOT_KEY, {});
    const dataSourceCtx = columnProps.column.dataSource
      ? useDataSource(columnProps.column.dataSource)
      : null;

    const resolvedColumn = computed<VxeSchemaColumn<Row>>(() => {
      const column: VxeSchemaColumn<Row> = { ...columnProps.column };

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
      const RecursiveSchemaColumn = resolveComponent('SchemaColumn');

      const children = column.children?.map((child, idx) =>
        h(RecursiveSchemaColumn, {
          column: child,
          key: child.field || child.type || idx,
        })
      );

      const slotName = column.slot;
      const defaultSlot =
        children && children.length
          ? () => children
          : slotName
            ? (scope: SchemaCellScope<Row>) =>
                parentSlots?.[slotName]?.({ ...scope, dataSource: dataSourceCtx })
            : column.render
              ? (scope: SchemaCellScope<Row>) =>
                  column.render?.({ ...scope, dataSource: dataSourceCtx })
              : undefined;

      const headerSlotName = column.headerSlot;
      const headerSlot = headerSlotName
        ? (scope: SchemaHeaderScope<Row>) =>
            parentSlots?.[headerSlotName]?.({ ...scope, dataSource: dataSourceCtx })
        : undefined;

      return h(resolveComponent('vxe-column'), column, {
        default: defaultSlot,
        header: headerSlot,
      });
    };
  },
});

function normalizeColumns<T extends object>(
  columns: VxeSchemaColumn<T>[],
  widgets?: VxeWidgetResolverMap
): VxeSchemaColumn<T>[] {
  return columns.map((column) => {
    const widgetColumn = resolveWidgetColumn(column, widgets);
    const merged = mergeColumnOptions(widgetColumn, column);

    if (merged.children) {
      merged.children = normalizeColumns(merged.children, widgets);
    }

    return merged;
  });
}

function buildTableListeners<T extends object>(hooks?: VxeSchemaHooks<T>) {
  if (!hooks) return {};
  const listeners: {
    'cell-click'?: VxeTableEvents.CellClick<T>;
    'cell-dblclick'?: VxeTableEvents.CellDblclick<T>;
    'edit-closed'?: VxeTableEvents.EditClosed<T>;
  } = {};

  if (hooks.onCellClick) listeners['cell-click'] = hooks.onCellClick;
  if (hooks.onCellDblclick) listeners['cell-dblclick'] = hooks.onCellDblclick;
  if (hooks.onEditClosed || hooks.onValueChange) {
    listeners['edit-closed'] = (params: SchemaEditClosedParams<T>) => {
      hooks.onEditClosed?.(params);
      if (hooks.onValueChange && params?.row && params?.column?.field) {
        const field = params.column.field;
        hooks.onValueChange({
          row: params.row,
          field,
          value: Reflect.get(params.row, field),
          params,
        });
      }
    };
  }

  return listeners;
}
</script>
