// Temporary local contracts for historical endpoints that are not yet represented
// by generated OpenAPI types. Migrate each shape to shared/openapi.json-backed
// generated types as the corresponding backend contract becomes reliable.
export interface MockListQuery {
  page?: number;
  pageSize?: number;
  [key: string]: unknown;
}

export interface MockPage<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
}

export interface MockMutationResult<T = unknown> {
  data: T;
  changed: boolean;
}
