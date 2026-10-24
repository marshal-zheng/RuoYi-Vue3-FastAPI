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

describe('dev-menu SSE session lifecycle', () => {
  class Source {
    static instances: Source[] = [];
    listeners = new Map<string, EventListener>();
    onerror?: () => void;
    close = vi.fn();
    constructor() {
      Source.instances.push(this);
    }
    addEventListener(name: string, handler: EventListener) {
      this.listeners.set(name, handler);
    }
  }
  beforeEach(async () => {
    vi.resetModules();
    vi.clearAllMocks();
    vi.useFakeTimers();
    configMock.isDevMenuSyncEnabled = true;
    configMock.isDevMenuSyncSseEnabled = true;
    configMock.isDevMenuSyncPollingEnabled = false;
    configMock.devMenuSyncMode = 'sse';
    getTokenMock.mockReturnValue('access');
    getDevMenuSignatureMock.mockResolvedValue({ signature: 'stable' });
    Source.instances = [];
    vi.stubGlobal('EventSource', Source);
    const { setQuerySession } = await import('@/queries/context');
    setQuerySession('qa-sse', ['admin'], []);
  });
  afterEach(async () => {
    (await import('@/plugins/dev-menu-hot-sync')).stopDevMenuHotSync();
    (await import('@/queries/context')).endQuerySession();
    vi.clearAllTimers();
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it('probes authenticated HTTP before connecting and reconnects after an error', async () => {
    const plugin = await import('@/plugins/dev-menu-hot-sync');
    plugin.startDevMenuHotSync();
    await flushMicrotasks();
    expect(getDevMenuSignatureMock).toHaveBeenCalledTimes(1);
    expect(Source.instances).toHaveLength(1);
    Source.instances[0].onerror?.();
    await flushMicrotasks();
    await vi.advanceTimersByTimeAsync(1000);
    await flushMicrotasks();
    expect(Source.instances[0].close).toHaveBeenCalledOnce();
    expect(Source.instances).toHaveLength(2);
  });

  it('does not open an EventSource after a pending probe is stopped', async () => {
    let resolve!: (value: unknown) => void;
    getDevMenuSignatureMock.mockReturnValue(
      new Promise((done) => {
        resolve = done;
      })
    );
    const plugin = await import('@/plugins/dev-menu-hot-sync');
    plugin.startDevMenuHotSync();
    plugin.stopDevMenuHotSync();
    resolve({ signature: 'late' });
    await flushMicrotasks();
    expect(Source.instances).toHaveLength(0);
  });

  it('closes on logout and ignores the old source error callback', async () => {
    const plugin = await import('@/plugins/dev-menu-hot-sync');
    plugin.startDevMenuHotSync();
    await flushMicrotasks();
    const old = Source.instances[0];
    (await import('@/queries/context')).endQuerySession();
    getTokenMock.mockReturnValue('');
    old.onerror?.();
    await vi.advanceTimersByTimeAsync(60000);
    expect(old.close).toHaveBeenCalledOnce();
    expect(Source.instances).toHaveLength(1);
  });

  it('does not open a socket when the session probe is unauthorized', async () => {
    getDevMenuSignatureMock.mockRejectedValue({ status: 401 });
    const plugin = await import('@/plugins/dev-menu-hot-sync');
    plugin.startDevMenuHotSync();
    await flushMicrotasks();
    expect(Source.instances).toHaveLength(0);
  });
});
