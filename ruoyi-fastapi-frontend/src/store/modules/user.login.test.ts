import { beforeEach, describe, expect, it, vi } from 'vitest';
import { createPinia, defineStore, setActivePinia } from 'pinia';

import {
  createApiContractHandlers,
  createStatusHandler,
} from '../../../tests/mocks/api-contract-handlers';
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
  beforeEach(async () => {
    vi.stubGlobal('defineStore', defineStore);
    setActivePinia(createPinia());
    vi.clearAllMocks();
    mockServer.use(...createApiContractHandlers());
    const auth = await import('@/utils/auth');
    auth.clearSecurityTokens();
  });

  it('fetches csrf token through MSW after login when the login response has no csrf token', async () => {
    loginMock.mockResolvedValue({ token: 'jwt-token-1' });

    const useUserStore = (await import('@/store/modules/user')).default;
    const store = useUserStore();
    await store.login({ username: 'admin', password: 'admin123', code: '1234', uuid: 'uuid-1' });

    expect(store.token).toBe('jwt-token-1');
  });

  it('restores session silently via refresh endpoint', async () => {
    const useUserStore = (await import('@/store/modules/user')).default;
    const store = useUserStore();
    const restored = await store.restoreSession();

    expect(restored).toBe(true);
    expect(store.token).toBe('jwt-token-restored');
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
});
