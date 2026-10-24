import { beforeEach, describe, expect, it, vi } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';

const { registeredRouteNames, routeRemoverSpy, mockResolve, mockRouter, getRoutersMock } =
  vi.hoisted(() => {
    const names = new Set<string>();
    const removerSpy = vi.fn();
    const resolve = vi.fn((path: string) => ({
      matched: path === '/missing' ? [{ path: '/:pathMatch(.*)*' }] : [{ path: '/system' }],
    }));
    const router = {
      addRoute: vi.fn((route: import('vue-router').RouteRecordRaw) => {
        if (typeof route.name === 'string') {
          names.add(route.name);
        }
        return () => {
          if (typeof route.name === 'string') {
            names.delete(route.name);
          }
          removerSpy(route);
        };
      }),
      removeRoute: vi.fn((routeName: string) => {
        names.delete(routeName);
      }),
      hasRoute: vi.fn((routeName: string) => names.has(routeName)),
      resolve,
      replace: vi.fn().mockResolvedValue(undefined),
      currentRoute: {
        value: {
          path: '/system/user',
          fullPath: '/system/user',
        },
      },
    };
    return {
      registeredRouteNames: names,
      routeRemoverSpy: removerSpy,
      mockResolve: resolve,
      mockRouter: router,
      getRoutersMock: vi.fn(),
    };
  });

vi.mock('@/api/menu', () => ({
  getRouters: getRoutersMock,
}));
vi.mock('@/router', () => ({
  default: mockRouter,
  Layout: {},
  constantRoutes: [
    { path: '/login', name: 'Login', hidden: true },
    { path: '/index', name: 'Index', hidden: false },
  ],
  dynamicRoutes: [{ path: '/audit', name: 'AuditRoute', permissions: ['monitor:audit:list'] }],
}));
vi.mock('@/layout/index.vue', () => ({ default: {} }));
vi.mock('@/components/ui/ParentView/index.vue', () => ({ default: {} }));
vi.mock('@/layout/components/InnerLink/index.vue', () => ({ default: {} }));
vi.mock('@/plugins/auth', () => ({
  default: {
    hasPermiOr: vi.fn(() => true),
    hasRoleOr: vi.fn(() => true),
  },
}));

async function loadPermissionStore() {
  const module = await import('@/store/modules/permission');
  return module.default;
}

describe('permission store route hot reload', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
    registeredRouteNames.clear();
    mockRouter.currentRoute.value.path = '/system/user';
    mockRouter.currentRoute.value.fullPath = '/system/user';
    mockResolve.mockImplementation((path: string) => ({
      matched: path === '/missing' ? [{ path: '/:pathMatch(.*)*' }] : [{ path: '/system' }],
    }));
  });

  it('generates routes and registers them into router', async () => {
    getRoutersMock.mockResolvedValue({
      items: [
        {
          path: '/system',
          component: 'Layout',
          name: 'System',
          hidden: false,
          children: [
            {
              path: 'user',
              component: 'system/user/index',
              name: 'SystemUser',
              hidden: false,
            },
          ],
        },
      ],
    });

    const usePermissionStore = await loadPermissionStore();
    const store = usePermissionStore();
    await store.generateRoutes();

    expect(getRoutersMock).toHaveBeenCalledTimes(1);
    expect(mockRouter.addRoute).toHaveBeenCalled();
    expect(store.firstMenuPath).toBe('/system/user');
    expect(store.registeredRouteNames).toContain('System');
    expect(store.registeredRouteNames).toContain('AuditRoute');
  });

  it('accepts collection-style router payloads from the new HTTP contract', async () => {
    getRoutersMock.mockResolvedValue({
      items: [
        {
          path: '/system',
          component: 'Layout',
          name: 'System',
          hidden: false,
          children: [
            {
              path: 'user',
              component: 'system/user/index',
              name: 'SystemUser',
              hidden: false,
            },
          ],
        },
      ],
    });

    const usePermissionStore = await loadPermissionStore();
    const store = usePermissionStore();
    await store.generateRoutes();

    expect(mockRouter.addRoute).toHaveBeenCalled();
    expect(store.firstMenuPath).toBe('/system/user');
    expect(store.registeredRouteNames).toContain('System');
  });

  it('falls back to first menu path when current route disappears after reload', async () => {
    getRoutersMock.mockResolvedValue({
      items: [
        {
          path: '/system',
          component: 'Layout',
          name: 'System',
          hidden: false,
          children: [
            {
              path: 'user',
              component: 'system/user/index',
              name: 'SystemUser',
              hidden: false,
            },
          ],
        },
      ],
    });

    const usePermissionStore = await loadPermissionStore();
    const store = usePermissionStore();
    await store.generateRoutes();

    mockRouter.currentRoute.value.path = '/missing';
    mockRouter.currentRoute.value.fullPath = '/missing';
    await store.reloadDynamicRoutes('signature_changed');

    expect(mockRouter.replace).toHaveBeenCalledWith('/system/user');
  });

  it('keeps existing routes when reload request fails', async () => {
    getRoutersMock.mockResolvedValue({
      items: [
        {
          path: '/system',
          component: 'Layout',
          name: 'System',
          hidden: false,
        },
      ],
    });

    const usePermissionStore = await loadPermissionStore();
    const store = usePermissionStore();
    await store.generateRoutes();
    const registeredBefore = [...store.registeredRouteNames];
    const removerCallCountBefore = routeRemoverSpy.mock.calls.length;

    getRoutersMock.mockRejectedValue(new Error('network down'));
    await store.reloadDynamicRoutes('signature_changed');

    expect(store.registeredRouteNames).toEqual(registeredBefore);
    expect(mockRouter.removeRoute).not.toHaveBeenCalled();
    expect(routeRemoverSpy.mock.calls.length).toBe(removerCallCountBefore);
  });

  it('removes unnamed dynamic routes via route remover callbacks', async () => {
    getRoutersMock.mockResolvedValueOnce({
      items: [
        {
          path: '/anonymous',
          component: 'Layout',
          hidden: false,
          children: [
            {
              path: 'page',
              component: 'system/user/index',
              hidden: false,
            },
          ],
        },
      ],
    });

    getRoutersMock.mockResolvedValueOnce({
      items: [
        {
          path: '/next',
          component: 'Layout',
          hidden: false,
          children: [
            {
              path: 'page',
              component: 'system/user/index',
              hidden: false,
            },
          ],
        },
      ],
    });

    const usePermissionStore = await loadPermissionStore();
    const store = usePermissionStore();
    await store.generateRoutes();
    await store.generateRoutes();

    expect(routeRemoverSpy).toHaveBeenCalled();
    expect(
      routeRemoverSpy.mock.calls.some(
        (call) => (call[0] as { path?: string }).path === '/anonymous'
      )
    ).toBe(true);
  });
});
