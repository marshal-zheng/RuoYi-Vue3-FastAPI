/**
 * Auth 工具函数测试
 * 测试 Token 管理功能
 */
import { beforeEach, describe, expect, it } from 'vitest';
import {
  clearSecurityTokens,
  getCsrfToken,
  getToken,
  removeToken,
  setCsrfToken,
  setToken,
} from '@/utils/auth';

describe('Auth Utils', () => {
  beforeEach(() => {
    sessionStorage.clear();
    document.cookie = 'csrf_token=; Max-Age=0; path=/';
    clearSecurityTokens();
  });

  describe('getToken', () => {
    it('should return undefined when no token exists', () => {
      expect(getToken()).toBeUndefined();
    });

    it('should return the in-memory token after setToken', () => {
      setToken('test-token-123');

      expect(getToken()).toBe('test-token-123');
    });

    it('should treat empty token as absent', () => {
      setToken('');

      expect(getToken()).toBeUndefined();
    });
  });

  describe('setToken', () => {
    it('should set token in session storage and memory', () => {
      const result = setToken('new-token-456');

      expect(result).toBe('new-token-456');
      expect(getToken()).toBe('new-token-456');
      expect(sessionStorage.getItem('ruoyi_access_token')).toBe('new-token-456');
    });

    it('should remove session storage token for empty string token', () => {
      setToken('existing-token');
      const result = setToken('');

      expect(result).toBe('');
      expect(getToken()).toBeUndefined();
      expect(sessionStorage.getItem('ruoyi_access_token')).toBeNull();
    });

    it('should handle long token strings', () => {
      const longToken = 'a'.repeat(1000);

      const result = setToken(longToken);

      expect(result).toBe(longToken);
      expect(getToken()).toBe(longToken);
    });

    it('should handle special characters in token', () => {
      const specialToken = 'token-with-!@#$%^&*()';

      const result = setToken(specialToken);

      expect(result).toBe(specialToken);
      expect(getToken()).toBe(specialToken);
    });
  });

  describe('removeToken', () => {
    it('should remove token from memory and session storage', () => {
      setToken('token-to-remove');

      removeToken();

      expect(getToken()).toBeUndefined();
      expect(sessionStorage.getItem('ruoyi_access_token')).toBeNull();
    });

    it('should not throw error when removing non-existent token', () => {
      expect(() => removeToken()).not.toThrow();
    });

    it('should be callable multiple times', () => {
      removeToken();
      removeToken();
      removeToken();

      expect(getToken()).toBeUndefined();
    });
  });

  describe('Token Workflow', () => {
    it('should handle complete token lifecycle', () => {
      setToken('lifecycle-token');
      expect(getToken()).toBe('lifecycle-token');

      removeToken();
      expect(getToken()).toBeUndefined();
    });

    it('should handle token update', () => {
      setToken('old-token');
      setToken('new-token');

      expect(getToken()).toBe('new-token');
      expect(sessionStorage.getItem('ruoyi_access_token')).toBe('new-token');
    });
  });

  describe('CSRF Token Workflow', () => {
    it('should set and get csrf token from memory and session storage', () => {
      const result = setCsrfToken('csrf-token');

      expect(result).toBe('csrf-token');
      expect(getCsrfToken()).toBe('csrf-token');
      expect(sessionStorage.getItem('ruoyi_csrf_token')).toBe('csrf-token');
    });

    it('should read csrf token from cookie when memory is empty', () => {
      document.cookie = 'csrf_token=cookie-csrf-token; path=/';

      expect(getCsrfToken()).toBe('cookie-csrf-token');
      expect(sessionStorage.getItem('ruoyi_csrf_token')).toBe('cookie-csrf-token');
    });

    it('should clear csrf token with removeToken', () => {
      setCsrfToken('csrf-token');

      removeToken();

      expect(getCsrfToken()).toBeUndefined();
      expect(sessionStorage.getItem('ruoyi_csrf_token')).toBeNull();
    });
  });
});
