export type Recordable<T = unknown> = Record<string, T>;

export interface ResultOptions {
  msg?: string;
}

export interface ErrorOptions<T = null> {
  code?: number;
  data?: T;
}

function isRecord(value: unknown): value is Recordable {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function cloneSuccessData<T>(data: T): T {
  if (Array.isArray(data)) {
    return data.map((item) => cloneSuccessData(item)) as T;
  }

  if (!isRecord(data)) {
    return data;
  }

  const normalized: Recordable = {};
  Object.entries(data).forEach(([key, value]) => {
    normalized[key] = cloneSuccessData(value);
  });
  return normalized as T;
}

export function resultSuccess<T = Recordable>(data: T, { msg = '操作成功' }: ResultOptions = {}) {
  void msg;
  return cloneSuccessData(data);
}

export function resultError<T = null>(
  msg = '请求失败',
  { code = 500, data = null as T }: ErrorOptions<T> = {}
) {
  const detail = typeof data === 'string' ? data : msg;
  return {
    type: 'about:blank',
    title: msg,
    status: code,
    detail,
    instance: '',
  };
}

export function resultPageSuccess<T = unknown>(
  page: number,
  pageSize: number,
  list: T[],
  { msg = '操作成功' }: ResultOptions = {}
) {
  void msg;
  return resultSuccess({
    items: pagination(page, pageSize, list),
    total: list.length,
    page,
    pageSize,
  });
}

export function pagination<T = unknown>(pageNo: number, pageSize: number, array: T[]): T[] {
  const offset = (pageNo - 1) * Number(pageSize);
  const size = Number(pageSize);
  return offset + size >= array.length
    ? array.slice(offset, array.length)
    : array.slice(offset, offset + size);
}
