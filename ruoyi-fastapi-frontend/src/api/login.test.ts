import { beforeEach, describe, expect, it } from 'vitest';

import {
  createApiContractHandlers,
  createStatusHandler,
} from '../../tests/mocks/api-contract-handlers';
import { mockServer } from '../../tests/mocks/server';
import { clampBcryptPassword } from '@/utils/password';
import { getCodeImg, getInfo, login, logout, register } from './login';

describe('login API contract', () => {
  beforeEach(() => {
    mockServer.use(...createApiContractHandlers());
  });

  it('serializes login payload as x-www-form-urlencoded data through MSW', async () => {
    const result = await login('admin', 'admin123', '1234', 'uuid-1');

    expect(result).toMatchObject({
      token: 'jwt-token-admin',
      csrfToken: 'csrf-token-from-login',
      payload: {
        username: 'admin',
        password: 'admin123',
        code: '1234',
        uuid: 'uuid-1',
      },
    });
  });

  it('clamps long login and register passwords before sending the request', async () => {
    const longPassword = '密码'.repeat(80);
    const clamped = clampBcryptPassword(longPassword);

    const loginResult = await login('admin', longPassword, '1234', 'uuid-long');
    expect(loginResult.payload.password).toBe(clamped);

    const registerResult = await register({
      username: 'new-user',
      password: longPassword,
      confirmPassword: longPassword,
    });
    expect(registerResult.payload).toMatchObject({
      username: 'new-user',
      password: clamped,
      confirmPassword: clamped,
    });
  });

  it('covers auth metadata endpoints through the real request path', async () => {
    await expect(getInfo()).resolves.toMatchObject({
      user: expect.objectContaining({ userName: 'admin' }),
      roles: ['admin'],
      permissions: ['*:*:*'],
    });
    await expect(logout({ silentSuccess: true, silentError: true })).resolves.toBeNull();
    await expect(getCodeImg()).resolves.toMatchObject({
      captchaEnabled: false,
      uuid: 'captcha-uuid-1',
    });
  });

  it('surfaces login API failures from the request error mapping', async () => {
    mockServer.use(createStatusHandler('post', '/login', 429));

    await expect(login('admin', 'admin123', '1234', 'uuid-1')).rejects.toMatchObject({
      status: 429,
    });
  });
});
