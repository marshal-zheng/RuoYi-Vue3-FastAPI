import router from './router';
import { ElMessage } from 'element-plus';
import NProgress from 'nprogress';
import 'nprogress/nprogress.css';
import { getToken } from '@/utils/auth';
import { isHttp, isPathMatch } from '@/utils/validate';
import { isRelogin } from '@/utils/request';
import useUserStore from '@/store/modules/user';
import useSettingsStore from '@/store/modules/settings';
import usePermissionStore from '@/store/modules/permission';
import type { RouteLocationNormalized, NavigationGuardNext, RouteRecordRaw } from 'vue-router';

// 定义路由元信息接口
interface RouteMeta {
  title?: string;
  icon?: string;
  noCache?: boolean;
  link?: string;
}

// 定义动态路由接口
interface DynamicRoute {
  name?: string;
  path: string;
  hidden?: boolean;
  redirect?: string;
  component?: any;
  query?: string;
  alwaysShow?: boolean;
  meta?: RouteMeta;
  children?: DynamicRoute[];
}

NProgress.configure({ showSpinner: false });

const whiteList: string[] = ['/login', '/register'];

const isWhiteList = (path: string): boolean => {
  return whiteList.some((pattern) => isPathMatch(pattern, path));
};

const resolveLandingRedirect = (path: string, firstMenuPath: string): string => {
  if (!firstMenuPath) {
    return '';
  }
  if (path === '/' || path === '') {
    return firstMenuPath;
  }
  if (path === '/index' && firstMenuPath !== '/index') {
    return firstMenuPath;
  }
  return '';
};

router.beforeEach(
  (to: RouteLocationNormalized, from: RouteLocationNormalized, next: NavigationGuardNext) => {
    NProgress.start();
    if (getToken()) {
      const permissionStore = usePermissionStore();
      to.meta.title && useSettingsStore().setTitle(to.meta.title);
      /* has token*/
      if (to.path === '/login') {
        next({ path: '/' });
        NProgress.done();
      } else if (isWhiteList(to.path)) {
        next();
      } else {
        if (useUserStore().roles.length === 0) {
          isRelogin.show = true;
          // 判断当前用户是否已拉取完user_info信息
          useUserStore()
            .getInfo()
            .then(() => {
              isRelogin.show = false;
              permissionStore.generateRoutes().then((accessRoutes: DynamicRoute[]) => {
                // 根据roles权限生成可访问的路由表
                accessRoutes.forEach((route: DynamicRoute) => {
                  if (!isHttp(route.path)) {
                    router.addRoute(route as RouteRecordRaw); // 动态添加可访问路由表
                  }
                });
                const redirectPath = resolveLandingRedirect(to.path, permissionStore.firstMenuPath);
                if (redirectPath) {
                  next({ path: redirectPath, replace: true });
                } else {
                  next({ ...to, replace: true }); // hack方法 确保addRoutes已完成
                }
              });
            })
            .catch((err: Error) => {
              useUserStore()
                .logOut()
                .then(() => {
                  ElMessage.error(err);
                  next({ path: '/' });
                });
            });
        } else {
          const redirectPath = resolveLandingRedirect(to.path, permissionStore.firstMenuPath);
          if (redirectPath) {
            next({ path: redirectPath, replace: true });
            NProgress.done();
          } else {
            next();
          }
        }
      }
    } else {
      // 没有token
      if (isWhiteList(to.path)) {
        // 在免登录白名单，直接进入
        next();
      } else {
        next(`/login?redirect=${to.fullPath}`); // 否则全部重定向到登录页
        NProgress.done();
      }
    }
  }
);

router.afterEach(() => {
  NProgress.done();
});
