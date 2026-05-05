import { http, HttpResponse, type HttpHandler } from 'msw';

export interface MockApiNotImplementedPayload {
  code: 501;
  msg: string;
  data: null;
}

export function isMockApiRequest(request: Request, apiPrefix: string): boolean {
  const url = new URL(request.url);
  return url.pathname === apiPrefix || url.pathname.startsWith(`${apiPrefix}/`);
}

export function createMockApiNotImplementedPayload(request: Request): MockApiNotImplementedPayload {
  const url = new URL(request.url);
  const path = `${url.pathname}${url.search}`;
  return {
    code: 501,
    msg: `MOCK_API_NOT_IMPLEMENTED: ${request.method} ${path} 尚未在单套 mock 主线中实现`,
    data: null,
  };
}

export function createUnhandledApiHandler(apiPrefix = '/api'): HttpHandler {
  return http.all(
    ({ request }) => isMockApiRequest(request, apiPrefix),
    ({ request }) =>
      HttpResponse.json(createMockApiNotImplementedPayload(request), {
        status: 501,
        headers: {
          'X-Mock-Response': 'true',
          'X-Mock-Handler': 'unhandled-api',
        },
      })
  );
}
