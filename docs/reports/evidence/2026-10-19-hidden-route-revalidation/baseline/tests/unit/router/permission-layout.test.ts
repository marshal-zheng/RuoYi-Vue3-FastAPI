import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';
import { flushPromises, mount } from '@vue/test-utils';
import { createMemoryHistory, RouterView } from 'vue-router';
import { h } from 'vue';
import router, { Layout } from '@/router';
import usePermissionStore from '@/store/modules/permission';
import { getRouters } from '@/api/menu';
import auth from '@/plugins/auth';

const layout = vi.hoisted(() => ({ evaluated: vi.fn() }));
vi.mock('@/router/history', () => ({ createAppHistory: () => createMemoryHistory() }));
vi.mock('@/layout/index.vue', () => {
  layout.evaluated();
  return { __esModule: true, default: { name: 'Layout', render: () => h(RouterView) } };
});
vi.mock('@/views/system/user/index.vue', () => ({
  default: { render: () => h('p', 'User list') },
}));
vi.mock('@/views/system/user/authRole.vue', () => ({
  __esModule: true,
  default: { render: () => h('p', 'Role assignment') },
}));
vi.mock('@/api/menu', () => ({ getRouters: vi.fn() }));
vi.mock('@/plugins/auth', () => ({
  default: { hasPermiOr: vi.fn(() => true), hasRoleOr: vi.fn(() => true) },
}));

let wrapper: ReturnType<typeof mount> | undefined;
beforeEach(() => {
  setActivePinia(createPinia());
  vi.mocked(auth.hasPermiOr).mockReturnValue(true);
  vi.mocked(getRouters).mockResolvedValue({
    items: [
      {
        path: '/system',
        name: 'System',
        component: 'Layout',
        children: [{ path: 'user', name: 'User', component: 'system/user/index' }],
      },
    ],
  });
});
afterEach(() => {
  wrapper?.unmount();
  wrapper = undefined;
  usePermissionStore().removeRegisteredDynamicRoutes();
});

it('initializes the router and permission catalog without evaluating Layout and its store imports', async () => {
  expect(layout.evaluated).not.toHaveBeenCalled();
  const store = usePermissionStore();
  await store.generateRoutes();
  expect(layout.evaluated).not.toHaveBeenCalled();
  expect(store.firstMenuPath).toBe('/system/user');
  expect(router.resolve('/system/user').matched[0]?.components?.default).toBe(Layout);
  expect(router.resolve('/system/user-auth/role/42').name).toBe('AuthRole');

  await router.push('/system/user');
  wrapper = mount({ render: () => h(RouterView) }, { global: { plugins: [router] } });
  await flushPromises();
  expect(wrapper.text()).toBe('User list');
  expect(layout.evaluated).toHaveBeenCalledOnce();
  await router.push('/system/user-auth/role/42');
  await flushPromises();
  expect(wrapper.text()).toBe('Role assignment');
});

it('keeps the real nested authorization route across a delayed menu reload and navigation', async () => {
  const store = usePermissionStore();
  await store.generateRoutes();
  await router.push('/system/user');
  let resolve!: (value: Awaited<ReturnType<typeof getRouters>>) => void;
  const delayed = new Promise<Awaited<ReturnType<typeof getRouters>>>((accept) => {
    resolve = accept;
  });
  const payload = await getRouters();
  vi.mocked(getRouters).mockReturnValueOnce(delayed);
  const reload = store.reloadDynamicRoutes();
  await router.push('/system/user-auth/role/42');
  resolve(payload);
  await reload;
  for (let attempt = 0; attempt < 3; attempt++) {
    await router.push('/system/user');
    await router.push('/system/user-auth/role/42');
    expect(router.currentRoute.value.name).toBe('AuthRole');
    expect(router.resolve(router.currentRoute.value.fullPath).name).toBe('AuthRole');
  }
  expect(store.routeReloadError).toBeNull();
});

it('does not grant the hidden authorization route when its permission is absent', async () => {
  vi.mocked(auth.hasPermiOr).mockReturnValue(false);
  await usePermissionStore().generateRoutes();
  expect(router.hasRoute('AuthRole')).toBe(false);
  expect(router.resolve('/system/user-auth/role/42').matched.map((x) => x.path)).toEqual([
    '/:pathMatch(.*)*',
  ]);
});
