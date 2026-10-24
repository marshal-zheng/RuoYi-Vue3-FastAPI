/**
 * Unit tests for user store
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useUserStore } from '@/store/modules/user';
import { login as loginApi, logout as logoutApi, getInfo as getInfoApi } from '@/api/login';
import { clearSecurityTokens, getToken, setCsrfToken, setToken } from '@/utils/auth';
import { createStatusHandler } from '@/mocks/handlers/error-common';
import { setupMainlineMockHandlers } from '../../mocks/mainline';
import { mockServer } from '../../mocks/server';

vi.mock('@/api/login', () => ({
  login: vi.fn(),
  logout: vi.fn(),
  getInfo: vi.fn(),
}));

vi.mock('@/utils/auth', () => ({
  clearSecurityTokens: vi.fn(),
  getCsrfToken: vi.fn(() => ''),
  getToken: vi.fn(() => ''),
  setCsrfToken: vi.fn(),
  setToken: vi.fn(),
}));

describe('User Store', () => {
  setupMainlineMockHandlers();

  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
    vi.mocked(getToken).mockReturnValue('');
  });

  describe('Initial State', () => {
    it('should initialize with empty defaults', () => {
      const store = useUserStore();

      expect(store.token).toBe('');
      expect(store.id).toBe('');
      expect(store.name).toBe('');
      expect(store.nickName).toBe('');
      expect(store.avatar).toBe('');
      expect(store.roles).toEqual([]);
      expect(store.permissions).toEqual([]);
    });

    it('should initialize token from auth storage', () => {
      vi.mocked(getToken).mockReturnValue('stored-token');

      const store = useUserStore();

      expect(store.token).toBe('stored-token');
    });
  });

  describe('Login', () => {
    it('should login successfully and use csrf token from login response', async () => {
      const store = useUserStore();
      vi.mocked(loginApi).mockResolvedValue({
        token: 'test-token-123',
        csrfToken: 'csrf-token-123',
      } as any);

      await store.login({
        username: 'admin',
        password: 'admin123',
        code: '1234',
        uuid: 'uuid-1',
      });

      expect(loginApi).toHaveBeenCalledWith('admin', 'admin123', '1234', 'uuid-1');
      expect(setToken).toHaveBeenCalledWith('test-token-123');
      expect(setCsrfToken).toHaveBeenCalledWith('csrf-token-123');
      expect(store.token).toBe('test-token-123');
      expect(setCsrfToken).toHaveBeenCalledTimes(1);
    });

    it('should request csrf token when login response does not include one', async () => {
      const store = useUserStore();
      vi.mocked(loginApi).mockResolvedValue({ token: 'test-token-123' } as any);

      await store.login({
        username: 'admin',
        password: 'admin123',
        code: '1234',
        uuid: 'uuid-1',
      });

      expect(setCsrfToken).toHaveBeenCalledWith('mock-csrf-token');
    });

    it('should handle login failure', async () => {
      const store = useUserStore();
      vi.mocked(loginApi).mockRejectedValue(new Error('用户名或密码错误'));

      await expect(
        store.login({
          username: 'wrong',
          password: 'wrong',
          code: '1234',
          uuid: 'uuid-1',
        })
      ).rejects.toThrow('用户名或密码错误');

      expect(store.token).toBe('');
    });
  });

  describe('Session Restore', () => {
    it('should restore session when refresh returns token', async () => {
      const store = useUserStore();

      await expect(store.restoreSession()).resolves.toBe(true);

      expect(setToken).toHaveBeenCalledWith(expect.stringContaining('mock-session-admin-'));
      expect(setCsrfToken).toHaveBeenCalledWith('mock-csrf-refreshed');
      expect(store.token).toContain('mock-session-admin-');
    });

    it('should clear local security state when refresh fails', async () => {
      const store = useUserStore();
      store.token = 'stale-token';
      mockServer.use(createStatusHandler('post', '/auth/refresh', 401));

      await expect(store.restoreSession()).resolves.toBe(false);

      expect(clearSecurityTokens).toHaveBeenCalled();
      expect(store.token).toBe('');
    });
  });

  describe('Get Info', () => {
    it('should fetch user info successfully', async () => {
      const store = useUserStore();
      vi.mocked(getInfoApi).mockResolvedValue({
        user: {
          userId: 1,
          userName: 'admin',
          nickName: '管理员',
          avatar: '',
        },
        roles: ['admin'],
        permissions: ['*:*:*'],
      } as any);

      await store.getInfo();

      expect(store.id).toBe(1);
      expect(store.name).toBe('admin');
      expect(store.nickName).toBe('管理员');
      expect(store.roles).toEqual(['admin']);
      expect(store.permissions).toEqual(['*:*:*']);
      expect(store.avatar).toBeTruthy();
    });

    it('should fall back to default role when roles are empty', async () => {
      const store = useUserStore();
      vi.mocked(getInfoApi).mockResolvedValue({
        user: {
          userId: 2,
          userName: 'guest',
          nickName: '访客',
          avatar: '',
        },
        roles: [],
        permissions: [],
      } as any);

      await store.getInfo();

      expect(store.roles).toEqual(['ROLE_DEFAULT']);
    });

    it('should handle getInfo failure', async () => {
      const store = useUserStore();
      vi.mocked(getInfoApi).mockRejectedValue(new Error('Unauthorized'));

      await expect(store.getInfo()).rejects.toThrow('Unauthorized');
    });
  });

  describe('Logout', () => {
    it('should logout successfully', async () => {
      const store = useUserStore();
      store.token = 'test-token';
      store.roles = ['admin'];
      store.permissions = ['*:*:*'];
      vi.mocked(logoutApi).mockResolvedValue({ code: 200 } as any);

      await store.logOut();

      expect(logoutApi).toHaveBeenCalled();
      expect(store.token).toBe('');
      expect(store.roles).toEqual([]);
      expect(store.permissions).toEqual([]);
      expect(clearSecurityTokens).toHaveBeenCalled();
    });

    it('should clear state even if logout API fails', async () => {
      const store = useUserStore();
      store.token = 'test-token';
      store.roles = ['admin'];
      vi.mocked(logoutApi).mockRejectedValue(new Error('Network error'));

      await store.logOut();

      expect(store.token).toBe('');
      expect(store.roles).toEqual([]);
      expect(store.permissions).toEqual([]);
      expect(clearSecurityTokens).toHaveBeenCalled();
    });
  });
});
