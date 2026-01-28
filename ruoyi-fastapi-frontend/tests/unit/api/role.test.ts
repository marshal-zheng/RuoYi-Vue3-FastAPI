import { describe, it, expect, beforeEach, vi } from 'vitest'
import * as roleApi from '@/api/system/role'
import request from '@/utils/request'

// Mock request module
vi.mock('@/utils/request')

describe('Role API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('listRole', () => {
    it('should call request with correct params', async () => {
      const mockResponse = { data: { rows: [], total: 0 } }
      vi.mocked(request).mockResolvedValue(mockResponse)

      const query = { pageNum: 1, pageSize: 10, roleName: 'admin' }
      await roleApi.listRole(query)

      expect(request).toHaveBeenCalledWith({
        url: '/system/role/list',
        method: 'get',
        params: query
      })
    })

    it('should handle empty query', async () => {
      const mockResponse = { data: { rows: [], total: 0 } }
      vi.mocked(request).mockResolvedValue(mockResponse)

      await roleApi.listRole({})

      expect(request).toHaveBeenCalledWith({
        url: '/system/role/list',
        method: 'get',
        params: {}
      })
    })
  })

  describe('getRole', () => {
    it('should get role by id', async () => {
      const mockResponse = { data: { roleId: 1, roleName: 'admin' } }
      vi.mocked(request).mockResolvedValue(mockResponse)

      await roleApi.getRole(1)

      expect(request).toHaveBeenCalledWith({
        url: '/system/role/1',
        method: 'get'
      })
    })

    it('should handle string id', async () => {
      const mockResponse = { data: { roleId: '1', roleName: 'admin' } }
      vi.mocked(request).mockResolvedValue(mockResponse)

      await roleApi.getRole('1')

      expect(request).toHaveBeenCalledWith({
        url: '/system/role/1',
        method: 'get'
      })
    })
  })

  describe('addRole', () => {
    it('should add new role', async () => {
      const mockResponse = { code: 200, msg: '操作成功' }
      vi.mocked(request).mockResolvedValue(mockResponse)

      const data = {
        roleName: '测试角色',
        roleKey: 'test',
        roleSort: 1,
        status: '0'
      }

      await roleApi.addRole(data)

      expect(request).toHaveBeenCalledWith({
        url: '/system/role',
        method: 'post',
        data
      })
    })

    it('should handle role with menu ids', async () => {
      const mockResponse = { code: 200, msg: '操作成功' }
      vi.mocked(request).mockResolvedValue(mockResponse)

      const data = {
        roleName: '测试角色',
        roleKey: 'test',
        menuIds: [1, 2, 3]
      }

      await roleApi.addRole(data)

      expect(request).toHaveBeenCalledWith({
        url: '/system/role',
        method: 'post',
        data
      })
    })
  })

  describe('updateRole', () => {
    it('should update role', async () => {
      const mockResponse = { code: 200, msg: '操作成功' }
      vi.mocked(request).mockResolvedValue(mockResponse)

      const data = {
        roleId: 1,
        roleName: '更新角色',
        roleKey: 'updated'
      }

      await roleApi.updateRole(data)

      expect(request).toHaveBeenCalledWith({
        url: '/system/role',
        method: 'put',
        data
      })
    })
  })

  describe('dataScope', () => {
    it('should update role data scope', async () => {
      const mockResponse = { code: 200, msg: '操作成功' }
      vi.mocked(request).mockResolvedValue(mockResponse)

      const data = {
        roleId: 1,
        dataScope: '2',
        deptIds: [1, 2, 3]
      }

      await roleApi.dataScope(data)

      expect(request).toHaveBeenCalledWith({
        url: '/system/role/dataScope',
        method: 'put',
        data
      })
    })
  })

  describe('changeRoleStatus', () => {
    it('should change role status', async () => {
      const mockResponse = { code: 200, msg: '操作成功' }
      vi.mocked(request).mockResolvedValue(mockResponse)

      await roleApi.changeRoleStatus(1, '1')

      expect(request).toHaveBeenCalledWith({
        url: '/system/role/changeStatus',
        method: 'put',
        data: { roleId: 1, status: '1' }
      })
    })

    it('should handle enable status', async () => {
      const mockResponse = { code: 200, msg: '操作成功' }
      vi.mocked(request).mockResolvedValue(mockResponse)

      await roleApi.changeRoleStatus(1, '0')

      expect(request).toHaveBeenCalledWith({
        url: '/system/role/changeStatus',
        method: 'put',
        data: { roleId: 1, status: '0' }
      })
    })
  })

  describe('delRole', () => {
    it('should delete role by id', async () => {
      const mockResponse = { code: 200, msg: '操作成功' }
      vi.mocked(request).mockResolvedValue(mockResponse)

      await roleApi.delRole(1)

      expect(request).toHaveBeenCalledWith({
        url: '/system/role/1',
        method: 'delete'
      })
    })

    it('should handle multiple ids', async () => {
      const mockResponse = { code: 200, msg: '操作成功' }
      vi.mocked(request).mockResolvedValue(mockResponse)

      await roleApi.delRole('1,2,3')

      expect(request).toHaveBeenCalledWith({
        url: '/system/role/1,2,3',
        method: 'delete'
      })
    })
  })

  describe('allocatedUserList', () => {
    it('should get allocated user list', async () => {
      const mockResponse = { data: { rows: [], total: 0 } }
      vi.mocked(request).mockResolvedValue(mockResponse)

      const query = { roleId: 1, pageNum: 1, pageSize: 10 }
      await roleApi.allocatedUserList(query)

      expect(request).toHaveBeenCalledWith({
        url: '/system/role/authUser/allocatedList',
        method: 'get',
        params: query
      })
    })
  })

  describe('unallocatedUserList', () => {
    it('should get unallocated user list', async () => {
      const mockResponse = { data: { rows: [], total: 0 } }
      vi.mocked(request).mockResolvedValue(mockResponse)

      const query = { roleId: 1, pageNum: 1, pageSize: 10 }
      await roleApi.unallocatedUserList(query)

      expect(request).toHaveBeenCalledWith({
        url: '/system/role/authUser/unallocatedList',
        method: 'get',
        params: query
      })
    })
  })

  describe('authUserCancel', () => {
    it('should cancel user authorization', async () => {
      const mockResponse = { code: 200, msg: '操作成功' }
      vi.mocked(request).mockResolvedValue(mockResponse)

      const data = { roleId: 1, userId: 2 }
      await roleApi.authUserCancel(data)

      expect(request).toHaveBeenCalledWith({
        url: '/system/role/authUser/cancel',
        method: 'put',
        data
      })
    })
  })

  describe('authUserCancelAll', () => {
    it('should batch cancel user authorization', async () => {
      const mockResponse = { code: 200, msg: '操作成功' }
      vi.mocked(request).mockResolvedValue(mockResponse)

      const data = { roleId: 1, userIds: '2,3,4' }
      await roleApi.authUserCancelAll(data)

      expect(request).toHaveBeenCalledWith({
        url: '/system/role/authUser/cancelAll',
        method: 'put',
        params: data
      })
    })
  })

  describe('authUserSelectAll', () => {
    it('should batch select users for authorization', async () => {
      const mockResponse = { code: 200, msg: '操作成功' }
      vi.mocked(request).mockResolvedValue(mockResponse)

      const data = { roleId: 1, userIds: '2,3,4' }
      await roleApi.authUserSelectAll(data)

      expect(request).toHaveBeenCalledWith({
        url: '/system/role/authUser/selectAll',
        method: 'put',
        params: data
      })
    })
  })

  describe('deptTreeSelect', () => {
    it('should get dept tree by role id', async () => {
      const mockResponse = { data: { depts: [], checkedKeys: [] } }
      vi.mocked(request).mockResolvedValue(mockResponse)

      await roleApi.deptTreeSelect(1)

      expect(request).toHaveBeenCalledWith({
        url: '/system/role/deptTree/1',
        method: 'get'
      })
    })
  })

  describe('Error Handling', () => {
    it('should handle network errors', async () => {
      const error = new Error('Network Error')
      vi.mocked(request).mockRejectedValue(error)

      await expect(roleApi.listRole({})).rejects.toThrow('Network Error')
    })

    it('should handle API errors', async () => {
      const error = { code: 500, msg: '服务器错误' }
      vi.mocked(request).mockRejectedValue(error)

      await expect(roleApi.getRole(1)).rejects.toEqual(error)
    })
  })
})
