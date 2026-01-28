import { describe, it, expect, beforeEach, vi } from 'vitest'
import * as menuApi from '@/api/system/menu'
import request from '@/utils/request'

// Mock request module
vi.mock('@/utils/request')

describe('Menu API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('listMenu', () => {
    it('should call request with correct params', async () => {
      const mockResponse = { data: [] }
      vi.mocked(request).mockResolvedValue(mockResponse)

      const query = { menuName: '用户管理', status: '0' }
      await menuApi.listMenu(query)

      expect(request).toHaveBeenCalledWith({
        url: '/system/menu/list',
        method: 'get',
        params: query
      })
    })

    it('should handle empty query', async () => {
      const mockResponse = { data: [] }
      vi.mocked(request).mockResolvedValue(mockResponse)

      await menuApi.listMenu({})

      expect(request).toHaveBeenCalledWith({
        url: '/system/menu/list',
        method: 'get',
        params: {}
      })
    })

    it('should handle query with visible filter', async () => {
      const mockResponse = { data: [] }
      vi.mocked(request).mockResolvedValue(mockResponse)

      const query = { visible: '0' }
      await menuApi.listMenu(query)

      expect(request).toHaveBeenCalledWith({
        url: '/system/menu/list',
        method: 'get',
        params: query
      })
    })
  })

  describe('getMenu', () => {
    it('should get menu by id', async () => {
      const mockResponse = {
        data: {
          menuId: 1,
          menuName: '系统管理',
          menuType: 'M'
        }
      }
      vi.mocked(request).mockResolvedValue(mockResponse)

      await menuApi.getMenu(1)

      expect(request).toHaveBeenCalledWith({
        url: '/system/menu/1',
        method: 'get'
      })
    })

    it('should handle string id', async () => {
      const mockResponse = { data: { menuId: '1' } }
      vi.mocked(request).mockResolvedValue(mockResponse)

      await menuApi.getMenu('1')

      expect(request).toHaveBeenCalledWith({
        url: '/system/menu/1',
        method: 'get'
      })
    })
  })

  describe('treeselect', () => {
    it('should get menu tree structure', async () => {
      const mockResponse = {
        data: [
          {
            id: 1,
            label: '系统管理',
            children: [
              { id: 2, label: '用户管理' }
            ]
          }
        ]
      }
      vi.mocked(request).mockResolvedValue(mockResponse)

      await menuApi.treeselect()

      expect(request).toHaveBeenCalledWith({
        url: '/system/menu/treeselect',
        method: 'get'
      })
    })

    it('should return empty array when no menus', async () => {
      const mockResponse = { data: [] }
      vi.mocked(request).mockResolvedValue(mockResponse)

      const result = await menuApi.treeselect()

      expect(result).toEqual(mockResponse)
    })
  })

  describe('roleMenuTreeselect', () => {
    it('should get menu tree by role id', async () => {
      const mockResponse = {
        data: {
          menus: [
            { id: 1, label: '系统管理' }
          ],
          checkedKeys: [1, 2, 3]
        }
      }
      vi.mocked(request).mockResolvedValue(mockResponse)

      await menuApi.roleMenuTreeselect(1)

      expect(request).toHaveBeenCalledWith({
        url: '/system/menu/roleMenuTreeselect/1',
        method: 'get'
      })
    })

    it('should handle different role ids', async () => {
      const mockResponse = { data: { menus: [], checkedKeys: [] } }
      vi.mocked(request).mockResolvedValue(mockResponse)

      await menuApi.roleMenuTreeselect(999)

      expect(request).toHaveBeenCalledWith({
        url: '/system/menu/roleMenuTreeselect/999',
        method: 'get'
      })
    })
  })

  describe('addMenu', () => {
    it('should add new menu', async () => {
      const mockResponse = { code: 200, msg: '操作成功' }
      vi.mocked(request).mockResolvedValue(mockResponse)

      const data = {
        menuName: '测试菜单',
        parentId: 0,
        orderNum: 1,
        path: '/test',
        component: 'test/index',
        menuType: 'C',
        visible: '0',
        status: '0'
      }

      await menuApi.addMenu(data)

      expect(request).toHaveBeenCalledWith({
        url: '/system/menu',
        method: 'post',
        data
      })
    })

    it('should add menu with icon', async () => {
      const mockResponse = { code: 200, msg: '操作成功' }
      vi.mocked(request).mockResolvedValue(mockResponse)

      const data = {
        menuName: '测试菜单',
        icon: 'user',
        menuType: 'M'
      }

      await menuApi.addMenu(data)

      expect(request).toHaveBeenCalledWith({
        url: '/system/menu',
        method: 'post',
        data
      })
    })

    it('should add button permission', async () => {
      const mockResponse = { code: 200, msg: '操作成功' }
      vi.mocked(request).mockResolvedValue(mockResponse)

      const data = {
        menuName: '新增',
        parentId: 100,
        menuType: 'F',
        perms: 'system:user:add'
      }

      await menuApi.addMenu(data)

      expect(request).toHaveBeenCalledWith({
        url: '/system/menu',
        method: 'post',
        data
      })
    })
  })

  describe('updateMenu', () => {
    it('should update menu', async () => {
      const mockResponse = { code: 200, msg: '操作成功' }
      vi.mocked(request).mockResolvedValue(mockResponse)

      const data = {
        menuId: 1,
        menuName: '更新菜单',
        orderNum: 2
      }

      await menuApi.updateMenu(data)

      expect(request).toHaveBeenCalledWith({
        url: '/system/menu',
        method: 'put',
        data
      })
    })

    it('should update menu visibility', async () => {
      const mockResponse = { code: 200, msg: '操作成功' }
      vi.mocked(request).mockResolvedValue(mockResponse)

      const data = {
        menuId: 1,
        visible: '1'
      }

      await menuApi.updateMenu(data)

      expect(request).toHaveBeenCalledWith({
        url: '/system/menu',
        method: 'put',
        data
      })
    })

    it('should update menu status', async () => {
      const mockResponse = { code: 200, msg: '操作成功' }
      vi.mocked(request).mockResolvedValue(mockResponse)

      const data = {
        menuId: 1,
        status: '1'
      }

      await menuApi.updateMenu(data)

      expect(request).toHaveBeenCalledWith({
        url: '/system/menu',
        method: 'put',
        data
      })
    })
  })

  describe('delMenu', () => {
    it('should delete menu by id', async () => {
      const mockResponse = { code: 200, msg: '操作成功' }
      vi.mocked(request).mockResolvedValue(mockResponse)

      await menuApi.delMenu(1)

      expect(request).toHaveBeenCalledWith({
        url: '/system/menu/1',
        method: 'delete'
      })
    })

    it('should handle string id', async () => {
      const mockResponse = { code: 200, msg: '操作成功' }
      vi.mocked(request).mockResolvedValue(mockResponse)

      await menuApi.delMenu('100')

      expect(request).toHaveBeenCalledWith({
        url: '/system/menu/100',
        method: 'delete'
      })
    })
  })

  describe('Menu Types', () => {
    it('should handle directory menu type', async () => {
      const mockResponse = { code: 200, msg: '操作成功' }
      vi.mocked(request).mockResolvedValue(mockResponse)

      const data = {
        menuName: '系统管理',
        menuType: 'M',
        icon: 'system'
      }

      await menuApi.addMenu(data)

      expect(request).toHaveBeenCalledWith({
        url: '/system/menu',
        method: 'post',
        data
      })
    })

    it('should handle menu type', async () => {
      const mockResponse = { code: 200, msg: '操作成功' }
      vi.mocked(request).mockResolvedValue(mockResponse)

      const data = {
        menuName: '用户管理',
        menuType: 'C',
        path: '/system/user',
        component: 'system/user/index'
      }

      await menuApi.addMenu(data)

      expect(request).toHaveBeenCalledWith({
        url: '/system/menu',
        method: 'post',
        data
      })
    })

    it('should handle button type', async () => {
      const mockResponse = { code: 200, msg: '操作成功' }
      vi.mocked(request).mockResolvedValue(mockResponse)

      const data = {
        menuName: '新增',
        menuType: 'F',
        perms: 'system:user:add'
      }

      await menuApi.addMenu(data)

      expect(request).toHaveBeenCalledWith({
        url: '/system/menu',
        method: 'post',
        data
      })
    })
  })

  describe('Error Handling', () => {
    it('should handle network errors', async () => {
      const error = new Error('Network Error')
      vi.mocked(request).mockRejectedValue(error)

      await expect(menuApi.listMenu({})).rejects.toThrow('Network Error')
    })

    it('should handle API errors', async () => {
      const error = { code: 500, msg: '服务器错误' }
      vi.mocked(request).mockRejectedValue(error)

      await expect(menuApi.getMenu(1)).rejects.toEqual(error)
    })

    it('should handle permission errors', async () => {
      const error = { code: 403, msg: '无权限' }
      vi.mocked(request).mockRejectedValue(error)

      await expect(menuApi.delMenu(1)).rejects.toEqual(error)
    })
  })
})
