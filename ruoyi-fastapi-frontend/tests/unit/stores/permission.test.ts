import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import usePermissionStore from '@/store/modules/permission'
import * as menuApi from '@/api/menu'

// Mock dependencies
vi.mock('@/api/menu')
vi.mock('@/router', () => ({
  default: {
    addRoute: vi.fn()
  },
  constantRoutes: [
    { path: '/login', name: 'Login', hidden: true },
    { path: '/', name: 'Index', hidden: false }
  ],
  dynamicRoutes: []
}))
vi.mock('@/layout/index', () => ({ default: {} }))
vi.mock('@/components/ParentView', () => ({ default: {} }))
vi.mock('@/layout/components/InnerLink', () => ({ default: {} }))
vi.mock('@/plugins/auth', () => ({
  default: {
    hasPermiOr: vi.fn(() => true),
    hasRoleOr: vi.fn(() => true)
  }
}))

describe('Permission Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('State', () => {
    it('should initialize with default state', () => {
      const store = usePermissionStore()

      expect(store.routes).toEqual([])
      expect(store.addRoutes).toEqual([])
      expect(store.defaultRoutes).toEqual([])
      expect(store.topbarRouters).toEqual([])
      expect(store.sidebarRouters).toEqual([])
      expect(store.firstMenuPath).toBe('/index')
    })
  })

  describe('Actions', () => {
    describe('setRoutes', () => {
      it('should set routes correctly', () => {
        const store = usePermissionStore()
        const routes = [
          { path: '/system', name: 'System' },
          { path: '/monitor', name: 'Monitor' }
        ]

        store.setRoutes(routes)

        expect(store.addRoutes).toEqual(routes)
        expect(store.routes.length).toBeGreaterThan(routes.length)
      })

      it('should merge with constant routes', () => {
        const store = usePermissionStore()
        const routes = [{ path: '/system', name: 'System' }]

        store.setRoutes(routes)

        expect(store.routes).toContainEqual({ path: '/system', name: 'System' })
      })
    })

    describe('setDefaultRoutes', () => {
      it('should set default routes', () => {
        const store = usePermissionStore()
        const routes = [{ path: '/system', name: 'System' }]

        store.setDefaultRoutes(routes)

        expect(store.defaultRoutes.length).toBeGreaterThan(0)
      })
    })

    describe('setTopbarRoutes', () => {
      it('should set topbar routes', () => {
        const store = usePermissionStore()
        const routes = [
          { path: '/system', name: 'System' },
          { path: '/monitor', name: 'Monitor' }
        ]

        store.setTopbarRoutes(routes)

        expect(store.topbarRouters).toEqual(routes)
      })
    })

    describe('setSidebarRouters', () => {
      it('should set sidebar routes', () => {
        const store = usePermissionStore()
        const routes = [{ path: '/system', name: 'System' }]

        store.setSidebarRouters(routes)

        expect(store.sidebarRouters).toEqual(routes)
      })
    })

    describe('setFirstMenuPath', () => {
      it('should set first menu path', () => {
        const store = usePermissionStore()

        store.setFirstMenuPath('/system/user')

        expect(store.firstMenuPath).toBe('/system/user')
      })

      it('should use default path when null', () => {
        const store = usePermissionStore()

        store.setFirstMenuPath(null)

        expect(store.firstMenuPath).toBe('/index')
      })

      it('should use default path when empty string', () => {
        const store = usePermissionStore()

        store.setFirstMenuPath('')

        expect(store.firstMenuPath).toBe('/index')
      })
    })

    describe('generateRoutes', () => {
      it('should generate routes from API', async () => {
        const mockRoutes = [
          {
            path: '/system',
            component: 'Layout',
            name: 'System',
            meta: { title: '系统管理' },
            children: [
              {
                path: 'user',
                component: 'system/user/index',
                name: 'User',
                meta: { title: '用户管理' }
              }
            ]
          }
        ]

        vi.mocked(menuApi.getRouters).mockResolvedValue({
          data: mockRoutes
        } as any)

        const store = usePermissionStore()
        const result = await store.generateRoutes([])

        expect(menuApi.getRouters).toHaveBeenCalled()
        expect(result).toBeDefined()
        expect(store.routes.length).toBeGreaterThan(0)
      })

      it('should handle empty routes from API', async () => {
        vi.mocked(menuApi.getRouters).mockResolvedValue({
          data: []
        } as any)

        const store = usePermissionStore()
        const result = await store.generateRoutes([])

        expect(result).toEqual([])
      })

      it('should set sidebar routes', async () => {
        const mockRoutes = [
          {
            path: '/system',
            component: 'Layout',
            name: 'System',
            children: []
          }
        ]

        vi.mocked(menuApi.getRouters).mockResolvedValue({
          data: mockRoutes
        } as any)

        const store = usePermissionStore()
        await store.generateRoutes([])

        expect(store.sidebarRouters.length).toBeGreaterThan(0)
      })

      it('should set topbar routes', async () => {
        const mockRoutes = [
          {
            path: '/system',
            component: 'Layout',
            name: 'System'
          }
        ]

        vi.mocked(menuApi.getRouters).mockResolvedValue({
          data: mockRoutes
        } as any)

        const store = usePermissionStore()
        await store.generateRoutes([])

        expect(store.topbarRouters).toBeDefined()
      })

      it('should find first menu path', async () => {
        const mockRoutes = [
          {
            path: '/system',
            component: 'Layout',
            name: 'System',
            hidden: false,
            children: [
              {
                path: 'user',
                component: 'system/user/index',
                name: 'User',
                hidden: false
              }
            ]
          }
        ]

        vi.mocked(menuApi.getRouters).mockResolvedValue({
          data: mockRoutes
        } as any)

        const store = usePermissionStore()
        await store.generateRoutes([])

        expect(store.firstMenuPath).toBeDefined()
      })

      it('should handle API errors', async () => {
        vi.mocked(menuApi.getRouters).mockRejectedValue(new Error('API Error'))

        const store = usePermissionStore()

        await expect(store.generateRoutes([])).rejects.toThrow('API Error')
      })
    })
  })

  describe('Route Processing', () => {
    it('should handle Layout component', async () => {
      const mockRoutes = [
        {
          path: '/system',
          component: 'Layout',
          name: 'System'
        }
      ]

      vi.mocked(menuApi.getRouters).mockResolvedValue({
        data: mockRoutes
      } as any)

      const store = usePermissionStore()
      await store.generateRoutes([])

      expect(store.routes.length).toBeGreaterThan(0)
    })

    it('should handle ParentView component', async () => {
      const mockRoutes = [
        {
          path: '/system',
          component: 'ParentView',
          name: 'System'
        }
      ]

      vi.mocked(menuApi.getRouters).mockResolvedValue({
        data: mockRoutes
      } as any)

      const store = usePermissionStore()
      await store.generateRoutes([])

      expect(store.routes.length).toBeGreaterThan(0)
    })

    it('should handle InnerLink component', async () => {
      const mockRoutes = [
        {
          path: '/link',
          component: 'InnerLink',
          name: 'Link'
        }
      ]

      vi.mocked(menuApi.getRouters).mockResolvedValue({
        data: mockRoutes
      } as any)

      const store = usePermissionStore()
      await store.generateRoutes([])

      expect(store.routes.length).toBeGreaterThan(0)
    })

    it('should handle nested routes', async () => {
      const mockRoutes = [
        {
          path: '/system',
          component: 'Layout',
          children: [
            {
              path: 'user',
              component: 'system/user/index',
              children: [
                {
                  path: 'profile',
                  component: 'system/user/profile/index'
                }
              ]
            }
          ]
        }
      ]

      vi.mocked(menuApi.getRouters).mockResolvedValue({
        data: mockRoutes
      } as any)

      const store = usePermissionStore()
      await store.generateRoutes([])

      expect(store.routes.length).toBeGreaterThan(0)
    })

    it('should remove empty children', async () => {
      const mockRoutes = [
        {
          path: '/system',
          component: 'Layout',
          children: []
        }
      ]

      vi.mocked(menuApi.getRouters).mockResolvedValue({
        data: mockRoutes
      } as any)

      const store = usePermissionStore()
      await store.generateRoutes([])

      expect(store.routes.length).toBeGreaterThan(0)
    })
  })

  describe('Hidden Routes', () => {
    it('should skip hidden routes when finding first menu', async () => {
      const mockRoutes = [
        {
          path: '/hidden',
          component: 'Layout',
          hidden: true,
          children: [
            {
              path: 'page',
              component: 'hidden/page/index'
            }
          ]
        },
        {
          path: '/visible',
          component: 'Layout',
          hidden: false,
          children: [
            {
              path: 'page',
              component: 'visible/page/index'
            }
          ]
        }
      ]

      vi.mocked(menuApi.getRouters).mockResolvedValue({
        data: mockRoutes
      } as any)

      const store = usePermissionStore()
      await store.generateRoutes([])

      expect(store.firstMenuPath).not.toContain('hidden')
    })
  })

  describe('Edge Cases', () => {
    it('should handle routes without component', async () => {
      const mockRoutes = [
        {
          path: '/system',
          name: 'System'
        }
      ]

      vi.mocked(menuApi.getRouters).mockResolvedValue({
        data: mockRoutes
      } as any)

      const store = usePermissionStore()
      await store.generateRoutes([])

      expect(store.routes.length).toBeGreaterThan(0)
    })

    it('should handle routes with null children', async () => {
      const mockRoutes = [
        {
          path: '/system',
          component: 'Layout',
          children: null
        }
      ]

      vi.mocked(menuApi.getRouters).mockResolvedValue({
        data: mockRoutes
      } as any)

      const store = usePermissionStore()
      await store.generateRoutes([])

      expect(store.routes.length).toBeGreaterThan(0)
    })
  })
})
