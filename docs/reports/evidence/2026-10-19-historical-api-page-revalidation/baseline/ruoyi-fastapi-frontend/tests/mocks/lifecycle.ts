import { afterAll, afterEach, beforeAll } from 'vitest';

import { mockServer, resetMockServerHandlers } from './server';

export function setupMockServerLifecycle() {
  beforeAll(() => {
    mockServer.listen({
      onUnhandledRequest(request, print) {
        const accept = request.headers.get('accept') ?? '';
        const url = new URL(request.url);
        if (accept.includes('msw/passthrough') || url.hostname === '127.0.0.1') {
          return;
        }
        print.error();
      },
    });
  });

  afterEach(() => {
    resetMockServerHandlers();
  });

  afterAll(() => {
    mockServer.close();
  });
}
