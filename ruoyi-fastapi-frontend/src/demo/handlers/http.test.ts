import { describe, expect, it, vi } from 'vitest';

import type { RuntimeConfig } from '@/demo/runtime/mode';
import type { DemoRuntimeLogger } from '@/demo/runtime/logger';

import {
  createDemoApiCatchAllHandler,
  createDemoApiNotImplementedPayload,
  isDemoApiRequest,
} from './http';

const runtimeConfig: RuntimeConfig = {
  mode: 'demo-offline',
  mockMode: 'pure',
  apiPrefix: '/api',
  scenarioId: 'default',
  debug: true,
  source: 'runtime-mode',
};

const logger: DemoRuntimeLogger = {
  debug: vi.fn(),
  info: vi.fn(),
  warn: vi.fn(),
  error: vi.fn(),
};

describe('demo-offline HTTP boundaries', () => {
  it('matches only the configured API prefix', () => {
    expect(isDemoApiRequest(new Request('http://localhost/api'), '/api')).toBe(true);
    expect(isDemoApiRequest(new Request('http://localhost/api/project/list'), '/api')).toBe(true);
    expect(isDemoApiRequest(new Request('http://localhost/apiary/project/list'), '/api')).toBe(
      false
    );
    expect(isDemoApiRequest(new Request('http://localhost/assets/logo.svg'), '/api')).toBe(false);
  });

  it('builds deterministic not-implemented payloads', () => {
    const request = new Request('http://localhost/api/project/unknown?page=1', {
      method: 'POST',
    });

    expect(createDemoApiNotImplementedPayload(request, runtimeConfig)).toEqual({
      type: 'about:blank',
      title: 'Demo API Not Implemented',
      status: 501,
      detail:
        'DEMO_API_NOT_IMPLEMENTED: POST /api/project/unknown?page=1 尚未在 demo-offline 中实现',
      instance: '/api/project/unknown?page=1',
      errorCode: 'DEMO_API_NOT_IMPLEMENTED',
    });
  });

  it('creates a catch-all handler after covered demo handlers', () => {
    const handler = createDemoApiCatchAllHandler(runtimeConfig, logger);

    expect(handler).toBeDefined();
  });
});
