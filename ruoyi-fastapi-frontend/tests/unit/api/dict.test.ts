import { describe, it, expect, beforeEach, vi } from 'vitest'
import * as dictDataApi from '@/api/system/dict/data'
import * as dictTypeApi from '@/api/system/dict/type'
import request from '@/utils/request'

// Mock request module
vi.mock('@/utils/request')

describe('Dict Data API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('listData', () => {
    it('should call request with correct params', async () => {
      const mockResponse = { data: { rows: [], total: 0 } }
      vi.mocked(request).mockResolvedValue(mockResponse)

      const query = { dictType: 'sys_user_sex', pageNum: 1, pageSize: 10 }
      await dictDataApi.listData(query)

      expect(request).toHaveBeenCalledWith({
        url: '/system/dict/data/list',
        method: 'get',
        params: query
      })
    })

    it('should handle query with dict label', async () => {
      const mockResponse = { data: { rows: [], total: 0 } }
      vi.mocked(request).mockResolvedValue(mockResponse)

      const query = { dictType: 'sys_user_sex', dictLabel: '男' }
      await dictDataApi.listData(query)

      expect(request).toHaveBeenCalledWith({
        url: '/system/dict/data/list',
        method: 'get',
        params: query
      })
    })
  })

  describe('getData', () => {
    it('should get dict data by code', async () => {
      const mockResponse = {
        data: {
          dictCode: 1,
          dictLabel: '男',
          dictValue: '0'
        }
      }
      vi.mocked(request).mockResolvedValue(mockResponse)

      await dictDataApi.getData(1)

      expect(request).toHaveBeenCalledWith({
        url: '/system/dict/data/1',
        method: 'get'
      })
    })
  })

  describe('getDicts', () => {
    it('should get dict data by type', async () => {
      const mockResponse = {
        data: [
          { dictLabel: '男', dictValue: '0' },
          { dictLabel: '女', dictValue: '1' }
        ]
      }
      vi.mocked(request).mockResolvedValue(mockResponse)

      await dictDataApi.getDicts('sys_user_sex')

      expect(request).toHaveBeenCalledWith({
        url: '/system/dict/data/type/sys_user_sex',
        method: 'get'
      })
    })

    it('should handle different dict types', async () => {
      const mockResponse = { data: [] }
      vi.mocked(request).mockResolvedValue(mockResponse)

      await dictDataApi.getDicts('sys_normal_disable')

      expect(request).toHaveBeenCalledWith({
        url: '/system/dict/data/type/sys_normal_disable',
        method: 'get'
      })
    })
  })

  describe('addData', () => {
    it('should add new dict data', async () => {
      const mockResponse = { code: 200, msg: '操作成功' }
      vi.mocked(request).mockResolvedValue(mockResponse)

      const data = {
        dictType: 'sys_user_sex',
        dictLabel: '未知',
        dictValue: '2',
        dictSort: 3,
        status: '0'
      }

      await dictDataApi.addData(data)

      expect(request).toHaveBeenCalledWith({
        url: '/system/dict/data',
        method: 'post',
        data
      })
    })
  })

  describe('updateData', () => {
    it('should update dict data', async () => {
      const mockResponse = { code: 200, msg: '操作成功' }
      vi.mocked(request).mockResolvedValue(mockResponse)

      const data = {
        dictCode: 1,
        dictLabel: '男性',
        dictValue: '0'
      }

      await dictDataApi.updateData(data)

      expect(request).toHaveBeenCalledWith({
        url: '/system/dict/data',
        method: 'put',
        data
      })
    })
  })

  describe('delData', () => {
    it('should delete dict data by code', async () => {
      const mockResponse = { code: 200, msg: '操作成功' }
      vi.mocked(request).mockResolvedValue(mockResponse)

      await dictDataApi.delData(1)

      expect(request).toHaveBeenCalledWith({
        url: '/system/dict/data/1',
        method: 'delete'
      })
    })

    it('should handle multiple codes', async () => {
      const mockResponse = { code: 200, msg: '操作成功' }
      vi.mocked(request).mockResolvedValue(mockResponse)

      await dictDataApi.delData('1,2,3')

      expect(request).toHaveBeenCalledWith({
        url: '/system/dict/data/1,2,3',
        method: 'delete'
      })
    })
  })
})

