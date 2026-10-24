import router from '@/router';
import { dismissReloginPrompt } from '@/utils/http';

const isAuthRecoveryRoute = (path: string): boolean => {
  return path === '/login' || path === '/register';
};

router.afterEach((to) => {
  if (isAuthRecoveryRoute(to.path)) {
    dismissReloginPrompt();
  }
});
