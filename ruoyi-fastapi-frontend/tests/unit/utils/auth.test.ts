/**
 * Auth 工具函数测试
 * 测试 Token 管理功能
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import Cookies from 'js-cookie'
import { getToken, setToken, removeToken } from '@/utils/auth'

// Mock js-cookie
vi.mock('js-cookie')

describe('Auth Utils', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('getToken', () => {
    it('should get token from cookies', () => {
      const mockToken = 'test-token-123'
      vi.mocked(Cookies.get).mockReturnValue(mockToken)

      const token = getToken()

      expect(Cookies.get).toHaveBeenCalledWith('Admin-Token')
      expect(token).toBe(mockToken)
    })

    it('should return undefined when no token exists', () => {
      vi.mocked(Cookies.get).mockReturnValue(undefined)

      const token = getToken()

      expect(token).toBeUndefined()
    })

    it('should handle empty token', () => {
      vi.mocked(Cookies.get).mockReturnValue('')

      const token = getToken()

      expect(token).toBe('')
    })
  })

  describe('setToken', () => {
    it('should set token in cookies', () => {
      const mockToken = 'new-token-456'
      vi.mocked(Cookies.set).mockReturnValue(mockToken)

      const result = setToken(mockToken)

      expect(Cookies.set).toHaveBeenCalledWith('Admin-Token', mockToken)
      expect(result).toBe(mockToken)
    })

    it('should handle empty string token', () => {
      vi.mocked(Cookies.set).mockReturnValue('')

      const result = setToken('')

      expect(Cookies.set).toHaveBeenCalledWith('Admin-Token', '')
      expect(result).toBe('')
    })

    it('should handle long token strings', () => {
      const longToken = 'a'.repeat(1000)
      vi.mocked(Cookies.set).mockReturnValue(longToken)

      const result = setToken(longToken)

      expect(Cookies.set).toHaveBeenCalledWith('Admin-Token', longToken)
      expect(result).toBe(longToken)
    })

    it('should handle special characters in token', () => {
      const specialToken = 'token-with-!@#$%^&*()'
      vi.mocked(Cookies.set).mockReturnValue(specialToken)

      const result = setToken(specialToken)

      expect(Cookies.set).toHaveBeenCalledWith('Admin-Token', specialToken)
    })
  })

  describe('removeToken', () => {
    it('should remove token from cookies', () => {
      vi.mocked(Cookies.remove).mockReturnValue(undefined)

      removeToken()

      expect(Cookies.remove).toHaveBeenCalledWith('Admin-Token')
    })

    it('should not throw error when removing non-existent token', () => {
      vi.mocked(Cookies.remove).mockReturnValue(undefined)

      expect(() => removeToken()).not.toThrow()
    })

    it('should be callable multiple times', () => {
      vi.mocked(Cookies.remove).mockReturnValue(undefined)

      removeToken()
      removeToken()
      removeToken()

      expect(Cookies.remove).toHaveBeenCalledTimes(3)
    })
  })

  describe('Token Workflow', () => {
    it('should handle complete token lifecycle', () => {
      const token = 'lifecycle-token'
      
      // Set token
      vi.mocked(Cookies.set).mockReturnValue(token)
      setToken(token)
      expect(Cookies.set).toHaveBeenCalledWith('Admin-Token', token)

      // Get token
      vi.mocked(Cookies.get).mockReturnValue(token)
      const retrieved = getToken()
      expect(retrieved).toBe(token)

      // Remove token
      vi.mocked(Cookies.remove).mockReturnValue(undefined)
      removeToken()
      expect(Cookies.remove).toHaveBeenCalledWith('Admin-Token')

      // Verify token is gone
      vi.mocked(Cookies.get).mockReturnValue(undefined)
      const afterRemove = getToken()
      expect(afterRemove).toBeUndefined()
    })

    it('should handle token update', () => {
      const oldToken = 'old-token'
      const newToken = 'new-token'

      // Set old token
      vi.mocked(Cookies.set).mockReturnValue(oldToken)
      setToken(oldToken)

      // Update to new token
      vi.mocked(Cookies.set).mockReturnValue(newToken)
      setToken(newToken)

      expect(Cookies.set).toHaveBeenCalledTimes(2)
      expect(Cookies.set).toHaveBeenLastCalledWith('Admin-Token', newToken)
    })
  })

  describe('Edge Cases', () => {
    it('should handle null-like values in setToken', () => {
      // @ts-ignore - testing edge case
      vi.mocked(Cookies.set).mockReturnValue(null)
      // @ts-ignore - testing edge case
      const result = setToken(null)

      expect(Cookies.set).toHaveBeenCalled()
    })

    it('should handle concurrent token operations', () => {
      const tokens = ['token1', 'token2', 'token3']
      
      tokens.forEach(token => {
        vi.mocked(Cookies.set).mockReturnValue(token)
        setToken(token)
      })

      expect(Cookies.set).toHaveBeenCalledTimes(3)
    })

    it('should maintain token key consistency', () => {
      const tokenKey = 'Admin-Token'

      vi.mocked(Cookies.get).mockReturnValue('test')
      getToken()
      expect(Cookies.get).toHaveBeenCalledWith(tokenKey)

      vi.mocked(Cookies.set).mockReturnValue('test')
      setToken('test')
      expect(Cookies.set).toHaveBeenCalledWith(tokenKey, 'test')

      vi.mocked(Cookies.remove).mockReturnValue(undefined)
      removeToken()
      expect(Cookies.remove).toHaveBeenCalledWith(tokenKey)
    })
  })
})
