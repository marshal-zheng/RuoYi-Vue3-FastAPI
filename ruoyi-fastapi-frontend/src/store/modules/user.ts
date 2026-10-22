import { login, logout, getInfo } from '@/api/login';
import { defineStore } from 'pinia';
import { AbortError } from '@zxio/http';
import {
  clearSecurityTokens,
  getSecuritySessionVersion,
  getToken,
  setCsrfToken,
  setToken,
} from '@/utils/auth';
import { isHttp, isEmpty } from '@/utils/validate';
import { clampBcryptPassword } from '@/utils/password';
import defAva from '@/assets/images/profile.jpg';
import request from '@/utils/request';
import { refreshHttpSession } from '@/utils/http';
import { withSessionCookieLock } from '@/utils/session';
import { endQuerySession, setQuerySession } from '@/queries/context';

interface UserInfo {
  username: string;
  password: string;
  code: string;
  uuid: string;
}

interface LogoutOptions {
  silentSuccess?: boolean;
  silentError?: boolean;
}

interface UserState {
  token: string;
  id: string | number;
  name: string;
  nickName: string;
  avatar: string;
  roles: string[];
  permissions: string[];
  csrfRefreshError: unknown;
  logoutError: unknown;
}

const useUserStore = defineStore('user', {
  state: (): UserState => ({
    token: getToken() || '',
    id: '',
    name: '',
    nickName: '',
    avatar: '',
    roles: [],
    permissions: [],
    csrfRefreshError: null,
    logoutError: null,
  }),
  actions: {
    // 登录
    login(userInfo: UserInfo) {
      endQuerySession();
      clearSecurityTokens();
      this.token = '';
      const username = userInfo.username.trim();
      const password = clampBcryptPassword(userInfo.password);
      const code = userInfo.code;
      const uuid = userInfo.uuid;
      return new Promise((resolve, reject) => {
        login(username, password, code, uuid)
          .then(async (res) => {
            setToken(res.token);
            this.token = res.token;
            const loginCsrfToken = res.csrfToken || '';
            if (loginCsrfToken) {
              setCsrfToken(loginCsrfToken);
              resolve(res);
              return;
            }
            try {
              const csrfResp = await withSessionCookieLock(() =>
                request<{ csrfToken?: string }>({
                  url: '/auth/csrf-token',
                  method: 'post',
                  silentSuccess: true,
                })
              );
              const csrfToken = csrfResp.csrfToken || '';
              if (csrfToken) {
                setCsrfToken(csrfToken);
              }
            } catch (csrfError) {
              this.csrfRefreshError = csrfError;
            }
            resolve(res);
          })
          .catch((error) => {
            reject(error);
          });
      });
    },
    // 新标签页/刷新后的会话恢复
    async restoreSession(): Promise<boolean> {
      const version = getSecuritySessionVersion();
      try {
        this.token = await refreshHttpSession();
        return true;
      } catch {
        if (getSecuritySessionVersion() !== version) return false;
        endQuerySession();
        clearSecurityTokens();
        this.token = '';
        return false;
      }
    },
    // 获取用户信息
    async getInfo() {
      const sessionVersion = getSecuritySessionVersion();
      const res = await getInfo();
      if (sessionVersion !== getSecuritySessionVersion()) {
        throw new AbortError({ message: '会话已切换，忽略旧的用户信息' });
      }
      const user = res.user;
      let avatar = user.avatar || '';
      if (!isHttp(avatar)) {
        avatar = isEmpty(avatar) ? defAva : import.meta.env.VITE_APP_BASE_API + avatar;
      }
      this.roles = res.roles?.length ? res.roles : ['ROLE_DEFAULT'];
      this.permissions = res.roles?.length ? res.permissions : [];
      this.id = user.userId;
      this.name = user.userName;
      this.nickName = user.nickName;
      this.avatar = avatar;
      setQuerySession(this.id, this.roles, this.permissions);
      return res;
    },
    // 退出系统
    logOut(options: LogoutOptions = {}) {
      endQuerySession();
      clearSecurityTokens();
      return new Promise((resolve) => {
        logout(options)
          .catch((error) => {
            this.logoutError = error;
          })
          .then(() => {
            this.token = '';
            this.roles = [];
            this.permissions = [];
            clearSecurityTokens();
            resolve(undefined);
          });
      });
    },
  },
});

export default useUserStore;
export { useUserStore };