describe('Dict Type API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('listType', () => {
    it('should call request with correct params', async () => {
      const mockResponse = { data: { rows: [], total: 0 } }
      vi.mocked(request).mockResolvedValue(mockResponse)

      const query = { dictName: '用户性别', pageNum: 1, pageSize: 10 }
      await dictTypeApi.listType(query)

      expect(request).toHaveBeenCalledWith({
        url: '/system/dict/type/list',
        method: 'get',
        params: query
      })
    })

    it('should handle query with dict type', async () => {
      const mockResponse = { data: { rows: [], total: 0 } }
      vi.mocked(request).mockResolvedValue(mockResponse)

      const query = { dictType: 'sys_user_sex' }
      await dictTypeApi.listType(query)

      expect(request).toHaveBeenCalledWith({
        url: '/system/dict/type/list',
        method: 'get',
        params: query
      })
    })

    it('should handle query with status', async () => {
      const mockResponse = { data: { rows: [], total: 0 } }
      vi.mocked(request).mockResolvedValue(mockResponse)

      const query = { status: '0' }
      await dictTypeApi.listType(query)

      expect(request).toHaveBeenCalledWith({
        url: '/system/dict/type/list',
        method: 'get',
        params: query
      })
    })
  })

  describe('getType', () => {
    it('should get dict type by id', async () => {
      const mockResponse = {
        data: {
          dictId: 1,
          dictName: '用户性别',
          dictType: 'sys_user_sex'
        }
      }
      vi.mocked(request).mockResolvedValue(mockResponse)

      await dictTypeApi.getType(1)

      expect(request).toHaveBeenCalledWith({
        url: '/system/dict/type/1',
        method: 'get'
      })
    })
  })

  describe('addType', () => {
    it('should add new dict type', async () => {
      const mockResponse = { code: 200, msg: '操作成功' }
      vi.mocked(request).mockResolvedValue(mockResponse)

      const data = {
        dictName: '测试字典',
        dictType: 'test_dict',
        status: '0',
        remark: '测试用'
      }

      await dictTypeApi.addType(data)

      expect(request).toHaveBeenCalledWith({
        url: '/system/dict/type',
        method: 'post',
        data
      })
    })
  })

  describe('updateType', () => {
    it('should update dict type', async () => {
      const mockResponse = { code: 200, msg: '操作成功' }
      vi.mocked(request).mockResolvedValue(mockResponse)

      const data = {
        dictId: 1,
        dictName: '更新字典',
        dictType: 'updated_dict'
      }

      await dictTypeApi.updateType(data)

      expect(request).toHaveBeenCalledWith({
        url: '/system/dict/type',
        method: 'put',
        data
      })
    })
  })

  describe('delType', () => {
    it('should delete dict type by id', async () => {
      const mockResponse = { code: 200, msg: '操作成功' }
      vi.mocked(request).mockResolvedValue(mockResponse)

      await dictTypeApi.delType(1)

      expect(request).toHaveBeenCalledWith({
        url: '/system/dict/type/1',
        method: 'delete'
      })
    })

    it('should handle multiple ids', async () => {
      const mockResponse = { code: 200, msg: '操作成功' }
      vi.mocked(request).mockResolvedValue(mockResponse)

      await dictTypeApi.delType('1,2,3')

      expect(request).toHaveBeenCalledWith({
        url: '/system/dict/type/1,2,3',
        method: 'delete'
      })
    })
  })

  describe('refreshCache', () => {
    it('should refresh dict cache', async () => {
      const mockResponse = { code: 200, msg: '操作成功' }
      vi.mocked(request).mockResolvedValue(mockResponse)

      await dictTypeApi.refreshCache()

      expect(request).toHaveBeenCalledWith({
        url: '/system/dict/type/refreshCache',
        method: 'delete'
      })
    })
  })

  describe('optionselect', () => {
    it('should get dict option list', async () => {
      const mockResponse = {
        data: [
          { dictId: 1, dictName: '用户性别', dictType: 'sys_user_sex' },
          { dictId: 2, dictName: '菜单状态', dictType: 'sys_show_hide' }
        ]
      }
      vi.mocked(request).mockResolvedValue(mockResponse)

      await dictTypeApi.optionselect()

      expect(request).toHaveBeenCalledWith({
        url: '/system/dict/type/optionselect',
        method: 'get'
      })
    })

    it('should return empty array when no options', async () => {
      const mockResponse = { data: [] }
      vi.mocked(request).mockResolvedValue(mockResponse)

      const result = await dictTypeApi.optionselect()

      expect(result).toEqual(mockResponse)
    })
  })

  describe('Error Handling', () => {
    it('should handle network errors', async () => {
      const error = new Error('Network Error')
      vi.mocked(request).mockRejectedValue(error)

      await expect(dictTypeApi.listType({})).rejects.toThrow('Network Error')
    })

    it('should handle API errors', async () => {
      const error = { code: 500, msg: '服务器错误' }
      vi.mocked(request).mockRejectedValue(error)

      await expect(dictDataApi.getDicts('sys_user_sex')).rejects.toEqual(error)
    })
  })
})
