--- before/tests/unit/router/permission-layout.test.ts
+++ after/tests/unit/router/permission-layout.test.ts
@@ -7,12 +7,36 @@
 import usePermissionStore from '@/store/modules/permission';
 import { getRouters } from '@/api/menu';
 import auth from '@/plugins/auth';
+import { clearSecurityTokens } from '@/utils/auth';
+import useUserStore from '@/store/modules/user';
+
+const refreshInfo = vi.hoisted(() => vi.fn().mockResolvedValue(undefined));
+vi.mock('@/store/modules/user', () => ({
+  default: () => ({ getInfo: refreshInfo }),
+}));
+vi.mock('@/views/error/404.vue', () => ({
+  __esModule: true,
+  default: { render: () => h('p', 'Not found') },
+}));
+vi.mock('@/views/system/dict/data.vue', () => ({
+  __esModule: true,
+  default: { render: () => h('p', 'Dictionary data') },
+}));
+vi.mock('@/views/system/user/profile/index.vue', () => ({
+  __esModule: true,
+  default: { render: () => h('p', 'Profile') },
+}));
 
 const layout = vi.hoisted(() => ({ evaluated: vi.fn() }));
-vi.mock('@/router/history', () => ({ createAppHistory: () => createMemoryHistory() }));
+vi.mock('@/router/history', () => ({
+  createAppHistory: () => createMemoryHistory(),
+}));
 vi.mock('@/layout/index.vue', () => {
   layout.evaluated();
-  return { __esModule: true, default: { name: 'Layout', render: () => h(RouterView) } };
+  return {
+    __esModule: true,
+    default: { name: 'Layout', render: () => h(RouterView) },
+  };
 });
 vi.mock('@/views/system/user/index.vue', () => ({
   default: { render: () => h('p', 'User list') },
@@ -29,6 +53,9 @@
 let wrapper: ReturnType<typeof mount> | undefined;
 beforeEach(() => {
   setActivePinia(createPinia());
+  clearSecurityTokens();
+  vi.spyOn(window, 'scrollTo').mockImplementation(() => {});
+  refreshInfo.mockReset().mockResolvedValue(undefined);
   vi.mocked(auth.hasPermiOr).mockReturnValue(true);
   vi.mocked(getRouters).mockResolvedValue({
     items: [
@@ -97,3 +124,111 @@
     '/:pathMatch(.*)*',
   ]);
 });
+
+it('refreshes the authorization snapshot before filtering hidden routes', async () => {
+  const store = usePermissionStore();
+  vi.mocked(auth.hasPermiOr).mockReturnValue(false);
+  await store.generateRoutes();
+  expect(router.hasRoute('Data')).toBe(false);
+  refreshInfo.mockImplementationOnce(async () => {
+    vi.mocked(auth.hasPermiOr).mockReturnValue(true);
+  });
+  await store.reloadDynamicRoutes();
+  expect(useUserStore().getInfo).toHaveBeenCalledOnce();
+  expect(router.hasRoute('Data')).toBe(true);
+});
+
+it('replaces the rendered 404 when the current URL becomes authorized', async () => {
+  const store = usePermissionStore();
+  vi.mocked(auth.hasPermiOr).mockReturnValue(false);
+  await store.generateRoutes();
+  await router.push('/system/dict-data/index/1?source=grant#values');
+  wrapper = mount({ render: () => h(RouterView) }, { global: { plugins: [router] } });
+  await flushPromises();
+  expect(wrapper.text()).toBe('Not found');
+  vi.mocked(auth.hasPermiOr).mockReturnValue(true);
+  await store.reloadDynamicRoutes();
+  await flushPromises();
+  expect(router.currentRoute.value.fullPath).toBe('/system/dict-data/index/1?source=grant#values');
+  expect(router.currentRoute.value.name).toBe('Data');
+  expect(wrapper.text()).toBe('Dictionary data');
+});
+
+it('keeps the latest navigation when an earlier page loses permission during a slow reload', async () => {
+  const store = usePermissionStore();
+  await store.generateRoutes();
+  await router.push('/system/dict-data/index/1');
+  const payload = await getRouters();
+  let release!: (value: typeof payload) => void;
+  vi.mocked(getRouters).mockReturnValueOnce(
+    new Promise((resolve) => {
+      release = resolve;
+    })
+  );
+  const reload = store.reloadDynamicRoutes();
+  await flushPromises();
+  await router.push('/user/profile');
+  vi.mocked(auth.hasPermiOr).mockReturnValue(false);
+  release(payload);
+  await reload;
+  expect(router.currentRoute.value.name).toBe('Profile');
+  expect(router.hasRoute('Data')).toBe(false);
+});
+
+it('discards a menu response belonging to an ended session', async () => {
+  const store = usePermissionStore();
+  await store.generateRoutes();
+  const oldPayload = {
+    items: [{ path: '/old', name: 'OldSession', component: 'system/user/index' }],
+  };
+  let release!: (value: typeof oldPayload) => void;
+  vi.mocked(getRouters).mockReturnValueOnce(
+    new Promise((resolve) => {
+      release = resolve;
+    })
+  );
+  const reload = store.reloadDynamicRoutes();
+  await flushPromises();
+  clearSecurityTokens();
+  vi.mocked(getRouters).mockResolvedValue({
+    items: [{ path: '/new', name: 'NewSession', component: 'system/user/index' }],
+  });
+  await store.generateRoutes();
+  release(oldPayload);
+  await reload;
+  expect(router.hasRoute('OldSession')).toBe(false);
+  expect(router.hasRoute('NewSession')).toBe(true);
+});
+
+it.each([
+  ['AuthRole', '/system/user-auth/role/42', 'system:user:edit'],
+  ['AuthUser', '/system/role-auth/user/42', 'system:role:edit'],
+  ['Data', '/system/dict-data/index/42', 'system:dict:list'],
+  ['JobLog', '/monitor/job-log/index/0', 'monitor:job:list'],
+  ['GenEdit', '/tool/gen-edit/index/42', 'tool:gen:edit'],
+  ['ProjectDetail', '/project/project-detail/index/42', 'project:project:query'],
+  ['DeviceDetail', '/device/detail/index/42', 'device:list:query'],
+  ['DeviceDetail', '/device/detail/index', 'device:list:query'],
+  ['ProjectTopo', '/project/topo/index/42', 'project:project:edit'],
+])('registers only the authorized catalog entry %s at %s', async (name, path, permission) => {
+  vi.mocked(auth.hasPermiOr).mockImplementation((permissions) => permissions.includes(permission));
+  await usePermissionStore().generateRoutes();
+  expect(router.resolve(path).name).toBe(name);
+  expect(router.getRoutes().filter((record) => record.name === name)).toHaveLength(1);
+  vi.mocked(auth.hasPermiOr).mockReturnValue(false);
+  await usePermissionStore().generateRoutes();
+  expect(router.hasRoute(name)).toBe(false);
+  expect(router.resolve(path).matched.map((record) => record.path)).toEqual(['/:pathMatch(.*)*']);
+});
+
+it('redirects the current hidden page after its permission is revoked', async () => {
+  const store = usePermissionStore();
+  await store.generateRoutes();
+  await router.push('/system/dict-data/index/1');
+  refreshInfo.mockImplementationOnce(async () => {
+    vi.mocked(auth.hasPermiOr).mockReturnValue(false);
+  });
+  await store.reloadDynamicRoutes();
+  expect(router.hasRoute('Data')).toBe(false);
+  expect(router.currentRoute.value.fullPath).toBe('/system/user');
+});
