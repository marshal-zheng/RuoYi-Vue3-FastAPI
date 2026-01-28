/**
 * Permission 工具函数测试
 * 测试权限和角色校验功能
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { checkPermi, checkRole } from '@/utils/permission'
import useUserStore from '@/store/modules/user'

// Mock user store
vi.mock('@/store/modules/user')

describe('Permission Utils', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Reset console.error mock
    vi.spyOn(console, 'error').mockImplementation(() => {})
  })

  describe('checkPermi', () => {
    it('should return true when user has required permission', () => {
      vi.mocked(useUserStore).mockReturnValue({
        permissions: ['system:user:add', 'system:user:edit'],
      } as any)

      const result = checkPermi(['system:user:add'])

      expect(result).toBe(true)
    })

    it('should return true when user has super permission', () => {
      vi.mocked(useUserStore).mockReturnValue({
        permissions: ['*:*:*'],
      } as any)

      const result = checkPermi(['system:user:add'])

      expect(result).toBe(true)
    })

    it('should return false when user lacks permission', () => {
      vi.mocked(useUserStore).mockReturnValue({
        permissions: ['system:user:view'],
      } as any)

      const result = checkPermi(['system:user:delete'])

      expect(result).toBe(false)
    })

    it('should return true when user has any of multiple permissions', () => {
      vi.mocked(useUserStore).mockReturnValue({
        permissions: ['system:user:add', 'system:user:edit'],
      } as any)

      const result = checkPermi(['system:user:add', 'system:user:delete'])

      expect(result).toBe(true)
    })

    it('should return false when user has none of multiple permissions', () => {
      vi.mocked(useUserStore).mockReturnValue({
        permissions: ['system:user:view'],
      } as any)

      const result = checkPermi(['system:user:add', 'system:user:delete'])

      expect(result).toBe(false)
    })

    it('should return false and log error for empty array', () => {
      const consoleSpy = vi.spyOn(console, 'error')

      const result = checkPermi([])

      expect(result).toBe(false)
      expect(consoleSpy).toHaveBeenCalled()
    })

    it('should return false and log error for non-array input', () => {
      const consoleSpy = vi.spyOn(console, 'error')

      // @ts-ignore - testing invalid input
      const result = checkPermi('system:user:add')

      expect(result).toBe(false)
      expect(consoleSpy).toHaveBeenCalled()
    })

    it('should return false and log error for null input', () => {
      const consoleSpy = vi.spyOn(console, 'error')

      // @ts-ignore - testing invalid input
      const result = checkPermi(null)

      expect(result).toBe(false)
      expect(consoleSpy).toHaveBeenCalled()
    })

    it('should return false and log error for undefined input', () => {
      const consoleSpy = vi.spyOn(console, 'error')

      // @ts-ignore - testing invalid input
      const result = checkPermi(undefined)

      expect(result).toBe(false)
      expect(consoleSpy).toHaveBeenCalled()
    })

    it('should handle empty permissions array', () => {
      vi.mocked(useUserStore).mockReturnValue({
        permissions: [],
      } as any)

      const result = checkPermi(['system:user:add'])

      expect(result).toBe(false)
    })

    it('should handle case-sensitive permission matching', () => {
      vi.mocked(useUserStore).mockReturnValue({
        permissions: ['system:user:add'],
      } as any)

      const result = checkPermi(['SYSTEM:USER:ADD'])

      expect(result).toBe(false)
    })

    it('should handle complex permission strings', () => {
      vi.mocked(useUserStore).mockReturnValue({
        permissions: ['system:user:add:special'],
      } as any)

      const result = checkPermi(['system:user:add:special'])

      expect(result).toBe(true)
    })
  })

  describe('checkRole', () => {
    it('should return true when user has required role', () => {
      vi.mocked(useUserStore).mockReturnValue({
        roles: ['admin', 'editor'],
      } as any)

      const result = checkRole(['editor'])

      expect(result).toBe(true)
    })

    it('should return true when user is super admin', () => {
      vi.mocked(useUserStore).mockReturnValue({
        roles: ['admin'],
      } as any)

      const result = checkRole(['editor'])

      expect(result).toBe(true)
    })

    it('should return false when user lacks role', () => {
      vi.mocked(useUserStore).mockReturnValue({
        roles: ['viewer'],
      } as any)

      const result = checkRole(['admin'])

      expect(result).toBe(false)
    })

    it('should return true when user has any of multiple roles', () => {
      vi.mocked(useUserStore).mockReturnValue({
        roles: ['editor', 'viewer'],
      } as any)

      const result = checkRole(['editor', 'admin'])

      expect(result).toBe(true)
    })

    it('should return false when user has none of multiple roles', () => {
      vi.mocked(useUserStore).mockReturnValue({
        roles: ['viewer'],
      } as any)

      const result = checkRole(['admin', 'editor'])

      expect(result).toBe(false)
    })

    it('should return false and log error for empty array', () => {
      const consoleSpy = vi.spyOn(console, 'error')

      const result = checkRole([])

      expect(result).toBe(false)
      expect(consoleSpy).toHaveBeenCalled()
    })

    it('should return false and log error for non-array input', () => {
      const consoleSpy = vi.spyOn(console, 'error')

      // @ts-ignore - testing invalid input
      const result = checkRole('admin')

      expect(result).toBe(false)
      expect(consoleSpy).toHaveBeenCalled()
    })

    it('should return false and log error for null input', () => {
      const consoleSpy = vi.spyOn(console, 'error')

      // @ts-ignore - testing invalid input
      const result = checkRole(null)

      expect(result).toBe(false)
      expect(consoleSpy).toHaveBeenCalled()
    })

    it('should handle empty roles array', () => {
      vi.mocked(useUserStore).mockReturnValue({
        roles: [],
      } as any)

      const result = checkRole(['admin'])

      expect(result).toBe(false)
    })

    it('should handle case-sensitive role matching', () => {
      vi.mocked(useUserStore).mockReturnValue({
        roles: ['admin'],
      } as any)

      const result = checkRole(['ADMIN'])

      expect(result).toBe(false)
    })

    it('should prioritize admin role', () => {
      vi.mocked(useUserStore).mockReturnValue({
        roles: ['admin'],
      } as any)

      const result = checkRole(['nonexistent-role'])

      expect(result).toBe(true)
    })
  })

  describe('Permission and Role Integration', () => {
    it('should handle both permission and role checks', () => {
      vi.mocked(useUserStore).mockReturnValue({
        permissions: ['system:user:add'],
        roles: ['editor'],
      } as any)

      const hasPermission = checkPermi(['system:user:add'])
      const hasRole = checkRole(['editor'])

      expect(hasPermission).toBe(true)
      expect(hasRole).toBe(true)
    })

    it('should handle super admin with all permissions', () => {
      vi.mocked(useUserStore).mockReturnValue({
        permissions: ['*:*:*'],
        roles: ['admin'],
      } as any)

      const hasPermission = checkPermi(['any:permission:here'])
      const hasRole = checkRole(['any-role'])

      expect(hasPermission).toBe(true)
      expect(hasRole).toBe(true)
    })

    it('should handle user with no permissions or roles', () => {
      vi.mocked(useUserStore).mockReturnValue({
        permissions: [],
        roles: [],
      } as any)

      const hasPermission = checkPermi(['system:user:add'])
      const hasRole = checkRole(['editor'])

      expect(hasPermission).toBe(false)
      expect(hasRole).toBe(false)
    })
  })

  describe('Edge Cases', () => {
    it('should handle special characters in permissions', () => {
      vi.mocked(useUserStore).mockReturnValue({
        permissions: ['system:user:add-special'],
      } as any)

      const result = checkPermi(['system:user:add-special'])

      expect(result).toBe(true)
    })

    it('should handle special characters in roles', () => {
      vi.mocked(useUserStore).mockReturnValue({
        roles: ['super-admin'],
      } as any)

      const result = checkRole(['super-admin'])

      expect(result).toBe(true)
    })

    it('should handle very long permission strings', () => {
      const longPermission = 'system:' + 'a'.repeat(100) + ':add'
      vi.mocked(useUserStore).mockReturnValue({
        permissions: [longPermission],
      } as any)

      const result = checkPermi([longPermission])

      expect(result).toBe(true)
    })

    it('should handle multiple permission checks in sequence', () => {
      vi.mocked(useUserStore).mockReturnValue({
        permissions: ['system:user:add', 'system:user:edit', 'system:user:delete'],
      } as any)

      expect(checkPermi(['system:user:add'])).toBe(true)
      expect(checkPermi(['system:user:edit'])).toBe(true)
      expect(checkPermi(['system:user:delete'])).toBe(true)
      expect(checkPermi(['system:user:view'])).toBe(false)
    })

    it('should handle multiple role checks in sequence', () => {
      vi.mocked(useUserStore).mockReturnValue({
        roles: ['admin', 'editor'],
      } as any)

      expect(checkRole(['admin'])).toBe(true)
      expect(checkRole(['editor'])).toBe(true)
      expect(checkRole(['viewer'])).toBe(false)
    })
  })
})
