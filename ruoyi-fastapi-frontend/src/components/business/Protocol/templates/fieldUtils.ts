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

const fieldText = (value: unknown, fallback = ''): string =>
  typeof value === 'string' || typeof value === 'number' ? String(value) : fallback;

export const normalizeFieldRow = (row: unknown): ProtocolFieldRow => {
  const normalized = createFieldSkeleton();
  if (!row || typeof row !== 'object') return normalized;

  Object.entries(FIELD_KEY_MAP).forEach(([cnKey, enKey]) => {
    if (enKey in row) {
      normalized[enKey] = fieldText(Reflect.get(row, enKey), normalized[enKey]);
    } else if (cnKey in row) {
      normalized[enKey] = fieldText(Reflect.get(row, cnKey), normalized[enKey]);
    }
  });
  return normalized;
};

export const normalizeFieldRows = (rows?: unknown[]): ProtocolFieldRow[] => {
  if (!Array.isArray(rows)) return [];
  return rows.map((row) => normalizeFieldRow(row));
};

export const getNextSeqNo = (rows: ProtocolFieldRow[]): string => {
  if (!rows.length) return '1';
  const max = Math.max(
    ...rows.map((row) => {
      const parsed = parseInt(row.seqNo, 10);
      return Number.isNaN(parsed) ? 0 : parsed;
    })
  );
  return (max + 1).toString();
};

export const cloneConfig = <T>(config: T): T => JSON.parse(JSON.stringify(config));

export const resolveEditorValue = <T>(
  cellParams: { cellValue?: T } | undefined,
  value: T | undefined
) => (value !== undefined ? value : (cellParams?.cellValue ?? ''));
