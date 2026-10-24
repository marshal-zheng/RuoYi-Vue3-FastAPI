import { delay, http, HttpResponse, type HttpHandler, type JsonBodyType } from 'msw';

import { createApiPath } from '../constants';
import type { MockErrorScenario, MockRuntimeHandler } from '../types';

export type MockHttpMethod = 'get' | 'post' | 'put' | 'patch' | 'delete' | 'all';

export interface MockErrorHandlerOptions {
  detail?: string;
  delayMs?: number;
  errorCode?: number | string;
  headers?: HeadersInit;
  scenario?: MockErrorScenario;
}

const DEFAULT_TIMEOUT_DELAY_MS = 11_000;

const scenarioStatus = {
  'error-5xx': 503,
  'error-429': 429,
} satisfies Partial<Record<MockErrorScenario, number>>;

function methodHandler(method: MockHttpMethod) {
  switch (method) {
    case 'get':
      return http.get;
    case 'post':
      return http.post;
    case 'put':
      return http.put;
    case 'patch':
      return http.patch;
    case 'delete':
      return http.delete;
    case 'all':
      return http.all;
    default:
      return http.all;
  }
}

function problem(status: number, detail: string, errorCode: number | string = status) {
  return {
    type: 'about:blank',
    title: detail,
    status,
    detail,
    instance: '',
    errorCode,
  };
}

function responseHeaders(
  scenario: MockErrorScenario | undefined,
  status: number,
  headers?: HeadersInit
): Headers {
  const responseHeaders = new Headers(headers);
  responseHeaders.set('X-Mock-Handler', 'error-scenario');
  if (scenario) {
    responseHeaders.set('X-Mock-Scenario', scenario);
  }
  if (status === 429 && !responseHeaders.has('Retry-After')) {
    responseHeaders.set('Retry-After', '30');
  }
  return responseHeaders;
}

function registerHandler(
  method: MockHttpMethod,
  path: string,
  resolver: Parameters<typeof http.all>[1]
): HttpHandler {
  return methodHandler(method)(createApiPath(path), resolver);
}

export function createStatusHandler(
  method: MockHttpMethod,
  path: string,
  status: number,
  options: MockErrorHandlerOptions = {}
): HttpHandler {
  const scenario =
    options.scenario ?? (status === 429 ? 'error-429' : status >= 500 ? 'error-5xx' : undefined);
  const detail =
    options.detail ??
    (status === 429 ? '请求过于频繁' : status >= 500 ? '服务暂不可用' : '请求失败');

  return registerHandler(method, path, () =>
    HttpResponse.json(problem(status, detail, options.errorCode), {
      status,
      headers: responseHeaders(scenario, status, options.headers),
    })
  );
}

export function createNetworkErrorHandler(
  method: MockHttpMethod,
  path: string,
  options: MockErrorHandlerOptions = {}
): HttpHandler {
  return registerHandler(method, path, () => {
    void options;
    return HttpResponse.error();
  });
}

export function createTimeoutHandler(
  method: MockHttpMethod,
  path: string,
  options: MockErrorHandlerOptions = {}
): HttpHandler {
  const delayMs = options.delayMs ?? DEFAULT_TIMEOUT_DELAY_MS;
  const status = 504;
  return registerHandler(method, path, async () => {
    await delay(delayMs);
    return HttpResponse.json(
      problem(status, options.detail ?? '请求超时', options.errorCode ?? 'MOCK_TIMEOUT'),
      {
        status,
        headers: responseHeaders(options.scenario ?? 'error-timeout', status, options.headers),
      }
    );
  });
}

export function isMockErrorScenario(scenario: string): scenario is MockErrorScenario {
  return scenario === 'error-timeout' || scenario === 'error-5xx' || scenario === 'error-429';
}

export function createErrorScenarioHandlers(
  scenario: MockErrorScenario,
  path = '/*'
): MockRuntimeHandler[] {
  if (scenario === 'error-timeout') {
    return [createTimeoutHandler('all', path, { scenario })];
  }

  return [
    createStatusHandler('all', path, scenarioStatus[scenario] ?? 503, {
      scenario,
    }),
  ];
}

export const mockErrorScenarios = ['error-timeout', 'error-5xx', 'error-429'] as const;

export type MockProblemResponse = ReturnType<typeof problem> & JsonBodyType;
