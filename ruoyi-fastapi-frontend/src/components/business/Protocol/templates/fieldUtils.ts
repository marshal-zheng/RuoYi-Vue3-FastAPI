export type ProtocolFieldRow = {
  seqNo: string;
  infoName: string;
  byteSize: string;
  wordSize: string;
  valueRange: string;
  dimension: string;
  dataType: string;
  scale: string;
  remark: string;
};

const FIELD_KEY_MAP: Record<string, keyof ProtocolFieldRow> = {
  序号: 'seqNo',
  信息名称: 'infoName',
  字节数: 'byteSize',
  字号: 'wordSize',
  值域及含义: 'valueRange',
  量纲: 'dimension',
  数据类型: 'dataType',
  比例尺: 'scale',
  备注: 'remark',
};

const createFieldSkeleton = (): ProtocolFieldRow => ({
  seqNo: '',
  infoName: '',
  byteSize: '',
  wordSize: '',
  valueRange: '',
  dimension: '',
  dataType: '',
  scale: '1',
  remark: '',
});

export const createEmptyFieldRow = (
  overrides: Partial<ProtocolFieldRow> = {}
): ProtocolFieldRow => ({
  ...createFieldSkeleton(),
  ...overrides,
});

export const normalizeFieldRow = (row: any): ProtocolFieldRow => {
  if (!row) {
    return createEmptyFieldRow();
  }
  if ('seqNo' in row) {
    return createEmptyFieldRow(row);
  }

  const normalized = createFieldSkeleton();
  Object.entries(FIELD_KEY_MAP).forEach(([cnKey, enKey]) => {
    if (Object.prototype.hasOwnProperty.call(row, cnKey)) {
      normalized[enKey] = row[cnKey];
    }
  });
  return normalized;
};

export const normalizeFieldRows = (rows?: any[]): ProtocolFieldRow[] => {
  if (!Array.isArray(rows)) return [];
  return rows.map(row => normalizeFieldRow(row));
};

export const getNextSeqNo = (rows: ProtocolFieldRow[]): string => {
  if (!rows.length) return '1';
  const max = Math.max(
    ...rows.map(row => {
      const parsed = parseInt(row.seqNo, 10);
      return Number.isNaN(parsed) ? 0 : parsed;
    })
  );
  return (max + 1).toString();
};

export const cloneConfig = <T>(config: T): T => JSON.parse(JSON.stringify(config));

export const resolveEditorValue = (cellParams: any, value: any) =>
  value !== undefined ? value : (cellParams?.cellValue ?? '');
