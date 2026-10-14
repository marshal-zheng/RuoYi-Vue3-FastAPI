import auth from '@/plugins/auth';
import router, { constantRoutes, dynamicRoutes } from '@/router';
import { getRouters } from '@/api/menu';
import Layout from '@/layout/index.vue';
import ParentView from '@/components/ui/ParentView/index.vue';
import InnerLink from '@/layout/components/InnerLink/index.vue';
import { defineStore } from 'pinia';
import { isHttp } from '@/utils/validate';
import type { RouteRecordRaw, RouteRecordSingleView } from 'vue-router';
import type { BackendRoute } from '@/api/menu';

type AppRoute = RouteRecordRaw & { hidden?: boolean; permissions?: string[]; roles?: string[] };

// 匹配views里面所有的.vue文件
const modules = import.meta.glob<{ default: import('vue').Component }>('./../../views/**/*.vue');
const NOT_FOUND_ROUTE_PATH = '/:pathMatch(.*)*';
let reloadPromise: Promise<void> | null = null;
let registeredRouteRemovers: Array<() => void> = [];

interface RouteBundle {
  sidebarRoutes: RouteRecordRaw[];
  rewriteRoutes: RouteRecordRaw[];
  defaultRoutes: RouteRecordRaw[];
  asyncRoutes: RouteRecordRaw[];
  firstMenuPath: string;
}

interface PermissionState {
  routes: RouteRecordRaw[];
  addRoutes: RouteRecordRaw[];
  defaultRoutes: RouteRecordRaw[];
  topbarRouters: RouteRecordRaw[];
  sidebarRouters: RouteRecordRaw[];
  firstMenuPath: string;
  registeredRouteNames: string[];
  routeRemovalErrors: unknown[];
  routeReloadError: unknown;
  lastRouteReloadReason: string;
}

const usePermissionStore = defineStore('permission', {
  state: (): PermissionState => ({
    routes: [],
    addRoutes: [],
    defaultRoutes: [],
    topbarRouters: [],
    sidebarRouters: [],
    firstMenuPath: '/index',
    registeredRouteNames: [],
    routeRemovalErrors: [],
    routeReloadError: null,
    lastRouteReloadReason: '',
  }),
  actions: {
    setRoutes(routes: RouteRecordRaw[]) {
      this.addRoutes = routes;
      this.routes = getConstantRouteRecords().concat(routes);
    },
    setDefaultRoutes(routes: RouteRecordRaw[]) {
      this.defaultRoutes = getConstantRouteRecords().concat(routes);
    },
    setTopbarRoutes(routes: RouteRecordRaw[]) {
      this.topbarRouters = routes;
    },
    setSidebarRouters(routes: RouteRecordRaw[]) {
      this.sidebarRouters = routes;
    },
    setFirstMenuPath(path: string) {
      this.firstMenuPath = path || '/index';
    },
    setRegisteredRouteNames(routeNames: string[]) {
      this.registeredRouteNames = toUniqueRouteNames(routeNames);
    },
    appendRegisteredRouteNames(routeNames: string[]) {
      this.registeredRouteNames = toUniqueRouteNames(this.registeredRouteNames.concat(routeNames));
    },
    registerDynamicRouteRecords(routes: RouteRecordRaw[]) {
      routes.forEach((route) => {
        if (!isHttp(route.path)) {
          const routeName = typeof route.name === 'string' ? route.name : undefined;
          if (routeName && router.hasRoute(routeName)) {
            router.removeRoute(routeName);
          }
          const removeRoute = router.addRoute(route);
          if (typeof removeRoute === 'function') {
            registeredRouteRemovers.push(removeRoute);
          }
        }
      });
      this.appendRegisteredRouteNames(collectRouteNames(routes));
    },
    removeRegisteredDynamicRoutes() {
      [...registeredRouteRemovers].reverse().forEach((removeRoute) => {
        try {
          removeRoute();
        } catch (error) {
          this.routeRemovalErrors.push(error);
        }
      });
      registeredRouteRemovers = [];
      [...this.registeredRouteNames].reverse().forEach((routeName) => {
        if (router.hasRoute(routeName)) {
          router.removeRoute(routeName);
        }
      });
      this.setRegisteredRouteNames([]);
    },
    async fetchRouteBundle(): Promise<RouteBundle> {
      const rawRoutes = (await getRouters()).items;
      const sidebarRoutes = filterAsyncRouter(rawRoutes);
      const rewriteRoutes = filterAsyncRouter(rawRoutes, true);
      const defaultRoutes = filterAsyncRouter(rawRoutes);
      const asyncRoutes = filterDynamicRoutes(dynamicRoutes);
      const landingCandidates = getConstantRouteRecords()
        .filter((route) => !route.hidden)
        .concat(sidebarRoutes);
      return {
        sidebarRoutes,
        rewriteRoutes,
        defaultRoutes,
        asyncRoutes,
        firstMenuPath: findFirstMenuPath(landingCandidates),
      };
    },
    applyRouteBundle(bundle: RouteBundle) {
      this.setRoutes(bundle.rewriteRoutes);
      this.setSidebarRouters(getConstantRouteRecords().concat(bundle.sidebarRoutes));
      this.setDefaultRoutes(bundle.sidebarRoutes);
      this.setTopbarRoutes(bundle.defaultRoutes);
      this.setFirstMenuPath(bundle.firstMenuPath);
      this.registerDynamicRouteRecords(bundle.rewriteRoutes);
      this.registerDynamicRouteRecords(bundle.asyncRoutes);
    },
    async generateRoutes() {
      const bundle = await this.fetchRouteBundle();
      this.removeRegisteredDynamicRoutes();
      this.applyRouteBundle(bundle);
      return bundle.rewriteRoutes;
    },
    async reloadDynamicRoutes(reason: string = 'signature_changed'): Promise<void> {
      if (reloadPromise) {
        return reloadPromise;
      }
      reloadPromise = (async () => {
        const currentPath = router.currentRoute.value.fullPath || router.currentRoute.value.path;
        try {
          const bundle = await this.fetchRouteBundle();
          this.removeRegisteredDynamicRoutes();
          this.applyRouteBundle(bundle);
          if (!hasAccessibleMatch(currentPath)) {
            await router.replace(this.firstMenuPath || '/index');
          }
          this.lastRouteReloadReason = reason;
          this.routeReloadError = null;
        } catch (error) {
          this.routeReloadError = error;
        }
      })().finally(() => {
        reloadPromise = null;
      });
      return reloadPromise;
    },
  },
});

