import { describe, expect, it } from 'vitest';

import { mockServer } from '../../../tests/mocks/server';

import {
  createMockApiNotImplementedPayload,
  createUnhandledApiHandler,
  isMockApiRequest,
} from './unhandled';

describe('mock runtime unhandled API helpers', () => {
  it('recognizes API requests by prefix', () => {
    expect(isMockApiRequest(new Request('http://localhost/api/project/list'), '/api')).toBe(true);
    expect(isMockApiRequest(new Request('http://localhost/assets/logo.png'), '/api')).toBe(false);
  });

  it('creates deterministic not implemented payloads', () => {
    const payload = createMockApiNotImplementedPayload(
      new Request('http://localhost/api/example?page=1', { method: 'POST' })
    );

    expect(payload).toEqual({
      type: 'about:blank',
      title: 'MOCK_API_NOT_IMPLEMENTED',
      status: 501,
      errorCode: 'MOCK_API_NOT_IMPLEMENTED',
      detail: 'MOCK_API_NOT_IMPLEMENTED: POST /api/example?page=1 尚未在单套 mock 主线中实现',
      instance: '/api/example?page=1',
    });
  });

  it('returns deterministic 501 responses with mock debug headers', async () => {
    mockServer.use(createUnhandledApiHandler('/api'));

    const response = await fetch('http://localhost/api/uncovered/resource?source=test', {
      method: 'PATCH',
    });

    await expect(response.json()).resolves.toEqual({
      type: 'about:blank',
      title: 'MOCK_API_NOT_IMPLEMENTED',
      status: 501,
      errorCode: 'MOCK_API_NOT_IMPLEMENTED',
      detail:
        'MOCK_API_NOT_IMPLEMENTED: PATCH /api/uncovered/resource?source=test 尚未在单套 mock 主线中实现',
      instance: '/api/uncovered/resource?source=test',
    });
    expect(response.status).toBe(501);
    expect(response.headers.get('content-type')).toContain('application/problem+json');
    expect(response.headers.get('x-mock-response')).toBe('true');
    expect(response.headers.get('x-mock-handler')).toBe('unhandled-api');
  });
});
