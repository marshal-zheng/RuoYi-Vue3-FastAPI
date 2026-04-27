import router from './router';
import NProgress from 'nprogress';
import 'nprogress/nprogress.css';
import { getToken } from '@/utils/auth';
import { isPathMatch } from '@/utils/validate';
import { isRelogin } from '@/utils/request';
import useUserStore from '@/store/modules/user';
import useSettingsStore from '@/store/modules/settings';
import usePermissionStore from '@/store/modules/permission';
import type { RouteLocationNormalized, NavigationGuardNext } from 'vue-router';

NProgress.configure({ showSpinner: false });

const whiteList: string[] = ['/login', '/register'];
let restoringSessionPromise: Promise<boolean> | null = null;

const isWhiteList = (path: string): boolean => {
  return whiteList.some((pattern) => isPathMatch(pattern, path));
};

const isAuthExpiredError = (error: unknown): boolean => {
  const message = (error as { message?: string })?.message || '';
  const status = (error as { response?: { status?: number } })?.response?.status;
  return status === 401 || message.includes('401') || message.includes('会话已过期');
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

const restoreSessionOnce = (): Promise<boolean> => {
  if (!restoringSessionPromise) {
    restoringSessionPromise = useUserStore()
      .restoreSession()
      .finally(() => {
        restoringSessionPromise = null;
      });
  }
  return restoringSessionPromise;
};

router.beforeEach(
  (to: RouteLocationNormalized, from: RouteLocationNormalized, next: NavigationGuardNext) => {
    NProgress.start();
    if (getToken()) {
      const permissionStore = usePermissionStore();
      if (to.meta.title) {
        useSettingsStore().setTitle(to.meta.title as string);
      }
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
            .then(() => permissionStore.generateRoutes())
            .then(() => {
              isRelogin.show = false;
              const redirectPath = resolveLandingRedirect(to.path, permissionStore.firstMenuPath);
              if (redirectPath) {
                next({ path: redirectPath, replace: true });
              } else {
                next({ ...to, replace: true }); // hack方法 确保addRoutes已完成
              }
            })
            .catch((err: unknown) => {
              isRelogin.show = false;
              useUserStore()
                .logOut({ silentSuccess: true, silentError: true })
                .then(() => {
                  if (!isAuthExpiredError(err)) {
                    const errorMsg = (err as { message?: string })?.message || '获取用户信息失败';
                    console.error('[permission] restore user info failed:', errorMsg, err);
                  }
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
        restoreSessionOnce()
          .then((restored) => {
            if (restored) {
              next({ ...to, replace: true });
              return;
            }
            next(`/login?redirect=${to.fullPath}`);
            NProgress.done();
          })
          .catch(() => {
            next(`/login?redirect=${to.fullPath}`);
            NProgress.done();
          });
      }
    }
  }
);

router.afterEach(() => {
  NProgress.done();
});
