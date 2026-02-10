import auth from '@/plugins/auth';
import router, { constantRoutes, dynamicRoutes } from '@/router';
import { getRouters } from '@/api/menu';
import Layout from '@/layout/index';
import ParentView from '@/components/ui/ParentView';
import InnerLink from '@/layout/components/InnerLink';
import type { RouteRecordRaw } from 'vue-router';

// 匹配views里面所有的.vue文件
const modules = import.meta.glob('./../../views/**/*.vue');

interface PermissionState {
  routes: RouteRecordRaw[];
  addRoutes: RouteRecordRaw[];
  defaultRoutes: RouteRecordRaw[];
  topbarRouters: RouteRecordRaw[];
  sidebarRouters: RouteRecordRaw[];
  firstMenuPath: string;
}

const usePermissionStore = defineStore('permission', {
  state: (): PermissionState => ({
    routes: [],
    addRoutes: [],
    defaultRoutes: [],
    topbarRouters: [],
    sidebarRouters: [],
    firstMenuPath: '/index',
  }),
  actions: {
    setRoutes(routes: RouteRecordRaw[]) {
      this.addRoutes = routes;
      this.routes = constantRoutes.concat(routes);
    },
    setDefaultRoutes(routes: RouteRecordRaw[]) {
      this.defaultRoutes = constantRoutes.concat(routes);
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
    generateRoutes(roles: string[]) {
      return new Promise((resolve) => {
        // 向后端请求路由数据
        // http 客户端已解包 payload.data，res 直接是路由数组
        getRouters().then((res) => {
          const sdata = JSON.parse(JSON.stringify(res));
          const rdata = JSON.parse(JSON.stringify(res));
          const defaultData = JSON.parse(JSON.stringify(res));

          const sidebarRoutes = filterAsyncRouter(sdata);
          const rewriteRoutes = filterAsyncRouter(rdata, false, true);
          const defaultRoutes = filterAsyncRouter(defaultData);
          const asyncRoutes = filterDynamicRoutes(dynamicRoutes);
          asyncRoutes.forEach((route) => {
            router.addRoute(route);
          });
          this.setRoutes(rewriteRoutes);
          this.setSidebarRouters(constantRoutes.concat(sidebarRoutes));
          this.setDefaultRoutes(sidebarRoutes);
          this.setTopbarRoutes(defaultRoutes);
          const landingCandidates = constantRoutes
            .filter((route) => !route.hidden)
            .concat(sidebarRoutes);
          const firstMenuPath = findFirstMenuPath(landingCandidates);
          this.setFirstMenuPath(firstMenuPath);
          resolve(rewriteRoutes);
        });
      });
    },
  },
});

// 遍历后台传来的路由字符串，转换为组件对象
function filterAsyncRouter(asyncRouterMap: any[], lastRouter: any = false, type: boolean = false): any[] {
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
