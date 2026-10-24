--- before/src/store/modules/user.login.test.ts
+++ after/src/store/modules/user.login.test.ts
@@ -88,18 +88,72 @@
       mswHttp.post('*/auth/refresh', async () => {
         started();
         await waiting;
-        return HttpResponse.json({ token: 'old-restored-token', csrfToken: 'old-csrf' });
+        return HttpResponse.json({
+          token: 'old-restored-token',
+          csrfToken: 'old-csrf',
+        });
       })
     );
     const useUserStore = (await import('@/store/modules/user')).default;
     const store = useUserStore();
     const restoring = store.restoreSession();
     await entered;
-    loginMock.mockResolvedValue({ token: 'new-login-token', csrfToken: 'new-login-csrf' });
-    await store.login({ username: 'admin', password: 'admin123', code: '', uuid: '' });
+    loginMock.mockResolvedValue({
+      token: 'new-login-token',
+      csrfToken: 'new-login-csrf',
+    });
+    await store.login({
+      username: 'admin',
+      password: 'admin123',
+      code: '',
+      uuid: '',
+    });
     release();
     await expect(restoring).resolves.toBe(false);
     expect(store.token).toBe('new-login-token');
     expect((await import('@/utils/auth')).getToken()).toBe('new-login-token');
   });
 });
+
+describe('user authorization refresh isolation', () => {
+  beforeEach(() => {
+    setActivePinia(createPinia());
+    vi.clearAllMocks();
+  });
+
+  it('clears permissions when the refreshed user has no roles', async () => {
+    getInfoMock.mockResolvedValue({
+      user: { userId: 2, userName: 'limited' },
+      roles: [],
+      permissions: [],
+    });
+    const store = (await import('@/store/modules/user')).default();
+    store.roles = ['old'];
+    store.permissions = ['system:role:edit'];
+    await store.getInfo();
+    expect(store.roles).toEqual(['ROLE_DEFAULT']);
+    expect(store.permissions).toEqual([]);
+  });
+
+  it('does not restore old authorization after logout while getInfo is pending', async () => {
+    let release!: (value: unknown) => void;
+    getInfoMock.mockReturnValueOnce(
+      new Promise((resolve) => {
+        release = resolve;
+      })
+    );
+    logoutMock.mockResolvedValue(undefined);
+    const store = (await import('@/store/modules/user')).default();
+    const info = store.getInfo();
+    const result = expect(info).rejects.toMatchObject({ name: 'AbortError' });
+    await store.logOut();
+    release({
+      user: { userId: 1, userName: 'old' },
+      roles: ['admin'],
+      permissions: ['*:*:*'],
+    });
+    await result;
+    expect(store.roles).toEqual([]);
+    expect(store.permissions).toEqual([]);
+  });
+});
