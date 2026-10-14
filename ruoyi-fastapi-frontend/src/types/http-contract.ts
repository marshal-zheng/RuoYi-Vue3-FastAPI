export interface HttpCollection<T = unknown> {
  readonly pager?: HttpPager;
  readonly __httpMeta?: HttpContractMeta;
  items: T[];
}

export interface HttpOffsetPage<T = unknown> {
  readonly pager?: HttpPager;
  readonly __httpMeta?: HttpContractMeta;
  items: T[];
  total: number;
  page: number;
  pageSize: number;
}

export interface HttpCursorPage<T = unknown> {
  readonly pager?: HttpPager;
  readonly __httpMeta?: HttpContractMeta;
  items: T[];
  pageSize: number;
  nextCursor?: string | null;
}

export interface BatchResultItemError {
  errorCode?: string | number | null;
  title?: string | null;
  detail?: string | null;
}

export interface BatchResultItem {
  success: boolean;
  itemId?: string | number | null;
  error?: BatchResultItemError | null;
  [key: string]: unknown;
}

export interface BatchResultSummary {
  total?: number;
  succeeded?: number;
  failed?: number;
  [key: string]: unknown;
}

export interface BatchResult<TItem extends BatchResultItem = BatchResultItem> {
  results: TItem[];
  summary: BatchResultSummary;
}

export interface ProblemValidationError {
  field: string;
  message: string;
  code?: string | null;
}

export interface ProblemDetails {
  type: string;
  title: string;
  status: number;
  detail: string;
  instance: string;
  errorCode?: string | number;
  requestId?: string;
  traceId?: string;
  errors?: ProblemValidationError[];
}

export interface HttpContractMeta {
  status: number;
  requestId?: string;
  traceId?: string;
  location?: string;
  retryAfter?: number;
  rateLimitLimit?: number;
  rateLimitRemaining?: number;
  rateLimitReset?: number;
}

export interface HttpPager {
  mode: 'collection' | 'offset' | 'cursor';
  page?: number;
  size?: number;
  total?: number;
  nextCursor?: string | null;
}

export type HttpListResult<T = unknown> = HttpCollection<T> | HttpOffsetPage<T> | HttpCursorPage<T>;

export const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === 'object' && value !== null && !Array.isArray(value);

export const isProblemDetails = (value: unknown): value is ProblemDetails =>
  isRecord(value) &&
  typeof value.type === 'string' &&
  typeof value.title === 'string' &&
  typeof value.status === 'number' &&
  typeof value.detail === 'string' &&
  typeof value.instance === 'string';

export const isBatchResult = (value: unknown): value is BatchResult =>
  isRecord(value) && Array.isArray(value.results) && isRecord(value.summary);

export const isOffsetPage = <T = unknown>(value: unknown): value is HttpOffsetPage<T> =>
  isRecord(value) &&
  Array.isArray(value.items) &&
  typeof value.total === 'number' &&
  typeof value.page === 'number' &&
  typeof value.pageSize === 'number';

export const isCursorPage = <T = unknown>(value: unknown): value is HttpCursorPage<T> =>
  isRecord(value) &&
  Array.isArray(value.items) &&
  typeof value.pageSize === 'number' &&
  ('nextCursor' in value || value.nextCursor === null);

export const isCollection = <T = unknown>(value: unknown): value is HttpCollection<T> =>
  isRecord(value) && Array.isArray(value.items) && !('total' in value) && !('nextCursor' in value);
