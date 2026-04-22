import { describe, expect, it } from 'vitest';

import { readJsonBody } from './request';

describe('mock request body reader', () => {
  it('parses JSON bodies', async () => {
    const request = new Request('http://localhost/api/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        username: 'admin',
        password: 'admin123',
      }),
    });

    await expect(readJsonBody(request)).resolves.toEqual({
      username: 'admin',
      password: 'admin123',
    });
  });

  it('parses x-www-form-urlencoded bodies', async () => {
    const request = new Request('http://localhost/api/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: 'username=admin&password=admin123&code=1234',
    });

    await expect(readJsonBody(request)).resolves.toEqual({
      username: 'admin',
      password: 'admin123',
      code: '1234',
    });
  });

  it('parses FormData bodies', async () => {
    const formData = new FormData();
    formData.set('username', 'admin');
    formData.set('password', 'admin123');

    const request = new Request('http://localhost/api/login', {
      method: 'POST',
      body: formData,
    });

    await expect(readJsonBody(request)).resolves.toEqual({
      username: 'admin',
      password: 'admin123',
    });
  });
});
