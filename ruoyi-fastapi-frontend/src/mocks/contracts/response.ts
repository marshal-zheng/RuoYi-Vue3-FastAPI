export interface ApiResult<T = unknown> {
  code: number;
  msg: string;
  data: T;
}

export interface ApiPageResult<T = unknown> {
  code: number;
  msg: string;
  rows?: T[];
  total?: number;
  data?: {
    items?: T[];
    total?: number;
    page?: number;
    pageSize?: number;
  };
}

export interface ApiErrorResult {
  code: number;
  msg: string;
  data: null;
}

export type MockApiResponse<T = unknown> = ApiResult<T> | ApiPageResult<T> | ApiErrorResult;

export interface MockBinaryResponse {
  body: Blob | ArrayBuffer | string;
  filename: string;
  contentType: string;
}
