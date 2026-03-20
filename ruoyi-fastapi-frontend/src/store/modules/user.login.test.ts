import { beforeEach, describe, expect, it, vi } from 'vitest';
import { createPinia, defineStore, setActivePinia } from 'pinia';

const loginMock = vi.fn();
const logoutMock = vi.fn();
const getInfoMock = vi.fn();
const requestMock = vi.fn();

vi.mock('@/api/login', () => ({
  login: (...args: unknown[]) => loginMock(...args),
  logout: (...args: unknown[]) => logoutMock(...args),
  getInfo: (...args: unknown[]) => getInfoMock(...args),
}));

vi.mock('@/utils/request', () => ({
  default: (...args: unknown[]) => requestMock(...args),
}));

describe('user store login flow', () => {
  beforeEach(async () => {
    vi.stubGlobal('defineStore', defineStore);
    setActivePinia(createPinia());
    vi.clearAllMocks();
    const auth = await import('@/utils/auth');
    auth.clearSecurityTokens();
  });

  it('fetches csrf token in silent mode after login', async () => {
    loginMock.mockResolvedValue({ token: 'jwt-token-1' });
    requestMock.mockResolvedValue({ csrfToken: 'csrf-token-1' });

    const useUserStore = (await import('@/store/modules/user')).default;
    const store = useUserStore();
    await store.login({ username: 'admin', password: 'admin123', code: '1234', uuid: 'uuid-1' });

    expect(requestMock).toHaveBeenCalledWith(
      expect.objectContaining({
        url: '/auth/csrf-token',
        method: 'post',
        silentSuccess: true,
      })
    );
  });

  it('restores session silently via refresh endpoint', async () => {
    requestMock.mockResolvedValue({
      token: 'jwt-token-restored',
      csrfToken: 'csrf-token-restored',
    });

    const useUserStore = (await import('@/store/modules/user')).default;
    const store = useUserStore();
    const restored = await store.restoreSession();

    expect(restored).toBe(true);
    expect(store.token).toBe('jwt-token-restored');
    expect(requestMock).toHaveBeenCalledWith(
      expect.objectContaining({
        url: '/auth/refresh',
        method: 'post',
        isToken: false,
        silentSuccess: true,
        silentError: true,
      })
    );
  });
});
