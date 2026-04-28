import request from '@/utils/request';
import { clampBcryptPassword } from '@/utils/password';

// 登录方法
export function login(username: string, password: string, code: string, uuid: string) {
  const data = new URLSearchParams({
    username,
    password: clampBcryptPassword(password),
    code,
    uuid,
  });
  return request({
    url: '/login',
    headers: {
      isToken: false,
      repeatSubmit: false,
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    method: 'post',
    data,
    skipRelogin: true,
    silentSuccess: true,
    feedback: { mode: 'auto' },
  });
}

// 注册方法
export function register(data: Record<string, any>) {
  const payload = { ...data };
  if (payload.password) {
    payload.password = clampBcryptPassword(payload.password);
  }
  if (payload.confirmPassword) {
    payload.confirmPassword = clampBcryptPassword(payload.confirmPassword);
  }
  return request({
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
  return request({
    url: '/getInfo',
    method: 'get',
  });
}

// 退出方法
interface LogoutRequestOptions {
  silentSuccess?: boolean;
  silentError?: boolean;
}

export function logout(options: LogoutRequestOptions = {}) {
  return request({
    url: '/auth/logout',
    method: 'post',
    feedback: { mode: 'silent' },
    ...options,
  });
}

// 获取验证码
export function getCodeImg() {
  return request({
    url: '/captchaImage',
    headers: {
      isToken: false,
    },
    method: 'get',
    timeout: 20000,
    feedback: { mode: 'silent' },
  });
}
