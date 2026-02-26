import { login, logout, getInfo } from '@/api/login';
import { getToken, setToken, removeToken } from '@/utils/auth';
import { isHttp, isEmpty } from '@/utils/validate';
import { clampBcryptPassword } from '@/utils/password';
import defAva from '@/assets/images/profile.jpg';

interface UserInfo {
  username: string;
  password: string;
  code: string;
  uuid: string;
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
          .then((res) => {
            setToken(res.token);
            this.token = res.token;
            resolve(res);
          })
          .catch((error) => {
            reject(error);
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
    logOut() {
      return new Promise((resolve) => {
        logout()
          .catch((error) => {
            console.warn('Logout request failed, fallback to client-side cleanup only.', error);
          })
          .then(() => {
            this.token = '';
            this.roles = [];
            this.permissions = [];
            removeToken();
            resolve(undefined);
          });
      });
    },
  },
});

export default useUserStore;
