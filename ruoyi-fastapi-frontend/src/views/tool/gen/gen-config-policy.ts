export interface GenerationColumn {
  columnName: string;
  columnComment?: string;
}
export interface GenerationTable {
  tableName: string;
  columns?: GenerationColumn[];
}
export function getGenerationColumnOptions(columns?: readonly GenerationColumn[]) {
  return (columns ?? []).map((column) => ({
    label: `${column.columnName}：${column.columnComment ?? ''}`,
    value: column.columnName,
  }));
}
export function getSubTableColumns(
  tables: readonly GenerationTable[] | null | undefined,
  name: string
) {
  return tables?.find((table) => table.tableName === name)?.columns ?? [];
}
export function getGenerationUserPatch(
  command: { type: 'subTable' } | { type: 'template'; value: string }
) {
  if (command.type === 'subTable') return { subTableFkName: '' };
  return command.value === 'sub' ? {} : { subTableName: '', subTableFkName: '' };
}
export function buildGenTablePayload<T extends Record<string, unknown>>(
  info: T,
  columns: unknown[]
) {
  return {
    ...info,
    columns,
    params: {
      treeCode: info.treeCode,
      treeName: info.treeName,
      treeParentCode: info.treeParentCode,
      parentMenuId: info.parentMenuId,
    },
  };
}
