import request from '@/utils/request';
import { clampBcryptPassword } from '@/utils/password';

// 登录方法
export function login(username, password, code, uuid) {
  const data = {
    username,
    password: clampBcryptPassword(password),
    code,
    uuid,
  };
  return request({
    url: '/login',
    headers: {
      isToken: false,
      repeatSubmit: false,
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    method: 'post',
    data: data,
  });
}

// 注册方法
export function register(data) {
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
export function logout() {
  return request({
    url: '/logout',
    method: 'post',
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
  });
}
