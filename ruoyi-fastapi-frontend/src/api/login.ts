export interface LoginSession {
  token: string;
  csrfToken?: string;
}
import type { UserInfoModel, UserDetailReadModel, UserRegister } from '@/api/_generated/types.gen';
import request from '@/utils/request';
import { clampBcryptPassword } from '@/utils/password';
import { withSessionCookieLock } from '@/utils/session';

// 登录方法
export function login(username: string, password: string, code: string, uuid: string) {
  const data = new URLSearchParams({
    username,
    password: clampBcryptPassword(password),
    code,
    uuid,
  });
  return withSessionCookieLock(() =>
    request<LoginSession>({
      url: '/login',
      headers: {
        isToken: false,
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      method: 'post',
      data,
      skipRelogin: true,
      silentSuccess: true,
      feedback: { mode: 'auto' },
    })
  );
}

// 注册方法
export function register(data: UserRegister) {
  const payload = { ...data };
  if (payload.password) {
    payload.password = clampBcryptPassword(payload.password);
  }
  if (payload.confirmPassword) {
    payload.confirmPassword = clampBcryptPassword(payload.confirmPassword);
  }
  return request<UserDetailReadModel>({
    url: '/register',
    headers: {
      isToken: false,
    },
    method: 'post',
    data: payload,
    feedback: { mode: 'silent' },
  });
}

// 获取用户详细信息
export function getInfo() {
  return request<{
    user: UserInfoModel & {
      userId: number;
      userName: string;
      nickName: string;
    };
    roles: string[];
    permissions: string[];
  }>({
    url: '/getInfo',
    method: 'get',
    skipRelogin: true,
  });
}

// 退出方法
interface LogoutRequestOptions {
  silentSuccess?: boolean;
  silentError?: boolean;
}

export function logout(options: LogoutRequestOptions = {}) {
  return withSessionCookieLock(() =>
    request<null>({
      url: '/auth/logout',
      isToken: false,
      method: 'post',
      feedback: { mode: 'silent' },
      skipRelogin: true,
      silentError: true,
      ...options,
    })
  );
}

// 获取验证码
export function getCodeImg() {
  return request<{ captchaEnabled: boolean; img: string; uuid: string }>({
    url: '/captchaImage',
    headers: {
      isToken: false,
    },
    method: 'get',
    timeout: 20000,
    feedback: { mode: 'silent' },
  });
}
