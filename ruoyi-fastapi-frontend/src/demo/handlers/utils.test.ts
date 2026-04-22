import { describe, expect, it } from 'vitest';

import { readDemoRequestBody } from './utils';

describe('readDemoRequestBody', () => {
  it('parses JSON payloads', async () => {
    const request = new Request('http://localhost/api/demo', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        username: 'admin',
        password: 'admin123',
      }),
    });

    await expect(readDemoRequestBody(request)).resolves.toEqual({
      username: 'admin',
      password: 'admin123',
    });
  });

  it('parses x-www-form-urlencoded payloads', async () => {
    const request = new Request('http://localhost/api/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: 'username=admin&password=admin123',
    });

    await expect(readDemoRequestBody(request)).resolves.toEqual({
      username: 'admin',
      password: 'admin123',
    });
  });

  it('parses FormData payloads', async () => {
    const formData = new FormData();
    formData.set('username', 'admin');
    formData.set('password', 'admin123');

    const request = new Request('http://localhost/api/login', {
      method: 'POST',
      body: formData,
    });

    await expect(readDemoRequestBody(request)).resolves.toEqual({
      username: 'admin',
      password: 'admin123',
    });
  });

  it('returns an empty object for empty payloads', async () => {
    const request = new Request('http://localhost/api/demo', {
      method: 'POST',
    });

    await expect(readDemoRequestBody(request)).resolves.toEqual({});
  });
});
