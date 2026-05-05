import { expect } from 'vitest';

import { createTimeoutHandler, type MockHttpMethod } from '@/mocks/handlers/error-common';
import request from '@/utils/request';

import { mockServer } from '../mocks/server';

type RequestMethod = Exclude<MockHttpMethod, 'all'>;

export async function expectRequestTimeout(
  method: RequestMethod,
  path: string,
  data?: Record<string, unknown>
): Promise<void> {
  mockServer.use(createTimeoutHandler(method, path, { delayMs: 30 }));

  await expect(
    request({
      url: path,
      method,
      data,
      timeout: 1,
      silentError: true,
      skipRelogin: true,
      headers: {
        repeatSubmit: false,
      },
    })
  ).rejects.toMatchObject({
    status: 504,
    problem: {
      errorCode: 'MOCK_TIMEOUT',
    },
  });
}
