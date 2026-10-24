import { beforeEach, describe, expect, it, vi } from 'vitest';

const loadAuthModule = () => import('@/utils/auth');

describe('auth token store', () => {
  beforeEach(async () => {
    vi.resetModules();
    sessionStorage.clear();
    const auth = await loadAuthModule();
    auth.clearSecurityTokens();
  });

  it('stores access token for current tab and survives module reload', async () => {
    let auth = await loadAuthModule();
    expect(auth.getToken()).toBeUndefined();

    auth.setToken('access-1');
    expect(auth.getToken()).toBe('access-1');

    vi.resetModules();
    auth = await loadAuthModule();
    expect(auth.getToken()).toBe('access-1');
  });

  it('stores csrf token for current tab and survives module reload', async () => {
    let auth = await loadAuthModule();
    expect(auth.getCsrfToken()).toBeUndefined();

    auth.setCsrfToken('csrf-1');
    expect(auth.getCsrfToken()).toBe('csrf-1');

    vi.resetModules();
    auth = await loadAuthModule();
    expect(auth.getCsrfToken()).toBe('csrf-1');
  });

  it('clears all security tokens', async () => {
    const auth = await loadAuthModule();
    auth.setToken('access-2');
    auth.setCsrfToken('csrf-2');
    auth.clearSecurityTokens();
    expect(auth.getToken()).toBeUndefined();
    expect(auth.getCsrfToken()).toBeUndefined();
  });
});
