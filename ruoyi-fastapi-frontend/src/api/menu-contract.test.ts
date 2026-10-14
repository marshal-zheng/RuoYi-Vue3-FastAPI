import 'fake-indexeddb/auto';

import { afterEach, beforeEach, describe, expect, expectTypeOf, it, vi } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';
import { http, HttpResponse } from 'msw';

import { getRouters, type BackendRoute } from './menu';
import { listDept, type DeptRecord } from './system/dept';
import { deptTreeSelect } from './system/user';
import { listMenu, treeselect } from './system/menu';
import { optionselect } from './system/dict/type';
import { login } from './login';
import { clearSecurityTokens, setToken } from '@/utils/auth';
import router from '@/router';
import usePermissionStore from '@/store/modules/permission';
import type { HttpCollection } from '@/types/http-contract';
import { setupMainlineMockHandlers } from '../../tests/mocks/mainline';
import { mockServer } from '../../tests/mocks/server';

vi.mock('@/router', async () => {
  const { createMemoryHistory, createRouter } = await import('vue-router');
  return {
    default: createRouter({ history: createMemoryHistory(), routes: [] }),
    constantRoutes: [],
    dynamicRoutes: [],
  };
});
vi.mock('@/layout/index.vue', () => ({ default: {} }));
vi.mock('@/components/ui/ParentView/index.vue', () => ({ default: {} }));
vi.mock('@/layout/components/InnerLink/index.vue', () => ({ default: {} }));

describe('system menu contracts through the mainline MSW and request client', () => {
  setupMainlineMockHandlers();

  beforeEach(() => {
    clearSecurityTokens();
    setActivePinia(createPinia());
  });

  afterEach(() => {
    usePermissionStore().removeRegisteredDynamicRoutes();
    clearSecurityTokens();
  });

  it('generates fresh login routes from the canonical collection without changing the HTTP snapshot', async () => {
    const session = await login('admin', 'admin123', '', '');
    setToken(session.token);

    const snapshot = await getRouters();
    expectTypeOf(snapshot).toEqualTypeOf<HttpCollection<BackendRoute>>();
    expect(snapshot.items).toEqual([
      expect.objectContaining({ name: 'Project', path: '/project', component: 'Layout' }),
      expect.objectContaining({ name: 'System', path: '/system', component: 'Layout' }),
    ]);

    const store = usePermissionStore();
    const routes = await store.generateRoutes();
    expect(routes.map((route) => route.name)).toEqual(['Project', 'System']);
    expect(store.firstMenuPath).toBe('/project/project');
    expect(router.hasRoute('System')).toBe(true);
    expect(router.resolve('/system/user').matched.map((route) => route.path)).toEqual([
      '/system',
      '/system/user',
    ]);
    expect(snapshot.items[0].component).toBe('Layout');
    expect(snapshot.items[0].children?.[0].component).toBe('project/index');
  });

  it('returns department resources and menu queries as collections', async () => {
    const departments = await listDept({});
    expectTypeOf(departments).toEqualTypeOf<HttpCollection<DeptRecord>>();
    expect(departments.items).toEqual(
      expect.arrayContaining([expect.objectContaining({ deptId: 100, deptName: '若依科技' })])
    );

    const userDeptTree = await deptTreeSelect();
    expect(userDeptTree.items).toEqual(
      expect.arrayContaining([expect.objectContaining({ id: 100, label: '若依科技' })])
    );

    const menus = await listMenu();
    expect(menus.items).toEqual(
      expect.arrayContaining([expect.objectContaining({ menuId: 1, menuName: '系统管理' })])
    );
    const tree = await treeselect();
    expect(tree.items).toEqual(
      expect.arrayContaining([expect.objectContaining({ id: 1, label: '系统管理' })])
    );
  });

  it('returns dictionary options as a collection consumed by dictionary forms', async () => {
    const options = await optionselect();
    expect(options.items).toEqual(
      expect.arrayContaining([expect.objectContaining({ dictType: 'sys_user_sex' })])
    );
  });

  it.each([
    { name: 'bare array', body: [{ path: '/legacy', component: 'Layout', name: 'Legacy' }] },
    {
      name: 'legacy data wrapper',
      body: { data: [{ path: '/legacy', component: 'Layout', name: 'Legacy' }] },
    },
  ])('rejects $name responses without registering routes', async ({ body }) => {
    mockServer.use(http.get('/api/getRouters', () => HttpResponse.json(body)));
    const store = usePermissionStore();

    await expect(store.generateRoutes()).rejects.toBeInstanceOf(TypeError);
    expect(store.registeredRouteNames).toEqual([]);
    expect(router.hasRoute('Legacy')).toBe(false);
  });
});
