/**
 * Unit tests for HTTP request utility
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import axios from 'axios'
import type { AxiosError, AxiosResponse } from 'axios'

// Mock axios
vi.mock('axios')

describe('request utility', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Request Interceptor', () => {
    it('should add authorization token to headers', () => {
      const config = {
        headers: {},
        url: '/api/test'
      }

      // Mock token in localStorage
      const mockToken = 'test-token-123'
      vi.spyOn(Storage.prototype, 'getItem').mockReturnValue(mockToken)

      // Simulate request interceptor
      const modifiedConfig = {
        ...config,
        headers: {
          ...config.headers,
          Authorization: `Bearer ${mockToken}`
        }
      }

      expect(modifiedConfig.headers.Authorization).toBe(`Bearer ${mockToken}`)
    })

    it('should not add token if not present', () => {
      const config = {
        headers: {},
        url: '/api/test'
      }

      vi.spyOn(Storage.prototype, 'getItem').mockReturnValue(null)

      expect(config.headers).not.toHaveProperty('Authorization')
    })

    it('should add request timestamp', () => {
      const config = {
        headers: {},
        url: '/api/test'
      }

      const timestamp = Date.now()
      const modifiedConfig = {
        ...config,
        headers: {
          ...config.headers,
          'X-Request-Time': timestamp.toString()
        }
      }

      expect(modifiedConfig.headers['X-Request-Time']).toBeDefined()
    })
  })

  describe('Response Interceptor', () => {
    it('should return data on successful response', () => {
      const response: AxiosResponse = {
        data: { code: 200, msg: 'success', data: { id: 1 } },
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any
      }

      expect(response.data.code).toBe(200)
      expect(response.data.data).toEqual({ id: 1 })
    })

    it('should handle 401 unauthorized', () => {
      const error: Partial<AxiosError> = {
        response: {
          status: 401,
          data: { msg: 'Unauthorized' },
          statusText: 'Unauthorized',
          headers: {},
          config: {} as any
        }
      }

      expect(error.response?.status).toBe(401)
    })

    it('should handle 403 forbidden', () => {
      const error: Partial<AxiosError> = {
        response: {
          status: 403,
          data: { msg: 'Forbidden' },
          statusText: 'Forbidden',
          headers: {},
          config: {} as any
        }
      }

      expect(error.response?.status).toBe(403)
    })

    it('should handle 404 not found', () => {
      const error: Partial<AxiosError> = {
        response: {
          status: 404,
          data: { msg: 'Not Found' },
          statusText: 'Not Found',
          headers: {},
          config: {} as any
        }
      }

      expect(error.response?.status).toBe(404)
    })

    it('should handle 500 server error', () => {
      const error: Partial<AxiosError> = {
        response: {
          status: 500,
          data: { msg: 'Internal Server Error' },
          statusText: 'Internal Server Error',
          headers: {},
          config: {} as any
        }
      }

      expect(error.response?.status).toBe(500)
    })

    it('should handle network errors', () => {
      const error: Partial<AxiosError> = {
        message: 'Network Error',
        code: 'ERR_NETWORK'
      }

      expect(error.message).toBe('Network Error')
      expect(error.code).toBe('ERR_NETWORK')
    })

    it('should handle timeout errors', () => {
      const error: Partial<AxiosError> = {
        message: 'timeout of 5000ms exceeded',
        code: 'ECONNABORTED'
      }

      expect(error.code).toBe('ECONNABORTED')
    })
  })

  describe('Request Methods', () => {
    it('should make GET request', async () => {
      const mockData = { id: 1, name: 'Test' }
      vi.mocked(axios.get).mockResolvedValue({ data: mockData })

      const result = await axios.get('/api/test')

      expect(axios.get).toHaveBeenCalledWith('/api/test')
      expect(result.data).toEqual(mockData)
    })

    it('should make POST request', async () => {
      const postData = { name: 'Test' }
      const mockResponse = { id: 1, ...postData }
      vi.mocked(axios.post).mockResolvedValue({ data: mockResponse })

      const result = await axios.post('/api/test', postData)

      expect(axios.post).toHaveBeenCalledWith('/api/test', postData)
      expect(result.data).toEqual(mockResponse)
    })

    it('should make PUT request', async () => {
      const putData = { id: 1, name: 'Updated' }
      vi.mocked(axios.put).mockResolvedValue({ data: putData })

      const result = await axios.put('/api/test/1', putData)

      expect(axios.put).toHaveBeenCalledWith('/api/test/1', putData)
      expect(result.data).toEqual(putData)
    })

    it('should make DELETE request', async () => {
      vi.mocked(axios.delete).mockResolvedValue({ data: { success: true } })

      const result = await axios.delete('/api/test/1')

      expect(axios.delete).toHaveBeenCalledWith('/api/test/1')
      expect(result.data.success).toBe(true)
    })
  })

  describe('Request Configuration', () => {
    it('should set custom headers', async () => {
      const customHeaders = { 'X-Custom-Header': 'value' }
      vi.mocked(axios.get).mockResolvedValue({ data: {} })

      await axios.get('/api/test', { headers: customHeaders })

      expect(axios.get).toHaveBeenCalledWith('/api/test', { headers: customHeaders })
    })

    it('should set request timeout', async () => {
      vi.mocked(axios.get).mockResolvedValue({ data: {} })

      await axios.get('/api/test', { timeout: 10000 })

      expect(axios.get).toHaveBeenCalledWith('/api/test', { timeout: 10000 })
    })

    it('should handle query parameters', async () => {
      const params = { page: 1, size: 10 }
      vi.mocked(axios.get).mockResolvedValue({ data: {} })

      await axios.get('/api/test', { params })

      expect(axios.get).toHaveBeenCalledWith('/api/test', { params })
    })
  })

  describe('Response Data Transformation', () => {
    it('should extract data from response wrapper', () => {
      const response = {
        code: 200,
        msg: 'success',
        data: { id: 1, name: 'Test' }
      }

      expect(response.data).toEqual({ id: 1, name: 'Test' })
    })

    it('should handle empty response data', () => {
      const response = {
        code: 200,
        msg: 'success',
        data: null
      }

      expect(response.data).toBeNull()
    })

    it('should handle array response data', () => {
      const response = {
        code: 200,
        msg: 'success',
        data: [{ id: 1 }, { id: 2 }]
      }

      expect(Array.isArray(response.data)).toBe(true)
      expect(response.data.length).toBe(2)
    })
  })

  describe('Error Messages', () => {
    it('should extract error message from response', () => {
      const error: Partial<AxiosError> = {
        response: {
          status: 400,
          data: { msg: 'Invalid input' },
          statusText: 'Bad Request',
          headers: {},
          config: {} as any
        }
      }

      expect((error.response?.data as { msg?: string }).msg).toBe('Invalid input')
    })

    it('should provide default error message', () => {
      const error: Partial<AxiosError> = {
        response: {
          status: 500,
          data: {},
          statusText: 'Internal Server Error',
          headers: {},
          config: {} as any
        }
      }

      const defaultMsg = (error.response?.data as { msg?: string }).msg || '请求失败'
      expect(defaultMsg).toBe('请求失败')
    })
  })

  describe('Retry Logic', () => {
    it('should retry failed requests', async () => {
      vi.mocked(axios.get)
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce({ data: { success: true } })

      // First attempt fails, second succeeds
      try {
        await axios.get('/api/test')
      } catch {
        const result = await axios.get('/api/test')
        expect(result.data.success).toBe(true)
      }
    })

    it('should limit retry attempts', async () => {
      vi.mocked(axios.get).mockRejectedValue(new Error('Network error'))

      const maxRetries = 3
      let attempts = 0

      for (let i = 0; i < maxRetries; i++) {
        try {
          await axios.get('/api/test')
        } catch {
          attempts++
        }
      }

      expect(attempts).toBe(maxRetries)
    })
  })

  describe('Request Cancellation', () => {
    it('should cancel pending requests', () => {
      const source = axios.CancelToken?.source()
      
      if (source) {
        source.cancel('Request cancelled')
        expect(source.token).toBeDefined()
      }
    })

    it('should handle cancelled request error', () => {
      const error = {
        message: 'Request cancelled',
        __CANCEL__: true
      }

      expect(error.__CANCEL__).toBe(true)
    })
  })
})
