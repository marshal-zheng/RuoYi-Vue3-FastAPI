import { login, logout, getInfo } from '@/api/login';
import { defineStore } from 'pinia';
import { clearSecurityTokens, getToken, setCsrfToken, setToken } from '@/utils/auth';
import { isHttp, isEmpty } from '@/utils/validate';
import { clampBcryptPassword } from '@/utils/password';
import defAva from '@/assets/images/profile.jpg';
import request from '@/utils/request';

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
  }),
  actions: {
    // 登录
    login(userInfo: UserInfo) {
      const username = userInfo.username.trim();
      const password = clampBcryptPassword(userInfo.password);
      const code = userInfo.code;
      const uuid = userInfo.uuid;
      return new Promise((resolve, reject) => {
        login(username, password, code, uuid)
          .then(async (res) => {
            setToken(res.token);
            this.token = res.token;
            const loginCsrfToken = res.csrfToken || res.csrf_token || '';
            if (loginCsrfToken) {
              setCsrfToken(loginCsrfToken);
              resolve(res);
              return;
            }
            try {
              const csrfResp = await request<{ csrfToken?: string; csrf_token?: string }>({
                url: '/auth/csrf-token',
                method: 'post',
                silentSuccess: true,
              });
              const csrfToken = csrfResp.csrfToken || csrfResp.csrf_token || '';
              if (csrfToken) {
                setCsrfToken(csrfToken);
              }
            } catch (csrfError) {
              console.warn('获取CSRF token失败，后续敏感操作可能被后端拒绝', csrfError);
            }
            resolve(res);
          })
          .catch((error) => {
            reject(error);
          });
      });
    },
    // 新标签页/刷新后的会话恢复
    restoreSession() {
      return new Promise<boolean>((resolve) => {
        request<{ token?: string; csrfToken?: string; csrf_token?: string }>({
          url: '/auth/refresh',
          method: 'post',
          isToken: false,
          skipRelogin: true,
          silentSuccess: true,
          silentError: true,
        })
          .then((res) => {
            const token = res.token || '';
            if (!token) {
              clearSecurityTokens();
              this.token = '';
              resolve(false);
              return;
            }
            setToken(token);
            this.token = token;
            const csrfToken = res.csrfToken || res.csrf_token || '';
            if (csrfToken) {
              setCsrfToken(csrfToken);
            }
            resolve(true);
          })
          .catch(() => {
            clearSecurityTokens();
            this.token = '';
            resolve(false);
          });
      });
    },
    // 获取用户信息
    getInfo() {
      return new Promise((resolve, reject) => {
        getInfo()
          .then((res) => {
            const user = res.user;
            let avatar = user.avatar || '';
            if (!isHttp(avatar)) {
              avatar = isEmpty(avatar) ? defAva : import.meta.env.VITE_APP_BASE_API + avatar;
            }
            if (res.roles && res.roles.length > 0) {
              // 验证返回的roles是否是一个非空数组
              this.roles = res.roles;
              this.permissions = res.permissions;
            } else {
              this.roles = ['ROLE_DEFAULT'];
            }
            this.id = user.userId;
            this.name = user.userName;
            this.nickName = user.nickName;
            this.avatar = avatar;
            resolve(res);
          })
          .catch((error) => {
            reject(error);
          });
      });
    },
    // 退出系统
    logOut(options: LogoutOptions = {}) {
      return new Promise((resolve) => {
        logout(options)
          .catch((error) => {
            console.warn('Logout request failed, fallback to client-side cleanup only.', error);
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
