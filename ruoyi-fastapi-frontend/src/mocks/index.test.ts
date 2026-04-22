import { beforeEach, describe, expect, it, vi } from 'vitest';

import type { MockRuntimeHandler } from './types';

const resolveRuntimeConfigMock = vi.fn();
const startBrowserMockMock = vi.fn();

vi.mock('@/demo/runtime/mode', () => ({
  resolveRuntimeConfig: (...args: unknown[]) => resolveRuntimeConfigMock(...args),
}));

vi.mock('./browser', () => ({
  startBrowserMock: (...args: unknown[]) => startBrowserMockMock(...args),
}));

describe('setupBrowserMocks', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    resolveRuntimeConfigMock.mockReturnValue({
      mockMode: 'fallback',
    });
    startBrowserMockMock.mockResolvedValue(undefined);
  });

  it('forwards custom runtime handlers to the browser worker', async () => {
    const customHandlers = [{ tag: 'demo-offline-handler' }] as unknown as MockRuntimeHandler[];
    const onUnhandledRequest = vi.fn();

    const { setupBrowserMocks } = await import('./index');
    await setupBrowserMocks({
      strategy: 'pure',
      handlers: customHandlers,
      onUnhandledRequest,
    });

    expect(startBrowserMockMock).toHaveBeenCalledWith({
      strategy: 'pure',
      scenario: 'pure',
      handlers: customHandlers,
      onUnhandledRequest,
    });
  });

  it('does not start the worker when mock mode is off and no strategy is provided', async () => {
    resolveRuntimeConfigMock.mockReturnValue({
      mockMode: 'off',
    });

    const { setupBrowserMocks } = await import('./index');
    await expect(setupBrowserMocks()).resolves.toBeUndefined();

    expect(startBrowserMockMock).not.toHaveBeenCalled();
  });
});
