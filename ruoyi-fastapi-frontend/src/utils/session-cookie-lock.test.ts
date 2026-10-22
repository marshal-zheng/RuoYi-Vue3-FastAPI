import { afterEach, describe, expect, it, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import { login, logout } from '@/api/login';
import { createApiPath } from '@/mocks/constants';
import { clearSecurityTokens } from '@/utils/auth';
import { createSessionTransport } from './session';
import { setupMainlineMockHandlers } from '../../tests/mocks/mainline';
import { mockServer } from '../../tests/mocks/server';

const deferred = () => {
  let resolve!: () => void;
  const promise = new Promise<void>((done) => {
    resolve = done;
  });
  return { promise, resolve };
};

describe('authentication cookie writes', () => {
  setupMainlineMockHandlers();

  afterEach(() => {
    clearSecurityTokens();
    vi.unstubAllGlobals();
  });

  it.each(['login', 'logout'] as const)(
    'serializes %s behind another tab refresh',
    async (operation) => {
      const entered = deferred();
      const release = deferred();
      const events: string[] = [];
      let queue = Promise.resolve();
      const lock = vi.fn(
        (_name: string, optionsOrRun: unknown, callback?: () => Promise<unknown>) => {
          const run = (callback ?? optionsOrRun) as () => Promise<unknown>;
          const result = queue.then(run);
          queue = result.then(
            () => undefined,
            () => undefined
          );
          return result;
        }
      );
      vi.stubGlobal('navigator', { locks: { request: lock } });
      mockServer.use(
        http.post(createApiPath('/auth/refresh'), async () => {
          events.push('refresh');
          entered.resolve();
          await release.promise;
          return HttpResponse.json({
            token: 'renewed-token',
            csrfToken: 'renewed-csrf',
          });
        }),
        http.post(createApiPath(operation === 'login' ? '/login' : '/auth/logout'), () => {
          events.push(operation);
          return operation === 'login'
            ? HttpResponse.json({ token: 'new-login-token' })
            : new HttpResponse(null, { status: 204 });
        })
      );
      const refresh = createSessionTransport(vi.fn()).refresh();
      await entered.promise;
      const mutation = operation === 'login' ? login('qa', 'qa-password', '', '') : logout();
      try {
        await vi.waitFor(() => expect(lock).toHaveBeenCalledTimes(2));
        expect(events).toEqual(['refresh']);
        expect(lock.mock.calls[0][0]).toBe(lock.mock.calls[1][0]);
      } finally {
        release.resolve();
        await Promise.all([refresh, mutation]);
      }
      expect(events).toEqual(['refresh', operation]);
    }
  );
});
