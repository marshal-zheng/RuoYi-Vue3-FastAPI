import type { VNodeChild } from 'vue';
import type { VxeTableDefines, VxeTableEvents, VxeTableInstance } from 'vxe-table';
import type { useDataSource, DataSourceOptions, DataSourceItem } from './dataSource';

export type SchemaCellScope<T extends object> = VxeTableDefines.CellRenderBodyParams<T>;
export type SchemaHeaderScope<T extends object> = VxeTableDefines.CellRenderHeaderParams<T>;
export type SchemaEditClosedParams<T extends object> = Parameters<VxeTableEvents.EditClosed<T>>[0];

export type VxeSchemaColumn<T extends object = DataSourceItem> =
  VxeTableDefines.ColumnOptions<T> & {
    slot?: string;
    headerSlot?: string;
    children?: VxeSchemaColumn<T>[];
    render?: (
      scope: SchemaCellScope<T> & { dataSource: ReturnType<typeof useDataSource> | null }
    ) => VNodeChild;
    widget?: string;
    widgetProps?: Record<string, unknown>;
    dataSource?: DataSourceOptions;
  };

export type VxeSchemaHooks<T extends object = DataSourceItem> = {
  onTableReady?: (table: VxeTableInstance<T>) => void;
  onCellClick?: VxeTableEvents.CellClick<T>;
  onCellDblclick?: VxeTableEvents.CellDblclick<T>;
  onEditClosed?: VxeTableEvents.EditClosed<T>;
  onValueChange?: (payload: {
    row: T;
    field: string;
    value: unknown;
    params: SchemaEditClosedParams<T>;
  }) => void;
};
