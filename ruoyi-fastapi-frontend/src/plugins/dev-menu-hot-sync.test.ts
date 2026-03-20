import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const getDevMenuSignatureMock = vi.fn();
const reloadDynamicRoutesMock = vi.fn();
const getTokenMock = vi.fn();

vi.mock('@/api/system/devMenuSync', () => ({
  getDevMenuSignature: (...args: unknown[]) => getDevMenuSignatureMock(...args),
}));

vi.mock('@/config/devMenuSync', () => ({
  isDevMenuSyncEnabled: true,
  isDevMenuSyncPollingEnabled: true,
  devMenuSyncMode: 'poll',
  devMenuSyncPollIntervalMs: 1000,
}));

vi.mock('@/store/modules/permission', () => ({
  default: () => ({
    reloadDynamicRoutes: (...args: unknown[]) => reloadDynamicRoutesMock(...args),
  }),
}));

vi.mock('@/utils/auth', () => ({
  getToken: () => getTokenMock(),
}));

const flushMicrotasks = async (): Promise<void> => {
  await Promise.resolve();
  await Promise.resolve();
};

describe('dev-menu-hot-sync', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.resetModules();
    vi.clearAllMocks();
  });

  afterEach(async () => {
    const plugin = await import('@/plugins/dev-menu-hot-sync');
    plugin.stopDevMenuHotSync();
    vi.runOnlyPendingTimers();
    vi.useRealTimers();
  });

  it('polls signature on interval when authenticated', async () => {
    getTokenMock.mockReturnValue('jwt-token');
    getDevMenuSignatureMock.mockResolvedValue({ signature: 'sig-1' });

    const plugin = await import('@/plugins/dev-menu-hot-sync');
    plugin.startDevMenuHotSync();
    await flushMicrotasks();

    expect(getDevMenuSignatureMock).toHaveBeenCalledTimes(1);

    vi.advanceTimersByTime(1000);
    await flushMicrotasks();
    expect(getDevMenuSignatureMock).toHaveBeenCalledTimes(2);
  });

  it('suspends polling for 60s after 401 and then retries', async () => {
    getTokenMock.mockReturnValue('jwt-token');
    getDevMenuSignatureMock.mockRejectedValueOnce({ response: { status: 401 } });
    getDevMenuSignatureMock.mockResolvedValue({ signature: 'sig-2' });

    const plugin = await import('@/plugins/dev-menu-hot-sync');
    plugin.startDevMenuHotSync();
    await flushMicrotasks();

    expect(getDevMenuSignatureMock).toHaveBeenCalledTimes(1);

    vi.advanceTimersByTime(59_000);
    await flushMicrotasks();
    expect(getDevMenuSignatureMock).toHaveBeenCalledTimes(1);

    vi.advanceTimersByTime(1000);
    await flushMicrotasks();
    expect(getDevMenuSignatureMock).toHaveBeenCalledTimes(2);
  });
});