function getConstantRouteRecords(): AppRoute[] {
  return constantRoutes;
}

function collectRouteNames(routes: RouteRecordRaw[]): string[] {
  const names: string[] = [];
  routes.forEach((route) => {
    if (typeof route.name === 'string') {
      names.push(route.name);
    }
    if (route.children && route.children.length) {
      names.push(...collectRouteNames(route.children));
    }
  });
  return names;
}

function toUniqueRouteNames(routeNames: string[]): string[] {
  return Array.from(new Set(routeNames.filter(Boolean)));
}

function hasAccessibleMatch(path: string): boolean {
  const resolved = router.resolve(path);
  return resolved.matched.some((record) => record.path !== NOT_FOUND_ROUTE_PATH);
}

// Convert the HTTP menu tree into Vue Router records without mutating the fetched snapshot.
function filterAsyncRouter(routes: BackendRoute[], flatten: boolean = false): AppRoute[] {
  return routes.map((route) => {
    const { children, component, redirect, ...fields } = route;
    const mappedChildren = children?.length
      ? filterAsyncRouter(flatten ? filterChildren(children) : children, flatten)
      : undefined;
    const resolvedComponent =
      component === 'Layout'
        ? Layout
        : component === 'ParentView'
          ? ParentView
          : component === 'InnerLink'
            ? InnerLink
            : component
              ? loadView(component)
              : undefined;
    if (mappedChildren)
      return { ...fields, component: resolvedComponent, children: mappedChildren, redirect };
    if (!resolvedComponent) throw new TypeError(`Route ${route.path} has no resolvable component`);
    return { ...fields, component: resolvedComponent };
  });
}

function filterChildren(childrenMap: BackendRoute[], parentPath: string = ''): BackendRoute[] {
  return childrenMap.flatMap((child) => {
    const path = parentPath ? `${parentPath}/${child.path}` : child.path;
    if (child.children?.length && (child.component === 'ParentView' || parentPath)) {
      return filterChildren(child.children, path);
    }
    return [{ ...child, path }];
  });
}

// 动态路由遍历，验证是否具备权限
export function filterDynamicRoutes(routes: AppRoute[]): AppRoute[] {
  const res: AppRoute[] = [];
  routes.forEach((route) => {
    if (route.permissions) {
      if (auth.hasPermiOr(route.permissions)) {
        res.push(route);
      }
    } else if (route.roles) {
      if (auth.hasRoleOr(route.roles)) {
        res.push(route);
      }
    }
  });
  return res;
}

export const loadView = (view: string): RouteRecordSingleView['component'] => {
  let res;
  for (const path in modules) {
    const dir = path.split('views/')[1].split('.vue')[0];
    if (dir === view) {
      res = () => modules[path]().then((module) => module.default);
    }
  }
  if (!res) throw new TypeError(`No page component exists for ${view}`);
  return res;
};

function findFirstMenuPath(routes: AppRoute[], parentPath: string = ''): string {
  for (const route of routes) {
    if (route.hidden) {
      continue;
    }
    const currentPath = resolveRoutePath(parentPath, route.path);
    if (isFunctionalRoute(route)) {
      return currentPath || '/';
    }
    if (route.children && route.children.length) {
      const childPath = findFirstMenuPath(route.children, currentPath);
      if (childPath) {
        return childPath;
      }
    }
  }
  return '';
}

function resolveRoutePath(parentPath: string, routePath: string = ''): string {
  if (!routePath) {
    return parentPath || '/';
  }
  if (routePath.startsWith('/')) {
    return routePath;
  }
  if (!parentPath || parentPath === '/') {
    return `/${routePath}`;
  }
  return `${parentPath.replace(/\/$/, '')}/${routePath}`;
}

function isFunctionalRoute(route: AppRoute): boolean {
  if (!route.component) {
    return false;
  }
  if (
    route.component === Layout ||
    route.component === ParentView ||
    route.component === InnerLink
  ) {
    return false;
  }
  return true;
}

export default usePermissionStore;
