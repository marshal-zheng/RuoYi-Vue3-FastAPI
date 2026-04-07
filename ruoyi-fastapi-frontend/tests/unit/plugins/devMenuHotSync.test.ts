import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const configMock = {
  isDevMenuSyncEnabled: true,
  isDevMenuSyncSseEnabled: true,
  isDevMenuSyncPollingEnabled: false,
  devMenuSyncMode: 'sse',
  devMenuSyncPollIntervalMs: 50,
};

const reloadDynamicRoutes = vi.fn().mockResolvedValue(undefined);
const getDevMenuSignature = vi.fn();
const getToken = vi.fn(() => 'token');

class FakeEventSource {
  static instances: FakeEventSource[] = [];

  public onerror: ((event: Event) => void) | null = null;
  public readonly listeners = new Map<string, Set<(event: Event) => void>>();
  public readonly url: string;
  public readonly withCredentials: boolean;
  public closed = false;

  constructor(url: string, init?: EventSourceInit) {
    this.url = url;
    this.withCredentials = init?.withCredentials === true;
    FakeEventSource.instances.push(this);
  }

  addEventListener(type: string, listener: (event: Event) => void): void {
    if (!this.listeners.has(type)) {
      this.listeners.set(type, new Set());
    }
    this.listeners.get(type)?.add(listener);
  }

  removeEventListener(type: string, listener: (event: Event) => void): void {
    this.listeners.get(type)?.delete(listener);
  }

  close(): void {
    this.closed = true;
  }

  emit(type: string, event: Event): void {
    if (type === 'error') {
      this.onerror?.(event);
    }
    this.listeners.get(type)?.forEach((listener) => listener(event));
  }
}

vi.mock('@/config/devMenuSync', () => configMock);
vi.mock('@/api/system/devMenuSync', () => ({
  getDevMenuSignature,
}));
vi.mock('@/utils/auth', () => ({
  getToken,
}));
vi.mock('@/store/modules/permission', () => ({
  default: () => ({
    reloadDynamicRoutes,
  }),
}));

const flushMicrotasks = async (): Promise<void> => {
  await Promise.resolve();
  await Promise.resolve();
  await Promise.resolve();
};

describe('dev menu hot sync plugin', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.resetModules();
    vi.clearAllMocks();
    FakeEventSource.instances = [];
    getToken.mockReturnValue('token');
    configMock.isDevMenuSyncEnabled = true;
    configMock.isDevMenuSyncSseEnabled = true;
    configMock.isDevMenuSyncPollingEnabled = false;
    configMock.devMenuSyncMode = 'sse';
    configMock.devMenuSyncPollIntervalMs = 50;
    vi.spyOn(console, 'info').mockImplementation(() => undefined);
    vi.spyOn(console, 'warn').mockImplementation(() => undefined);
    vi.spyOn(console, 'error').mockImplementation(() => undefined);
    vi.stubGlobal('EventSource', FakeEventSource);
  });

  afterEach(async () => {
    const plugin = await import('@/plugins/dev-menu-hot-sync');
    plugin.stopDevMenuHotSync();
    vi.runOnlyPendingTimers();
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  it('does not start auto sync when feature is disabled', async () => {
    configMock.isDevMenuSyncEnabled = false;
    configMock.isDevMenuSyncSseEnabled = false;
    const plugin = await import('@/plugins/dev-menu-hot-sync');

    plugin.startDevMenuHotSync();
    await flushMicrotasks();

    expect(FakeEventSource.instances).toHaveLength(0);
    expect(getDevMenuSignature).not.toHaveBeenCalled();
    expect(reloadDynamicRoutes).not.toHaveBeenCalled();
  });

  it('reloads dynamic routes when SSE menu_changed event arrives', async () => {
    const plugin = await import('@/plugins/dev-menu-hot-sync');

    plugin.startDevMenuHotSync();
    await flushMicrotasks();

    expect(FakeEventSource.instances).toHaveLength(1);
    const source = FakeEventSource.instances[0];
    expect(source.url).toBe('/api/dev/menu/events');
    expect(source.withCredentials).toBe(true);

    source.emit('open', new Event('open'));
    source.emit(
      'menu_changed',
      new MessageEvent('menu_changed', {
        data: JSON.stringify({ trigger: 'file_change', compiledChecksum: 'checksum-1' }),
      })
    );
    await flushMicrotasks();

    expect(reloadDynamicRoutes).toHaveBeenCalledTimes(1);
    expect(reloadDynamicRoutes).toHaveBeenCalledWith('sse_menu_changed');
  });

  it('silently disables hot sync when SSE probe returns 404', async () => {
    getDevMenuSignature.mockRejectedValue({ response: { status: 404 } });
    const plugin = await import('@/plugins/dev-menu-hot-sync');

    plugin.startDevMenuHotSync();
    await flushMicrotasks();

    const firstSource = FakeEventSource.instances[0];
    firstSource.emit('error', new Event('error'));
    await flushMicrotasks();
    await vi.runAllTimersAsync();

    expect(getDevMenuSignature).toHaveBeenCalledTimes(1);
    expect(FakeEventSource.instances).toHaveLength(1);
    expect(firstSource.closed).toBe(true);
    expect(reloadDynamicRoutes).not.toHaveBeenCalled();
  });

  it('falls back to signature polling after repeated SSE failures', async () => {
    getDevMenuSignature
      .mockResolvedValueOnce({ signature: 'sig-a' })
      .mockResolvedValueOnce({ signature: 'sig-a' })
      .mockResolvedValueOnce({ signature: 'sig-a' })
      .mockResolvedValueOnce({ signature: 'sig-b' });

    const plugin = await import('@/plugins/dev-menu-hot-sync');
    plugin.startDevMenuHotSync();
    await flushMicrotasks();

    for (let index = 0; index < 2; index += 1) {
      FakeEventSource.instances.at(-1)?.emit('error', new Event('error'));
      await flushMicrotasks();
      await vi.advanceTimersByTimeAsync(1000 * 2 ** index);
    }

    FakeEventSource.instances.at(-1)?.emit('error', new Event('error'));
    await flushMicrotasks();

    expect(getDevMenuSignature).toHaveBeenCalledTimes(4);
    expect(reloadDynamicRoutes).toHaveBeenCalledTimes(1);
    expect(reloadDynamicRoutes).toHaveBeenCalledWith('signature_changed_fallback');
  });

  it('exposes manual refresh API for fallback troubleshooting', async () => {
    const plugin = await import('@/plugins/dev-menu-hot-sync');

    plugin.startDevMenuHotSync();
    await flushMicrotasks();

    expect(window.__DEV_MENU_SYNC__).toBeDefined();

    await window.__DEV_MENU_SYNC__?.refreshRoutes();

    expect(reloadDynamicRoutes).toHaveBeenCalledTimes(1);
    expect(reloadDynamicRoutes).toHaveBeenCalledWith('manual_console_refresh');
  });
});
