import { describe, it, expect, beforeEach, vi } from 'vitest'
import * as configApi from '@/api/system/config'
import request from '@/utils/request'

// Mock request module
vi.mock('@/utils/request')

describe('Config API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('listConfig', () => {
    it('should call request with correct params', async () => {
      const mockResponse = { data: { rows: [], total: 0 } }
      vi.mocked(request).mockResolvedValue(mockResponse)

      const query = { configName: '系统名称', pageNum: 1, pageSize: 10 }
      await configApi.listConfig(query)

      expect(request).toHaveBeenCalledWith({
        url: '/system/config/list',
        method: 'get',
        params: query
      })
    })

    it('should handle query with config key', async () => {
      const mockResponse = { data: { rows: [], total: 0 } }
      vi.mocked(request).mockResolvedValue(mockResponse)

      const query = { configKey: 'sys.user.initPassword' }
      await configApi.listConfig(query)

      expect(request).toHaveBeenCalledWith({
        url: '/system/config/list',
        method: 'get',
        params: query
      })
    })

    it('should handle query with config type', async () => {
      const mockResponse = { data: { rows: [], total: 0 } }
      vi.mocked(request).mockResolvedValue(mockResponse)

      const query = { configType: 'Y' }
      await configApi.listConfig(query)

      expect(request).toHaveBeenCalledWith({
        url: '/system/config/list',
        method: 'get',
        params: query
      })
    })

    it('should handle date range query', async () => {
      const mockResponse = { data: { rows: [], total: 0 } }
      vi.mocked(request).mockResolvedValue(mockResponse)

      const query = {
        beginTime: '2024-01-01',
        endTime: '2024-12-31'
      }
      await configApi.listConfig(query)

      expect(request).toHaveBeenCalledWith({
        url: '/system/config/list',
        method: 'get',
        params: query
      })
    })
  })

  describe('getConfig', () => {
    it('should get config by id', async () => {
      const mockResponse = {
        data: {
          configId: 1,
          configName: '主框架页-默认皮肤样式名称',
          configKey: 'sys.index.skinName',
          configValue: 'skin-blue'
        }
      }
      vi.mocked(request).mockResolvedValue(mockResponse)

      await configApi.getConfig(1)

      expect(request).toHaveBeenCalledWith({
        url: '/system/config/1',
        method: 'get'
      })
    })

    it('should handle string id', async () => {
      const mockResponse = { data: { configId: '1' } }
      vi.mocked(request).mockResolvedValue(mockResponse)

      await configApi.getConfig('1')

      expect(request).toHaveBeenCalledWith({
        url: '/system/config/1',
        method: 'get'
      })
    })
  })

  describe('getConfigKey', () => {
    it('should get config value by key', async () => {
      const mockResponse = { data: 'skin-blue' }
      vi.mocked(request).mockResolvedValue(mockResponse)

      await configApi.getConfigKey('sys.index.skinName')

      expect(request).toHaveBeenCalledWith({
        url: '/system/config/configKey/sys.index.skinName',
        method: 'get'
      })
    })

    it('should handle different config keys', async () => {
      const mockResponse = { data: '123456' }
      vi.mocked(request).mockResolvedValue(mockResponse)

      await configApi.getConfigKey('sys.user.initPassword')

      expect(request).toHaveBeenCalledWith({
        url: '/system/config/configKey/sys.user.initPassword',
        method: 'get'
      })
    })

    it('should handle boolean config values', async () => {
      const mockResponse = { data: 'true' }
      vi.mocked(request).mockResolvedValue(mockResponse)

      await configApi.getConfigKey('sys.account.captchaEnabled')

      expect(request).toHaveBeenCalledWith({
        url: '/system/config/configKey/sys.account.captchaEnabled',
        method: 'get'
      })
    })
  })

  describe('addConfig', () => {
    it('should add new config', async () => {
      const mockResponse = { code: 200, msg: '操作成功' }
      vi.mocked(request).mockResolvedValue(mockResponse)

      const data = {
        configName: '测试参数',
        configKey: 'test.config.key',
        configValue: 'test-value',
        configType: 'N',
        remark: '测试用'
      }

      await configApi.addConfig(data)

      expect(request).toHaveBeenCalledWith({
        url: '/system/config',
        method: 'post',
        data
      })
    })

    it('should add built-in config', async () => {
      const mockResponse = { code: 200, msg: '操作成功' }
      vi.mocked(request).mockResolvedValue(mockResponse)

      const data = {
        configName: '内置参数',
        configKey: 'sys.builtin.key',
        configValue: 'value',
        configType: 'Y'
      }

      await configApi.addConfig(data)

      expect(request).toHaveBeenCalledWith({
        url: '/system/config',
        method: 'post',
        data
      })
    })
  })

  describe('updateConfig', () => {
    it('should update config', async () => {
      const mockResponse = { code: 200, msg: '操作成功' }
      vi.mocked(request).mockResolvedValue(mockResponse)

      const data = {
        configId: 1,
        configName: '更新参数',
        configValue: 'updated-value'
      }

      await configApi.updateConfig(data)

      expect(request).toHaveBeenCalledWith({
        url: '/system/config',
        method: 'put',
        data
      })
    })

    it('should update config key', async () => {
      const mockResponse = { code: 200, msg: '操作成功' }
      vi.mocked(request).mockResolvedValue(mockResponse)

      const data = {
        configId: 1,
        configKey: 'updated.key'
      }

      await configApi.updateConfig(data)

      expect(request).toHaveBeenCalledWith({
        url: '/system/config',
        method: 'put',
        data
      })
    })
  })

  describe('delConfig', () => {
    it('should delete config by id', async () => {
      const mockResponse = { code: 200, msg: '操作成功' }
      vi.mocked(request).mockResolvedValue(mockResponse)

      await configApi.delConfig(1)

      expect(request).toHaveBeenCalledWith({
        url: '/system/config/1',
        method: 'delete'
      })
    })

    it('should handle multiple ids', async () => {
      const mockResponse = { code: 200, msg: '操作成功' }
      vi.mocked(request).mockResolvedValue(mockResponse)

      await configApi.delConfig('1,2,3')

      expect(request).toHaveBeenCalledWith({
        url: '/system/config/1,2,3',
        method: 'delete'
      })
    })
  })

  describe('refreshCache', () => {
    it('should refresh config cache', async () => {
      const mockResponse = { code: 200, msg: '刷新成功' }
      vi.mocked(request).mockResolvedValue(mockResponse)

      await configApi.refreshCache()

      expect(request).toHaveBeenCalledWith({
        url: '/system/config/refreshCache',
        method: 'delete'
      })
    })

    it('should handle cache refresh errors', async () => {
      const error = { code: 500, msg: '刷新失败' }
      vi.mocked(request).mockRejectedValue(error)

      await expect(configApi.refreshCache()).rejects.toEqual(error)
    })
  })

  describe('Config Types', () => {
    it('should handle system built-in config', async () => {
      const mockResponse = { code: 200, msg: '操作成功' }
      vi.mocked(request).mockResolvedValue(mockResponse)

      const data = {
        configName: '系统内置参数',
        configKey: 'sys.builtin',
        configValue: 'value',
        configType: 'Y'
      }

      await configApi.addConfig(data)

      expect(request).toHaveBeenCalledWith({
        url: '/system/config',
        method: 'post',
        data
      })
    })

    it('should handle custom config', async () => {
      const mockResponse = { code: 200, msg: '操作成功' }
      vi.mocked(request).mockResolvedValue(mockResponse)

      const data = {
        configName: '自定义参数',
        configKey: 'custom.config',
        configValue: 'value',
        configType: 'N'
      }

      await configApi.addConfig(data)

      expect(request).toHaveBeenCalledWith({
        url: '/system/config',
        method: 'post',
        data
      })
    })
  })

  describe('Special Config Keys', () => {
    it('should get captcha enabled config', async () => {
      const mockResponse = { data: 'true' }
      vi.mocked(request).mockResolvedValue(mockResponse)

      await configApi.getConfigKey('sys.account.captchaEnabled')

      expect(request).toHaveBeenCalledWith({
        url: '/system/config/configKey/sys.account.captchaEnabled',
        method: 'get'
      })
    })

    it('should get init password config', async () => {
      const mockResponse = { data: '123456' }
      vi.mocked(request).mockResolvedValue(mockResponse)

      await configApi.getConfigKey('sys.user.initPassword')

      expect(request).toHaveBeenCalledWith({
        url: '/system/config/configKey/sys.user.initPassword',
        method: 'get'
      })
    })

    it('should get skin name config', async () => {
      const mockResponse = { data: 'skin-blue' }
      vi.mocked(request).mockResolvedValue(mockResponse)

      await configApi.getConfigKey('sys.index.skinName')

      expect(request).toHaveBeenCalledWith({
        url: '/system/config/configKey/sys.index.skinName',
        method: 'get'
      })
    })
  })

  describe('Error Handling', () => {
    it('should handle network errors', async () => {
      const error = new Error('Network Error')
      vi.mocked(request).mockRejectedValue(error)

      await expect(configApi.listConfig({})).rejects.toThrow('Network Error')
    })

    it('should handle API errors', async () => {
      const error = { code: 500, msg: '服务器错误' }
      vi.mocked(request).mockRejectedValue(error)

      await expect(configApi.getConfig(1)).rejects.toEqual(error)
    })

    it('should handle config not found', async () => {
      const error = { code: 404, msg: '参数不存在' }
      vi.mocked(request).mockRejectedValue(error)

      await expect(configApi.getConfigKey('non.existent.key')).rejects.toEqual(error)
    })

    it('should handle permission errors', async () => {
      const error = { code: 403, msg: '无权限' }
      vi.mocked(request).mockRejectedValue(error)

      await expect(configApi.delConfig(1)).rejects.toEqual(error)
    })
  })
})
