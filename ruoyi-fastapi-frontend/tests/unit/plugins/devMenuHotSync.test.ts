import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const configMock = {
  isDevMenuSyncEnabled: true,
  devMenuSyncPollIntervalMs: 50,
};
const reloadDynamicRoutes = vi.fn().mockResolvedValue(undefined);
const getDevMenuSignature = vi.fn();
const getToken = vi.fn(() => 'token');

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

describe('dev menu hot sync plugin', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.clearAllMocks();
    getToken.mockReturnValue('token');
    configMock.isDevMenuSyncEnabled = true;
    configMock.devMenuSyncPollIntervalMs = 50;
  });

  afterEach(async () => {
    const plugin = await import('@/plugins/dev-menu-hot-sync');
    plugin.stopDevMenuHotSync();
    vi.useRealTimers();
  });

  it('does not start polling when feature is disabled', async () => {
    configMock.isDevMenuSyncEnabled = false;
    const plugin = await import('@/plugins/dev-menu-hot-sync');
    plugin.startDevMenuHotSync();

    await vi.advanceTimersByTimeAsync(200);
    expect(getDevMenuSignature).not.toHaveBeenCalled();
    expect(reloadDynamicRoutes).not.toHaveBeenCalled();
  });

  it('triggers route reload only when signature changes', async () => {
    getDevMenuSignature
      .mockResolvedValueOnce({ signature: 'sig-a' })
      .mockResolvedValueOnce({ signature: 'sig-a' })
      .mockResolvedValueOnce({ signature: 'sig-b' });

    const plugin = await import('@/plugins/dev-menu-hot-sync');
    plugin.startDevMenuHotSync();

    await vi.advanceTimersByTimeAsync(170);
    expect(getDevMenuSignature).toHaveBeenCalledTimes(4);
    expect(reloadDynamicRoutes).toHaveBeenCalledTimes(1);
    expect(reloadDynamicRoutes).toHaveBeenCalledWith('signature_changed');
  });

  it('keeps polling after request errors', async () => {
    getDevMenuSignature.mockRejectedValueOnce(new Error('503')).mockResolvedValueOnce({ signature: 'sig-a' });

    const plugin = await import('@/plugins/dev-menu-hot-sync');
    plugin.startDevMenuHotSync();

    await vi.advanceTimersByTimeAsync(120);
    expect(getDevMenuSignature).toHaveBeenCalledTimes(3);
    expect(reloadDynamicRoutes).not.toHaveBeenCalled();
  });

  it('skips polling when user is not authenticated', async () => {
    getToken.mockReturnValue('');

    const plugin = await import('@/plugins/dev-menu-hot-sync');
    plugin.startDevMenuHotSync();

    await vi.advanceTimersByTimeAsync(150);
    expect(getDevMenuSignature).not.toHaveBeenCalled();
    expect(reloadDynamicRoutes).not.toHaveBeenCalled();
  });
});
