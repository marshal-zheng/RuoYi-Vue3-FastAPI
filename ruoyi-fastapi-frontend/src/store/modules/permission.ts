import auth from '@/plugins/auth';
import router, { constantRoutes, dynamicRoutes } from '@/router';
import { getRouters } from '@/api/menu';
import Layout from '@/layout/index.vue';
import ParentView from '@/components/ui/ParentView/index.vue';
import InnerLink from '@/layout/components/InnerLink/index.vue';
import { defineStore } from 'pinia';
import { isHttp } from '@/utils/validate';
import type { RouteRecordRaw } from 'vue-router';

// 匹配views里面所有的.vue文件
const modules = import.meta.glob('./../../views/**/*.vue');
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
          console.warn('[dev-menu-hot-sync] dynamic route remover failed:', error);
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
      const rawRoutes = normalizeBackendRoutes(await getRouters());
      const sdata = JSON.parse(JSON.stringify(rawRoutes));
      const rdata = JSON.parse(JSON.stringify(rawRoutes));
      const defaultData = JSON.parse(JSON.stringify(rawRoutes));
      const sidebarRoutes = filterAsyncRouter(sdata);
      const rewriteRoutes = filterAsyncRouter(rdata, false, true);
      const defaultRoutes = filterAsyncRouter(defaultData);
      const asyncRoutes = filterDynamicRoutes(dynamicRoutes);
      const landingCandidates = getConstantRouteRecords()
        .filter((route) => !(route as any).hidden)
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
          console.info('[dev-menu-hot-sync] dynamic routes reloaded:', reason);
        } catch (error) {
          console.error('[dev-menu-hot-sync] dynamic routes reload failed:', error);
        }
      })().finally(() => {
        reloadPromise = null;
      });
      return reloadPromise;
    },
  },
});

function getConstantRouteRecords(): RouteRecordRaw[] {
  return constantRoutes as unknown as RouteRecordRaw[];
}

function normalizeBackendRoutes(raw: any): any[] {
  if (Array.isArray(raw)) {
    return raw;
  }
  if (raw && Array.isArray(raw.data)) {
    return raw.data;
  }
  return [];
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

// 遍历后台传来的路由字符串，转换为组件对象
function filterAsyncRouter(
  asyncRouterMap: any[],
  lastRouter: any = false,
  type: boolean = false
): any[] {
  return asyncRouterMap.filter((route) => {
    if (type && route.children) {
      route.children = filterChildren(route.children);
    }
    if (route.component) {
      // Layout ParentView 组件特殊处理
      if (route.component === 'Layout') {
        route.component = Layout;
      } else if (route.component === 'ParentView') {
        route.component = ParentView;
      } else if (route.component === 'InnerLink') {
        route.component = InnerLink;
      } else {
        route.component = loadView(route.component);
      }
    }
    if (route.children != null && route.children && route.children.length) {
      route.children = filterAsyncRouter(route.children, route, type);
    } else {
      delete route['children'];
      delete route['redirect'];
    }
    return true;
  });
}

function filterChildren(childrenMap: any[], lastRouter: any = false): any[] {
  var children: any[] = [];
  childrenMap.forEach((el, index) => {
    if (el.children && el.children.length) {
      if (el.component === 'ParentView' && !lastRouter) {
        el.children.forEach((c: any) => {
          c.path = el.path + '/' + c.path;
          if (c.children && c.children.length) {
            children = children.concat(filterChildren(c.children, c));
            return;
          }
          children.push(c);
        });
        return;
      }
    }
    if (lastRouter) {
      el.path = lastRouter.path + '/' + el.path;
      if (el.children && el.children.length) {
        children = children.concat(filterChildren(el.children, el));
        return;
      }
    }
    children = children.concat(el);
  });
  return children;
}

// 动态路由遍历，验证是否具备权限
export function filterDynamicRoutes(routes: RouteRecordRaw[]): RouteRecordRaw[] {
  const res: RouteRecordRaw[] = [];
  routes.forEach((route) => {
    if ((route as any).permissions) {
      if (auth.hasPermiOr((route as any).permissions)) {
        res.push(route);
      }
    } else if ((route as any).roles) {
      if (auth.hasRoleOr((route as any).roles)) {
        res.push(route);
      }
    }
  });
  return res;
}

export const loadView = (view: string) => {
  let res;
  for (const path in modules) {
    const dir = path.split('views/')[1].split('.vue')[0];
    if (dir === view) {
      res = () => modules[path]();
    }
  }
  return res;
};

function findFirstMenuPath(routes: any[], parentPath: string = ''): string {
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

function isFunctionalRoute(route: any): boolean {
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
