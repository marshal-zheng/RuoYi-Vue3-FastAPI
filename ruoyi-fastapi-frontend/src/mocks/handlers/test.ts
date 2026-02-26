// @ts-nocheck
import { http, HttpResponse } from 'msw';

import type { MockStrategy } from '../types';
import { resultSuccess } from '../utils/response';
import { withBackendFallback } from '../utils/with-backend-fallback';

export function createTestHandlers(strategy: MockStrategy) {
  return [
    http.get('/dev-api/test/mock', ({ request }) =>
      withBackendFallback(
        request,
        () =>
          HttpResponse.json(
            resultSuccess({
              message: 'mock ssss',
              timestamp: Date.now(),
            })
          ),
        { strategy, tag: 'test:mock' }
      )
    ),
  ];
}
