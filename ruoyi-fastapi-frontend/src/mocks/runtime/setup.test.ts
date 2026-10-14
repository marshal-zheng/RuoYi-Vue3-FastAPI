import { beforeEach, describe, expect, it, vi } from 'vitest';

import type { MockDataSource } from '../store';

const startBrowserMockMock = vi.fn();

vi.mock('../browser', () => ({
  startBrowserMock: (...args: unknown[]) => startBrowserMockMock(...args),
}));

function createDataSource(): MockDataSource {
  return {
    init: vi.fn().mockResolvedValue(undefined),
    reset: vi.fn().mockResolvedValue(undefined),
    auth: {} as MockDataSource['auth'],
    system: {} as MockDataSource['system'],
    project: {} as MockDataSource['project'],
    version: {} as MockDataSource['version'],
    topology: {} as MockDataSource['topology'],
    simulation: {} as MockDataSource['simulation'],
  };
}

describe('setupMockRuntime', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    delete window.__MOCK_RUNTIME__;
    delete window.__MOCK_RUNTIME_BOOTSTRAP__;
    startBrowserMockMock.mockResolvedValue(undefined);
  });

  it('starts fallback runtime with fallback strategy handlers', async () => {
    const dataSource = createDataSource();
    const { setupMockRuntime } = await import('./setup');

    await setupMockRuntime({ mode: 'fallback', apiPrefix: '/api', dataSource });

    expect(dataSource.init).toHaveBeenCalledOnce();
    expect(startBrowserMockMock).toHaveBeenCalledWith(
      expect.objectContaining({
        strategy: 'fallback',
        scenario: 'default',
      })
    );
    expect(window.__MOCK_RUNTIME__).toBeUndefined();
  });

  it('starts demo-offline runtime with debug devtools', async () => {
    const dataSource = createDataSource();
    const { setupMockRuntime } = await import('./setup');

    await setupMockRuntime({ mode: 'demo-offline', apiPrefix: '/api', debug: true, dataSource });

    expect(startBrowserMockMock).toHaveBeenCalledWith(
      expect.objectContaining({
        strategy: 'pure',
        scenario: 'pure',
      })
    );
    expect(window.__MOCK_RUNTIME__?.getMode()).toBe('demo-offline');
    expect(window.__MOCK_RUNTIME__?.getDatasetVersion()).toBe('mock-dataset-v1');

    await window.__MOCK_RUNTIME__?.resetDataset();
    expect(dataSource.reset).toHaveBeenCalledOnce();
  });

  it('applies and clears Playwright bootstrap overlays before first page requests', async () => {
    const dataSource = createDataSource();
    const worker = { resetHandlers: vi.fn() };
    startBrowserMockMock.mockResolvedValue(worker);
    window.__MOCK_RUNTIME_BOOTSTRAP__ = {
      source: 'playwright',
      overlays: ['project-list-empty'],
    };
    const { setupMockRuntime } = await import('./setup');

    await setupMockRuntime({ mode: 'demo-offline', apiPrefix: '/api', debug: true, dataSource });

    expect(window.__MOCK_RUNTIME_BOOTSTRAP__).toBeUndefined();
    expect(window.__MOCK_RUNTIME__?.getOverlayState()).toMatchObject({
      activeIds: ['project-list-empty'],
      source: 'bootstrap',
    });
  });

  it('activates and resets overlays through the runtime debug API', async () => {
    const dataSource = createDataSource();
    const worker = { resetHandlers: vi.fn() };
    startBrowserMockMock.mockResolvedValue(worker);
    const { setupMockRuntime } = await import('./setup');

    await setupMockRuntime({ mode: 'demo-offline', apiPrefix: '/api', debug: true, dataSource });

    await expect(
      window.__MOCK_RUNTIME__?.activateOverlays(['project-list-empty'])
    ).resolves.toMatchObject({
      activeIds: ['project-list-empty'],
      source: 'runtime-api',
    });
    expect(worker.resetHandlers).toHaveBeenCalledTimes(1);

    await expect(window.__MOCK_RUNTIME__?.activateOverlays(['missing-overlay'])).rejects.toThrow(
      /Unknown mock overlay id/
    );
    expect(window.__MOCK_RUNTIME__?.getOverlayState().activeIds).toEqual(['project-list-empty']);

    await expect(window.__MOCK_RUNTIME__?.resetOverlays()).resolves.toMatchObject({
      activeIds: [],
      source: 'none',
    });
    expect(worker.resetHandlers).toHaveBeenCalledTimes(2);
  });

  it('does not expose overlay APIs for fallback mode even when bootstrap exists', async () => {
    const dataSource = createDataSource();
    window.__MOCK_RUNTIME_BOOTSTRAP__ = {
      source: 'playwright',
      overlays: ['project-list-empty'],
    };
    const { setupMockRuntime } = await import('./setup');

    await setupMockRuntime({ mode: 'fallback', apiPrefix: '/api', debug: true, dataSource });

    expect(window.__MOCK_RUNTIME__).toBeUndefined();
  });
});
