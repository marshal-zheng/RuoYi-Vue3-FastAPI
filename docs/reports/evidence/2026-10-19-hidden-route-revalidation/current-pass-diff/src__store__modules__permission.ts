--- before/src/store/modules/permission.ts
+++ after/src/store/modules/permission.ts
@@ -1,4 +1,6 @@
 import auth from '@/plugins/auth';
+import useUserStore from '@/store/modules/user';
+import { getSecuritySessionVersion } from '@/utils/auth';
 import router, { Layout, constantRoutes, dynamicRoutes } from '@/router';
 import { getRouters } from '@/api/menu';
 import ParentView from '@/components/ui/ParentView/index.vue';
@@ -8,12 +10,17 @@
 import type { RouteRecordRaw, RouteRecordSingleView } from 'vue-router';
 import type { BackendRoute } from '@/api/menu';
 
-type AppRoute = RouteRecordRaw & { hidden?: boolean; permissions?: string[]; roles?: string[] };
+type AppRoute = RouteRecordRaw & {
+  hidden?: boolean;
+  permissions?: string[];
+  roles?: string[];
+};
 
 // 匹配views里面所有的.vue文件
 const modules = import.meta.glob<{ default: import('vue').Component }>('./../../views/**/*.vue');
 const NOT_FOUND_ROUTE_PATH = '/:pathMatch(.*)*';
 let reloadPromise: Promise<void> | null = null;
+let reloadSessionVersion = -1;
 let registeredRouteRemovers: Array<() => void> = [];
 
 interface RouteBundle {
@@ -131,33 +138,46 @@
       this.registerDynamicRouteRecords(bundle.asyncRoutes);
     },
     async generateRoutes() {
+      const sessionVersion = getSecuritySessionVersion();
       const bundle = await this.fetchRouteBundle();
+      if (sessionVersion !== getSecuritySessionVersion()) return [];
       this.removeRegisteredDynamicRoutes();
       this.applyRouteBundle(bundle);
       return bundle.rewriteRoutes;
     },
     async reloadDynamicRoutes(reason: string = 'signature_changed'): Promise<void> {
-      if (reloadPromise) {
+      const sessionVersion = getSecuritySessionVersion();
+      if (reloadPromise && reloadSessionVersion === sessionVersion) {
         return reloadPromise;
       }
-      reloadPromise = (async () => {
-        const currentPath = router.currentRoute.value.fullPath || router.currentRoute.value.path;
+      reloadSessionVersion = sessionVersion;
+      const pending = (async () => {
         try {
+          // Menus and permission-only routes must use the same current authorization.
+          await useUserStore().getInfo();
+          if (sessionVersion !== getSecuritySessionVersion()) return;
           const bundle = await this.fetchRouteBundle();
+          if (sessionVersion !== getSecuritySessionVersion()) return;
+          const currentPath = router.currentRoute.value.fullPath || router.currentRoute.value.path;
           this.removeRegisteredDynamicRoutes();
           this.applyRouteBundle(bundle);
-          if (!hasAccessibleMatch(currentPath)) {
-            await router.replace(this.firstMenuPath || '/index');
-          }
+          // addRoute only changes the matcher. Re-resolve even an existing 404,
+          // using the latest location if navigation occurred while loading.
+          await router.replace(
+            hasAccessibleMatch(currentPath) ? currentPath : this.firstMenuPath || '/index'
+          );
           this.lastRouteReloadReason = reason;
           this.routeReloadError = null;
         } catch (error) {
-          this.routeReloadError = error;
+          if (sessionVersion === getSecuritySessionVersion()) this.routeReloadError = error;
         }
-      })().finally(() => {
-        reloadPromise = null;
-      });
-      return reloadPromise;
+      })();
+      reloadPromise = pending;
+      try {
+        await pending;
+      } finally {
+        if (reloadPromise === pending) reloadPromise = null;
+      }
     },
   },
 });
@@ -206,7 +226,12 @@
               ? loadView(component)
               : undefined;
     if (mappedChildren)
-      return { ...fields, component: resolvedComponent, children: mappedChildren, redirect };
+      return {
+        ...fields,
+        component: resolvedComponent,
+        children: mappedChildren,
+        redirect,
+      };
     if (!resolvedComponent) throw new TypeError(`Route ${route.path} has no resolvable component`);
     return { ...fields, component: resolvedComponent };
   });
