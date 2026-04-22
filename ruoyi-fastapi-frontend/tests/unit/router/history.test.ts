import { beforeEach, describe, expect, it, vi } from 'vitest';

const { createWebHashHistoryMock, createWebHistoryMock, resolveRuntimeConfigMock } = vi.hoisted(() => ({
  createWebHashHistoryMock: vi.fn(() => ({ type: 'hash-history' })),
  createWebHistoryMock: vi.fn(() => ({ type: 'web-history' })),
  resolveRuntimeConfigMock: vi.fn(),
}));

vi.mock('vue-router', () => ({
  createWebHashHistory: createWebHashHistoryMock,
  createWebHistory: createWebHistoryMock,
}));

vi.mock('@/demo/runtime/mode', () => ({
  resolveRuntimeConfig: resolveRuntimeConfigMock,
}));

describe('router history selection', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('uses hash history in demo-offline mode', async () => {
    resolveRuntimeConfigMock.mockReturnValue({ mode: 'demo-offline' });

    const { createAppHistory, isHashRouteMode } = await import('@/router/history');
    const history = createAppHistory();

    expect(history).toEqual({ type: 'hash-history' });
    expect(isHashRouteMode()).toBe(true);
    expect(createWebHashHistoryMock).toHaveBeenCalledTimes(1);
    expect(createWebHistoryMock).not.toHaveBeenCalled();
  });

  it('uses web history outside demo-offline mode', async () => {
    resolveRuntimeConfigMock.mockReturnValue({ mode: 'real' });

    const { createAppHistory, isHashRouteMode } = await import('@/router/history');
    const history = createAppHistory();

    expect(history).toEqual({ type: 'web-history' });
    expect(isHashRouteMode()).toBe(false);
    expect(createWebHistoryMock).toHaveBeenCalledTimes(1);
    expect(createWebHashHistoryMock).not.toHaveBeenCalled();
  });
});
