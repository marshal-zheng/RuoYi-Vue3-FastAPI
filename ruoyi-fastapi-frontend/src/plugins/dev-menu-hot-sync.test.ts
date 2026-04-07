import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const getDevMenuSignatureMock = vi.fn();
const reloadDynamicRoutesMock = vi.fn().mockResolvedValue(undefined);
const getTokenMock = vi.fn();

const configMock = {
  isDevMenuSyncEnabled: true,
  isDevMenuSyncSseEnabled: false,
  isDevMenuSyncPollingEnabled: true,
  devMenuSyncMode: 'poll',
  devMenuSyncPollIntervalMs: 1000,
};

vi.mock('@/api/system/devMenuSync', () => ({
  getDevMenuSignature: (...args: unknown[]) => getDevMenuSignatureMock(...args),
}));

vi.mock('@/config/devMenuSync', () => configMock);

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
  await Promise.resolve();
};

describe('dev-menu-hot-sync', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.resetModules();
    vi.clearAllMocks();
    configMock.isDevMenuSyncEnabled = true;
    configMock.isDevMenuSyncSseEnabled = false;
    configMock.isDevMenuSyncPollingEnabled = true;
    configMock.devMenuSyncMode = 'poll';
    configMock.devMenuSyncPollIntervalMs = 1000;
    getTokenMock.mockReturnValue('jwt-token');
    vi.spyOn(console, 'info').mockImplementation(() => undefined);
    vi.spyOn(console, 'warn').mockImplementation(() => undefined);
    vi.spyOn(console, 'error').mockImplementation(() => undefined);
  });

  afterEach(async () => {
    const plugin = await import('@/plugins/dev-menu-hot-sync');
    plugin.stopDevMenuHotSync();
    vi.runOnlyPendingTimers();
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  it('polls signature on interval in explicit poll mode', async () => {
    getDevMenuSignatureMock.mockResolvedValue({ signature: 'sig-1' });

    const plugin = await import('@/plugins/dev-menu-hot-sync');
    plugin.startDevMenuHotSync();
    await flushMicrotasks();

    expect(getDevMenuSignatureMock).toHaveBeenCalledTimes(1);

    vi.advanceTimersByTime(1000);
    await flushMicrotasks();
    expect(getDevMenuSignatureMock).toHaveBeenCalledTimes(2);
  });

  it('suspends signature fallback for 60s after auth failure', async () => {
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

  it('does not start automatic sync in manual mode', async () => {
    configMock.isDevMenuSyncPollingEnabled = false;
    configMock.devMenuSyncMode = 'manual';

    const plugin = await import('@/plugins/dev-menu-hot-sync');
    plugin.startDevMenuHotSync();
    await flushMicrotasks();

    expect(getDevMenuSignatureMock).not.toHaveBeenCalled();
    expect(reloadDynamicRoutesMock).not.toHaveBeenCalled();
  });
});
