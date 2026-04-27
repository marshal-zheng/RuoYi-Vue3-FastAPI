import { afterAll, afterEach, beforeAll } from 'vitest';

import { mockServer, resetMockServerHandlers } from './server';

export function setupMockServerLifecycle() {
  beforeAll(() => {
    mockServer.listen({
      onUnhandledRequest: 'error',
    });
  });

  afterEach(() => {
    resetMockServerHandlers();
  });

  afterAll(() => {
    mockServer.close();
  });
}

