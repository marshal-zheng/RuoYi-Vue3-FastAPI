--- before/tests/unit/stores/permission.test.ts
+++ after/tests/unit/stores/permission.test.ts
@@ -42,6 +42,10 @@
     };
   });
 
+vi.mock('@/store/modules/user', () => ({
+  default: () => ({ getInfo: vi.fn().mockResolvedValue(undefined) }),
+}));
+
 vi.mock('@/api/menu', () => ({
   getRouters: getRoutersMock,
 }));
