import { API_PREFIX } from '../constants';
import { mockDataset } from '../data';
import { createMockHandlers } from '../handlers';
import { startBrowserMock } from '../browser';
import { createMockOverlayRuntime, type MockOverlayRuntime } from '../overlays/runtime';
import type { MockOverlayRegistrySummary, MockOverlayState } from '../overlays';
import type { MockDataSource } from '../store';
import { getMockDataSource } from '../store';
import type { MockNetworkStrategy, MockRuntimeHandler, OnUnhandledRequestOption } from '../types';
import type { MockRuntimeMode } from './mode';
import { strategyForRuntimeMode } from './mode';

export interface MockRuntimeSetupOptions {
  mode: MockRuntimeMode;
  apiPrefix?: string;
  debug?: boolean;
  dataSource?: MockDataSource;
  onUnhandledRequest?: OnUnhandledRequestOption;
}

export interface MockRuntimeDevtools {
  getMode(): MockRuntimeMode;
  getDatasetVersion(): string;
  resetDataset(): Promise<void>;
  exportDatasetSnapshot(): Promise<unknown>;
  listOverlays(): MockOverlayRegistrySummary[];
  getOverlayState(): MockOverlayState;
  activateOverlays(ids: string[]): Promise<MockOverlayState>;
  resetOverlays(): Promise<MockOverlayState>;
}

declare global {
  interface Window {
    __MOCK_RUNTIME__?: MockRuntimeDevtools;
    __MOCK_RUNTIME_BOOTSTRAP__?: {
      source: 'playwright' | 'vitest';
      overlays?: string[];
    };
  }
}

function createRuntimeDevtools(
  mode: MockRuntimeMode,
  dataSource: MockDataSource,
  overlayRuntime: MockOverlayRuntime,
  rebuildHandlers: () => void
): MockRuntimeDevtools {
  return {
    getMode: () => mode,
    getDatasetVersion: () => mockDataset.version,
    resetDataset: () => dataSource.reset(),
    exportDatasetSnapshot: async () => mockDataset,
    listOverlays: () => overlayRuntime.listOverlays(),
    getOverlayState: () => overlayRuntime.getOverlayState(),
    activateOverlays: async (ids: string[]) => {
      const state = overlayRuntime.activateOverlays(ids, 'runtime-api');
      rebuildHandlers();
      return state;
    },
    resetOverlays: async () => {
      const state = overlayRuntime.resetOverlays();
      rebuildHandlers();
      return state;
    },
  };
}

function scenarioForStrategy(strategy: MockNetworkStrategy) {
  return strategy === 'pure' ? 'pure' : 'default';
}

export async function setupMockRuntime(options: MockRuntimeSetupOptions): Promise<void> {
  const apiPrefix = options.apiPrefix ?? API_PREFIX;
  const dataSource = options.dataSource ?? getMockDataSource();
  const strategy = strategyForRuntimeMode(options.mode);
  const canUseOverlayApi =
    options.mode === 'demo-offline' && (options.debug || import.meta.env.MODE === 'test');
  const bootstrap =
    canUseOverlayApi && typeof window !== 'undefined'
      ? window.__MOCK_RUNTIME_BOOTSTRAP__
      : undefined;
  const overlayRuntime = createMockOverlayRuntime({
    allowOverlays: canUseOverlayApi,
    initialOverlays: bootstrap?.overlays,
    source: bootstrap?.source === 'vitest' ? 'vitest' : 'bootstrap',
  });
  const handlers: MockRuntimeHandler[] = createMockHandlers({
    strategy,
    dataSource,
    apiPrefix,
    onMissingCapability: options.mode === 'demo-offline' ? 'error' : 'passthrough',
    overlays: overlayRuntime.getOverlayState(),
  });

  await dataSource.init();
  const worker = await startBrowserMock({
    strategy,
    scenario: scenarioForStrategy(strategy),
    handlers,
    onUnhandledRequest: options.onUnhandledRequest ?? 'bypass',
  });

  const rebuildHandlers = () => {
    const nextHandlers = createMockHandlers({
      strategy,
      dataSource,
      apiPrefix,
      onMissingCapability: options.mode === 'demo-offline' ? 'error' : 'passthrough',
      overlays: overlayRuntime.getOverlayState(),
    });
    worker?.resetHandlers(...nextHandlers);
    if (typeof window !== 'undefined') {
      window.__MSW_RUNTIME_HANDLERS__ = nextHandlers;
    }
  };

  if (typeof window !== 'undefined') {
    delete window.__MOCK_RUNTIME_BOOTSTRAP__;
  }

  if (canUseOverlayApi && typeof window !== 'undefined') {
    window.__MOCK_RUNTIME__ = createRuntimeDevtools(
      options.mode,
      dataSource,
      overlayRuntime,
      rebuildHandlers
    );
  }
}
