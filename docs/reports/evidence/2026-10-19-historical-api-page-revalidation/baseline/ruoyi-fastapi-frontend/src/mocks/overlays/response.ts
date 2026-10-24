import { HttpResponse } from 'msw';

import { createMockApiNotImplementedPayload } from '../runtime/unhandled';
import type { MockStrategy } from '../types';
import { resultError, resultSuccess } from '../utils/response';
import type { MockOverlayRegistryEntry } from './types';

export interface MockOverlayResponseOptions {
  request: Request;
  entry: MockOverlayRegistryEntry;
  strategy: MockStrategy;
  body: unknown;
  status?: number;
  contentType?: string;
}

function createOverlayHeaders(entry: MockOverlayRegistryEntry, strategy: MockStrategy) {
  const headers = new Headers();
  headers.set('X-Mock-Response', 'true');
  headers.set('X-Mock-Mode', strategy);
  headers.set('X-Mock-Handler', entry.target.handlerTag);
  headers.set('X-Mock-Overlay', entry.id);
  if (entry.response?.status === 429) {
    headers.set('Retry-After', '30');
  }
  return headers;
}

function problemStatus(entry: MockOverlayRegistryEntry) {
  if (entry.stateType === 'forbidden') return 403;
  if (entry.stateType === 'timeout') return 504;
  if (entry.stateType === 'unsupported') return 501;
  return entry.response?.status ?? 500;
}

function problemDetail(entry: MockOverlayRegistryEntry) {
  if (entry.response?.reason) return entry.response.reason;
  if (entry.stateType === 'forbidden') return '权限不足';
  if (entry.stateType === 'timeout') return '请求超时';
  if (entry.stateType === 'unsupported') return 'MOCK_API_NOT_IMPLEMENTED';
  if (entry.response?.status === 429) return '请求过于频繁';
  return '请求失败';
}

export function createOverlayProblemBody(entry: MockOverlayRegistryEntry) {
  const status = problemStatus(entry);
  return {
    ...resultError(problemDetail(entry), { code: status }),
    errorCode: entry.response?.errorCode ?? status,
  };
}

function createOverlayUnsupportedBody(request: Request, entry: MockOverlayRegistryEntry) {
  const payload = createMockApiNotImplementedPayload(request);
  const reason = entry.response?.reason ?? payload.detail;
  return {
    ...payload,
    detail: `${payload.detail}：${reason}`,
    reason,
    errorCode: entry.response?.errorCode ?? 'MOCK_API_NOT_IMPLEMENTED',
  };
}

export function createOverlayJsonResponse({
  entry,
  strategy,
  body,
  status = 200,
  contentType = 'application/json',
}: MockOverlayResponseOptions) {
  const headers = createOverlayHeaders(entry, strategy);
  headers.set('Content-Type', contentType);
  return new HttpResponse(JSON.stringify(body), { status, headers });
}

export function createOverlayProblemResponse(options: Omit<MockOverlayResponseOptions, 'body'>) {
  return createOverlayJsonResponse({
    ...options,
    body:
      options.entry.stateType === 'unsupported'
        ? createOverlayUnsupportedBody(options.request, options.entry)
        : createOverlayProblemBody(options.entry),
    status: problemStatus(options.entry),
    contentType: 'application/problem+json',
  });
}

export function createOverlaySuccessResponse(
  options: Omit<MockOverlayResponseOptions, 'body'> & { data: unknown }
) {
  return createOverlayJsonResponse({
    ...options,
    body: resultSuccess(options.data),
  });
}

export function createOverlayPageResponse(
  options: Omit<MockOverlayResponseOptions, 'body'> & {
    items: unknown[];
    total?: number;
    page: number;
    pageSize: number;
  }
) {
  return createOverlaySuccessResponse({
    ...options,
    data: {
      items: options.items,
      total: options.total ?? options.items.length,
      page: options.page,
      pageSize: options.pageSize,
    },
  });
}
