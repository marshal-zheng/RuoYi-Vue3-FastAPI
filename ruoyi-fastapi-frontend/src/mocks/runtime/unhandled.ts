import { http, HttpResponse, type HttpHandler } from 'msw';
import type { ProblemDetails } from '@/types/http-contract';

export interface MockApiNotImplementedPayload extends ProblemDetails {
  status: 501;
  errorCode: 'MOCK_API_NOT_IMPLEMENTED';
}

export function isMockApiRequest(request: Request, apiPrefix: string): boolean {
  const url = new URL(request.url);
  return url.pathname === apiPrefix || url.pathname.startsWith(`${apiPrefix}/`);
}

export function createMockApiNotImplementedPayload(request: Request): MockApiNotImplementedPayload {
  const url = new URL(request.url);
  const path = `${url.pathname}${url.search}`;
  return {
    type: 'about:blank',
    title: 'MOCK_API_NOT_IMPLEMENTED',
    status: 501,
    detail: `MOCK_API_NOT_IMPLEMENTED: ${request.method} ${path} 尚未在单套 mock 主线中实现`,
    instance: path,
    errorCode: 'MOCK_API_NOT_IMPLEMENTED',
  };
}

export function createUnhandledApiHandler(apiPrefix = '/api'): HttpHandler {
  return http.all(
    ({ request }) => isMockApiRequest(request, apiPrefix),
    ({ request }) =>
      HttpResponse.json(createMockApiNotImplementedPayload(request), {
        status: 501,
        headers: {
          'Content-Type': 'application/problem+json',
          'X-Mock-Response': 'true',
          'X-Mock-Handler': 'unhandled-api',
        },
      })
  );
}
