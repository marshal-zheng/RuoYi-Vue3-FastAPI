import 'fake-indexeddb/auto';

import { afterEach, describe, expect, it, vi } from 'vitest';

import type { RuntimeConfig } from './mode';
import type { DemoRuntimeLogger } from './logger';
import type { DemoRuntimeSnapshot } from './state';
import { clearDemoRuntimeDevtools, exposeDemoRuntimeDevtools } from './devtools';
import { getDemoOfflineDb, replaceDemoOfflineDb } from '@/demo/db';

const logger: DemoRuntimeLogger = {
  debug: vi.fn(),
  info: vi.fn(),
  warn: vi.fn(),
  error: vi.fn(),
};

const runtimeConfig: RuntimeConfig = {
  mode: 'demo-offline',
  mockMode: 'pure',
  apiPrefix: '/api',
  scenarioId: 'default',
  debug: true,
  source: 'runtime-mode',
};

const snapshot: DemoRuntimeSnapshot = {
  mode: 'demo-offline',
  apiPrefix: '/api',
  debug: true,
  persistence: 'indexeddb',
  dbName: 'ruoyi-demo-offline',
  startedAt: '2026-04-11T00:00:00.000Z',
  scenario: {
    id: 'default',
    name: 'default',
    version: '1.0.0',
    schemaVersion: 1,
    fingerprint: 'default:runtime-boundary',
    loadedAt: '2026-04-11T00:00:00.000Z',
  },
};

describe('demo runtime devtools', () => {
  afterEach(async () => {
    clearDemoRuntimeDevtools();
    await getDemoOfflineDb().delete();
    replaceDemoOfflineDb(undefined);
    vi.clearAllMocks();
  });

  it('exposes __DEMO_RUNTIME__ only when debug is enabled', () => {
    exposeDemoRuntimeDevtools(runtimeConfig, snapshot, logger);

    expect(window.__DEMO_RUNTIME__?.getMode()).toBe('demo-offline');
    expect(window.__DEMO_RUNTIME__?.getScenario()).toMatchObject({
      id: 'default',
      schemaVersion: 1,
    });
  });

  it('clears __DEMO_RUNTIME__ when debug is disabled', () => {
    exposeDemoRuntimeDevtools(runtimeConfig, snapshot, logger);
    exposeDemoRuntimeDevtools({ ...runtimeConfig, debug: false }, snapshot, logger);

    expect(window.__DEMO_RUNTIME__).toBeUndefined();
  });

  it('provides explicit reset and export operations', async () => {
    exposeDemoRuntimeDevtools(runtimeConfig, snapshot, logger);

    await expect(window.__DEMO_RUNTIME__?.resetScenario()).resolves.toMatchObject({
      id: 'default',
      schemaVersion: 1,
    });
    await expect(window.__DEMO_RUNTIME__?.exportScenario()).resolves.toMatchObject({
      schemaVersion: 1,
    });
  });
});
