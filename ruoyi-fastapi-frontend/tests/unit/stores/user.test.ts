/**
 * Unit tests for user store
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useUserStore } from '@/store/modules/user'
import * as userApi from '@/api/system/user'

// Mock API
vi.mock('@/api/system/user')

describe('User Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('Initial State', () => {
    it('should have correct initial state', () => {
      const store = useUserStore()

      expect(store.token).toBe('')
      expect(store.userInfo).toBeNull()
      expect(store.roles).toEqual([])
      expect(store.permissions).toEqual([])
    })
  })

  describe('Login', () => {
    it('should login successfully', async () => {
      const store = useUserStore()
      const mockResponse = {
        code: 200,
        data: {
          token: 'test-token-123',
          user: {
            user_id: 1,
            user_name: 'admin',
            nick_name: '管理员'
          }
        }
      }

      vi.mocked(userApi.login).mockResolvedValue(mockResponse)

      await store.login({ username: 'admin', password: 'admin123' })

      expect(store.token).toBe('test-token-123')
      expect(store.userInfo?.user_name).toBe('admin')
    })

    it('should handle login failure', async () => {
      const store = useUserStore()

      vi.mocked(userApi.login).mockRejectedValue(new Error('用户名或密码错误'))

      await expect(
        store.login({ username: 'wrong', password: 'wrong' })
      ).rejects.toThrow('用户名或密码错误')

      expect(store.token).toBe('')
      expect(store.userInfo).toBeNull()
    })

    it('should validate login credentials', async () => {
      const store = useUserStore()

      await expect(
        store.login({ username: '', password: 'password' })
      ).rejects.toThrow('用户名不能为空')

      await expect(
        store.login({ username: 'admin', password: '' })
      ).rejects.toThrow('密码不能为空')
    })
  })

  describe('Logout', () => {
    it('should logout successfully', async () => {
      const store = useUserStore()

      // Set initial state
      store.token = 'test-token'
      store.userInfo = { user_id: 1, user_name: 'admin' }
      store.roles = ['admin']

      vi.mocked(userApi.logout).mockResolvedValue({ code: 200 })

      await store.logout()

      expect(store.token).toBe('')
      expect(store.userInfo).toBeNull()
      expect(store.roles).toEqual([])
      expect(store.permissions).toEqual([])
    })

    it('should clear state even if logout API fails', async () => {
      const store = useUserStore()

      store.token = 'test-token'
      store.userInfo = { user_id: 1, user_name: 'admin' }

      vi.mocked(userApi.logout).mockRejectedValue(new Error('Network error'))

      await store.logout()

      // Should still clear local state
      expect(store.token).toBe('')
      expect(store.userInfo).toBeNull()
    })
  })

  describe('Get User Info', () => {
    it('should fetch user info successfully', async () => {
      const store = useUserStore()
      const mockUserInfo = {
        code: 200,
        data: {
          user: {
            user_id: 1,
            user_name: 'admin',
            nick_name: '管理员',
            email: 'admin@example.com'
          },
          roles: ['admin'],
          permissions: ['*:*:*']
        }
      }

      vi.mocked(userApi.getUserInfo).mockResolvedValue(mockUserInfo)

      await store.getUserInfo()

      expect(store.userInfo?.user_name).toBe('admin')
      expect(store.roles).toEqual(['admin'])
      expect(store.permissions).toEqual(['*:*:*'])
    })

    it('should handle getUserInfo failure', async () => {
      const store = useUserStore()

      vi.mocked(userApi.getUserInfo).mockRejectedValue(new Error('Unauthorized'))

      await expect(store.getUserInfo()).rejects.toThrow('Unauthorized')
    })
  })

  describe('Permissions', () => {
    it('should check if user has permission', () => {
      const store = useUserStore()

      store.permissions = ['system:user:add', 'system:user:edit', 'system:role:list']

      expect(store.hasPermission('system:user:add')).toBe(true)
      expect(store.hasPermission('system:user:delete')).toBe(false)
    })

    it('should handle wildcard permissions', () => {
      const store = useUserStore()

      store.permissions = ['*:*:*']

      expect(store.hasPermission('system:user:add')).toBe(true)
      expect(store.hasPermission('any:permission:here')).toBe(true)
    })

    it('should check multiple permissions (AND)', () => {
      const store = useUserStore()

      store.permissions = ['system:user:add', 'system:user:edit']

      expect(store.hasPermissions(['system:user:add', 'system:user:edit'])).toBe(true)
      expect(store.hasPermissions(['system:user:add', 'system:user:delete'])).toBe(false)
    })

    it('should check multiple permissions (OR)', () => {
      const store = useUserStore()

      store.permissions = ['system:user:add']

      expect(store.hasAnyPermission(['system:user:add', 'system:user:edit'])).toBe(true)
      expect(store.hasAnyPermission(['system:user:delete', 'system:role:delete'])).toBe(false)
    })
  })

  describe('Roles', () => {
    it('should check if user has role', () => {
      const store = useUserStore()

      store.roles = ['admin', 'user']

      expect(store.hasRole('admin')).toBe(true)
      expect(store.hasRole('guest')).toBe(false)
    })

    it('should check multiple roles (AND)', () => {
      const store = useUserStore()

      store.roles = ['admin', 'user']

      expect(store.hasRoles(['admin', 'user'])).toBe(true)
      expect(store.hasRoles(['admin', 'guest'])).toBe(false)
    })

    it('should check multiple roles (OR)', () => {
      const store = useUserStore()

      store.roles = ['admin']

      expect(store.hasAnyRole(['admin', 'user'])).toBe(true)
      expect(store.hasAnyRole(['user', 'guest'])).toBe(false)
    })

    it('should handle admin role specially', () => {
      const store = useUserStore()

      store.roles = ['admin']

      // Admin should have all permissions
      expect(store.isAdmin).toBe(true)
      expect(store.hasPermission('any:permission')).toBe(true)
    })
  })

  describe('Token Management', () => {
    it('should set token', () => {
      const store = useUserStore()

      store.setToken('new-token-123')

      expect(store.token).toBe('new-token-123')
      // Should also save to localStorage
      expect(localStorage.getItem('token')).toBe('new-token-123')
    })

    it('should clear token', () => {
      const store = useUserStore()

      store.token = 'test-token'
      localStorage.setItem('token', 'test-token')

      store.clearToken()

      expect(store.token).toBe('')
      expect(localStorage.getItem('token')).toBeNull()
    })

    it('should restore token from localStorage', () => {
      localStorage.setItem('token', 'stored-token')

      const store = useUserStore()
      store.restoreToken()

      expect(store.token).toBe('stored-token')
    })
  })

  describe('User Profile', () => {
    it('should update user profile', async () => {
      const store = useUserStore()

      store.userInfo = {
        user_id: 1,
        user_name: 'admin',
        nick_name: '管理员'
      }

      const updateData = {
        nick_name: '超级管理员',
        email: 'admin@example.com'
      }

      vi.mocked(userApi.updateProfile).mockResolvedValue({ code: 200 })

      await store.updateProfile(updateData)

      expect(store.userInfo?.nick_name).toBe('超级管理员')
      expect(store.userInfo?.email).toBe('admin@example.com')
    })

    it('should change password', async () => {
      const store = useUserStore()

      const passwordData = {
        old_password: 'old123',
        new_password: 'new123'
      }

      vi.mocked(userApi.changePassword).mockResolvedValue({ code: 200 })

      await store.changePassword(passwordData)

      expect(userApi.changePassword).toHaveBeenCalledWith(passwordData)
    })

    it('should validate password change', async () => {
      const store = useUserStore()

      await expect(
        store.changePassword({ old_password: '', new_password: 'new123' })
      ).rejects.toThrow('原密码不能为空')

      await expect(
        store.changePassword({ old_password: 'old123', new_password: '' })
      ).rejects.toThrow('新密码不能为空')

      await expect(
        store.changePassword({ old_password: 'old123', new_password: '123' })
      ).rejects.toThrow('密码长度不能少于6位')
    })
  })

  describe('State Persistence', () => {
    it('should persist state to localStorage', () => {
      const store = useUserStore()

      store.token = 'test-token'
      store.userInfo = { user_id: 1, user_name: 'admin' }

      store.persistState()

      expect(localStorage.getItem('token')).toBe('test-token')
      expect(localStorage.getItem('userInfo')).toContain('admin')
    })

    it('should restore state from localStorage', () => {
      localStorage.setItem('token', 'stored-token')
      localStorage.setItem('userInfo', JSON.stringify({ user_id: 1, user_name: 'admin' }))

      const store = useUserStore()
      store.restoreState()

      expect(store.token).toBe('stored-token')
      expect(store.userInfo?.user_name).toBe('admin')
    })

    it('should handle corrupted localStorage data', () => {
      localStorage.setItem('userInfo', 'invalid-json')

      const store = useUserStore()
      store.restoreState()

      // Should not crash, should use default values
      expect(store.userInfo).toBeNull()
    })
  })

  describe('Computed Properties', () => {
    it('should compute isLoggedIn', () => {
      const store = useUserStore()

      expect(store.isLoggedIn).toBe(false)

      store.token = 'test-token'

      expect(store.isLoggedIn).toBe(true)
    })

    it('should compute userName', () => {
      const store = useUserStore()

      expect(store.userName).toBe('')

      store.userInfo = { user_id: 1, user_name: 'admin', nick_name: '管理员' }

      expect(store.userName).toBe('admin')
    })

    it('should compute nickName', () => {
      const store = useUserStore()

      expect(store.nickName).toBe('')

      store.userInfo = { user_id: 1, user_name: 'admin', nick_name: '管理员' }

      expect(store.nickName).toBe('管理员')
    })

    it('should compute isAdmin', () => {
      const store = useUserStore()

      expect(store.isAdmin).toBe(false)

      store.roles = ['admin']

      expect(store.isAdmin).toBe(true)
    })
  })

  describe('Error Handling', () => {
    it('should handle network errors', async () => {
      const store = useUserStore()

      vi.mocked(userApi.login).mockRejectedValue(new Error('Network error'))

      await expect(
        store.login({ username: 'admin', password: 'admin123' })
      ).rejects.toThrow('Network error')
    })

    it('should handle API errors', async () => {
      const store = useUserStore()

      vi.mocked(userApi.getUserInfo).mockRejectedValue({
        response: { status: 401, data: { msg: 'Token expired' } }
      })

      await expect(store.getUserInfo()).rejects.toMatchObject({
        response: { status: 401 }
      })
    })

    it('should handle timeout errors', async () => {
      const store = useUserStore()

      vi.mocked(userApi.login).mockRejectedValue(new Error('timeout'))

      await expect(
        store.login({ username: 'admin', password: 'admin123' })
      ).rejects.toThrow('timeout')
    })
  })
})
