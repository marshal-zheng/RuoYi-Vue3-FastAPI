import { createPinia, setActivePinia } from 'pinia';
/**
 * Permission 工具函数测试
 * 测试权限和角色校验功能
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { checkPermi, checkRole } from '@/utils/permission';
import useUserStore from '@/store/modules/user';

describe('Permission Utils', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    setActivePinia(createPinia());
    // Reset console.error mock
    vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  describe('checkPermi', () => {
    it('should return true when user has required permission', () => {
      useUserStore().$patch({
        permissions: ['system:user:add', 'system:user:edit'],
      });

      const result = checkPermi(['system:user:add']);

      expect(result).toBe(true);
    });

    it('should return true when user has super permission', () => {
      useUserStore().$patch({
        permissions: ['*:*:*'],
      });

      const result = checkPermi(['system:user:add']);

      expect(result).toBe(true);
    });

    it('should return false when user lacks permission', () => {
      useUserStore().$patch({
        permissions: ['system:user:view'],
      });

      const result = checkPermi(['system:user:delete']);

      expect(result).toBe(false);
    });

    it('should return true when user has any of multiple permissions', () => {
      useUserStore().$patch({
        permissions: ['system:user:add', 'system:user:edit'],
      });

      const result = checkPermi(['system:user:add', 'system:user:delete']);

      expect(result).toBe(true);
    });

    it('should return false when user has none of multiple permissions', () => {
      useUserStore().$patch({
        permissions: ['system:user:view'],
      });

      const result = checkPermi(['system:user:add', 'system:user:delete']);

      expect(result).toBe(false);
    });

    it('should return false without logging for empty array', () => {
      const consoleSpy = vi.spyOn(console, 'error');

      const result = checkPermi([]);

      expect(result).toBe(false);
      expect(consoleSpy).not.toHaveBeenCalled();
    });

    it('should return false without logging for non-array input', () => {
      const consoleSpy = vi.spyOn(console, 'error');

      const result = checkPermi('system:user:add');

      expect(result).toBe(false);
      expect(consoleSpy).not.toHaveBeenCalled();
    });

    it('should return false without logging for null input', () => {
      const consoleSpy = vi.spyOn(console, 'error');

      const result = checkPermi(null);

      expect(result).toBe(false);
      expect(consoleSpy).not.toHaveBeenCalled();
    });

    it('should return false without logging for undefined input', () => {
      const consoleSpy = vi.spyOn(console, 'error');

      const result = checkPermi(undefined);

      expect(result).toBe(false);
      expect(consoleSpy).not.toHaveBeenCalled();
    });

    it('should handle empty permissions array', () => {
      useUserStore().$patch({
        permissions: [],
      });

      const result = checkPermi(['system:user:add']);

      expect(result).toBe(false);
    });

    it('should handle case-sensitive permission matching', () => {
      useUserStore().$patch({
        permissions: ['system:user:add'],
      });

      const result = checkPermi(['SYSTEM:USER:ADD']);

      expect(result).toBe(false);
    });

    it('should handle complex permission strings', () => {
      useUserStore().$patch({
        permissions: ['system:user:add:special'],
      });

      const result = checkPermi(['system:user:add:special']);

      expect(result).toBe(true);
    });
  });

  describe('checkRole', () => {
    it('should return true when user has required role', () => {
      useUserStore().$patch({
        roles: ['admin', 'editor'],
      });

      const result = checkRole(['editor']);

      expect(result).toBe(true);
    });

    it('should return true when user is super admin', () => {
      useUserStore().$patch({
        roles: ['admin'],
      });

      const result = checkRole(['editor']);

      expect(result).toBe(true);
    });

    it('should return false when user lacks role', () => {
      useUserStore().$patch({
        roles: ['viewer'],
      });

      const result = checkRole(['admin']);

      expect(result).toBe(false);
    });

    it('should return true when user has any of multiple roles', () => {
      useUserStore().$patch({
        roles: ['editor', 'viewer'],
      });

      const result = checkRole(['editor', 'admin']);

      expect(result).toBe(true);
    });

    it('should return false when user has none of multiple roles', () => {
      useUserStore().$patch({
        roles: ['viewer'],
      });

      const result = checkRole(['admin', 'editor']);

      expect(result).toBe(false);
    });

    it('should return false without logging for empty array', () => {
      const consoleSpy = vi.spyOn(console, 'error');

      const result = checkRole([]);

      expect(result).toBe(false);
      expect(consoleSpy).not.toHaveBeenCalled();
    });

    it('should return false without logging for non-array input', () => {
      const consoleSpy = vi.spyOn(console, 'error');

      const result = checkRole('admin');

      expect(result).toBe(false);
      expect(consoleSpy).not.toHaveBeenCalled();
    });

    it('should return false without logging for null input', () => {
      const consoleSpy = vi.spyOn(console, 'error');

      const result = checkRole(null);

      expect(result).toBe(false);
      expect(consoleSpy).not.toHaveBeenCalled();
    });

    it('should handle empty roles array', () => {
      useUserStore().$patch({
        roles: [],
      });

      const result = checkRole(['admin']);

      expect(result).toBe(false);
    });

    it('should handle case-sensitive role matching', () => {
      useUserStore().$patch({
        roles: ['editor'],
      });

      const result = checkRole(['ADMIN']);

      expect(result).toBe(false);
    });

    it('should prioritize admin role', () => {
      useUserStore().$patch({
        roles: ['admin'],
      });

      const result = checkRole(['nonexistent-role']);

      expect(result).toBe(true);
    });
  });

  describe('Permission and Role Integration', () => {
    it('should handle both permission and role checks', () => {
      useUserStore().$patch({
        permissions: ['system:user:add'],
        roles: ['editor'],
      });

      const hasPermission = checkPermi(['system:user:add']);
      const hasRole = checkRole(['editor']);

      expect(hasPermission).toBe(true);
      expect(hasRole).toBe(true);
    });

    it('should handle super admin with all permissions', () => {
      useUserStore().$patch({
        permissions: ['*:*:*'],
        roles: ['admin'],
      });

      const hasPermission = checkPermi(['any:permission:here']);
      const hasRole = checkRole(['any-role']);

      expect(hasPermission).toBe(true);
      expect(hasRole).toBe(true);
    });

    it('should handle user with no permissions or roles', () => {
      useUserStore().$patch({
        permissions: [],
        roles: [],
      });

      const hasPermission = checkPermi(['system:user:add']);
      const hasRole = checkRole(['editor']);

      expect(hasPermission).toBe(false);
      expect(hasRole).toBe(false);
    });
  });

  describe('Edge Cases', () => {
    it('should handle special characters in permissions', () => {
      useUserStore().$patch({
        permissions: ['system:user:add-special'],
      });

      const result = checkPermi(['system:user:add-special']);

      expect(result).toBe(true);
    });

    it('should handle special characters in roles', () => {
      useUserStore().$patch({
        roles: ['super-admin'],
      });

      const result = checkRole(['super-admin']);

      expect(result).toBe(true);
    });

    it('should handle very long permission strings', () => {
      const longPermission = 'system:' + 'a'.repeat(100) + ':add';
      useUserStore().$patch({
        permissions: [longPermission],
      });

      const result = checkPermi([longPermission]);

      expect(result).toBe(true);
    });

    it('should handle multiple permission checks in sequence', () => {
      useUserStore().$patch({
        permissions: ['system:user:add', 'system:user:edit', 'system:user:delete'],
      });

      expect(checkPermi(['system:user:add'])).toBe(true);
      expect(checkPermi(['system:user:edit'])).toBe(true);
      expect(checkPermi(['system:user:delete'])).toBe(true);
      expect(checkPermi(['system:user:view'])).toBe(false);
    });

    it('should handle multiple role checks in sequence', () => {
      useUserStore().$patch({
        roles: ['editor', 'operator'],
      });

      expect(checkRole(['operator'])).toBe(true);
      expect(checkRole(['editor'])).toBe(true);
      expect(checkRole(['viewer'])).toBe(false);
    });
  });
});
