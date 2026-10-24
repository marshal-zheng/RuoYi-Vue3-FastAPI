import { beforeEach, describe, expect, it, vi } from 'vitest';
import { http as mswHttp, HttpResponse } from 'msw';
import { createPinia, defineStore, setActivePinia } from 'pinia';

import { createStatusHandler } from '@/mocks/handlers/error-common';
import { setupMainlineMockHandlers } from '../../../tests/mocks/mainline';
import { mockServer } from '../../../tests/mocks/server';

const loginMock = vi.fn();
const logoutMock = vi.fn();
const getInfoMock = vi.fn();

vi.mock('@/api/login', () => ({
  login: (...args: unknown[]) => loginMock(...args),
  logout: (...args: unknown[]) => logoutMock(...args),
  getInfo: (...args: unknown[]) => getInfoMock(...args),
}));

describe('user store login flow', () => {
  setupMainlineMockHandlers();

  beforeEach(async () => {
    vi.stubGlobal('defineStore', defineStore);
    setActivePinia(createPinia());
    vi.clearAllMocks();
    const auth = await import('@/utils/auth');
    auth.clearSecurityTokens();
  });

  it('fetches csrf token through MSW after login when the login response has no csrf token', async () => {
    loginMock.mockResolvedValue({ token: 'jwt-token-1' });

    const useUserStore = (await import('@/store/modules/user')).default;
    const store = useUserStore();
    await store.login({
      username: 'admin',
      password: 'admin123',
      code: '1234',
      uuid: 'uuid-1',
    });

    expect(store.token).toBe('jwt-token-1');
  });

  it('restores session silently via refresh endpoint', async () => {
    const useUserStore = (await import('@/store/modules/user')).default;
    const store = useUserStore();
    const restored = await store.restoreSession();

    expect(restored).toBe(true);
    expect(store.token).toContain('mock-session-admin-');
  });

  it('clears local session when refresh endpoint rejects the session', async () => {
    mockServer.use(createStatusHandler('post', '/auth/refresh', 401));

    const useUserStore = (await import('@/store/modules/user')).default;
    const store = useUserStore();
    store.token = 'stale-token';

    await expect(store.restoreSession()).resolves.toBe(false);
    expect(store.token).toBe('');
  });

  it('passes silent options when logging out', async () => {
    logoutMock.mockResolvedValue(undefined);

    const useUserStore = (await import('@/store/modules/user')).default;
    const store = useUserStore();
    await store.logOut({ silentSuccess: true, silentError: true });

    expect(logoutMock).toHaveBeenCalledWith({
      silentSuccess: true,
      silentError: true,
    });
  });

  it('does not let an old restore failure clear a successful replacement login', async () => {
    let release!: () => void;
    let started!: () => void;
    const waiting = new Promise<void>((resolve) => {
      release = resolve;
    });
    const entered = new Promise<void>((resolve) => {
      started = resolve;
    });
    mockServer.use(
      mswHttp.post('*/auth/refresh', async () => {
        started();
        await waiting;
        return HttpResponse.json({ token: 'old-restored-token', csrfToken: 'old-csrf' });
      })
    );
    const useUserStore = (await import('@/store/modules/user')).default;
    const store = useUserStore();
    const restoring = store.restoreSession();
    await entered;
    loginMock.mockResolvedValue({ token: 'new-login-token', csrfToken: 'new-login-csrf' });
    await store.login({ username: 'admin', password: 'admin123', code: '', uuid: '' });
    release();
    await expect(restoring).resolves.toBe(false);
    expect(store.token).toBe('new-login-token');
    expect((await import('@/utils/auth')).getToken()).toBe('new-login-token');
  });
});
