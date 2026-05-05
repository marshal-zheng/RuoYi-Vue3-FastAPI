import { setupServer } from 'msw/node';

import { createMockHandlers } from '@/mocks/handlers';

export const mockServer = setupServer(...createMockHandlers({ strategy: 'pure' }));

export function resetMockServerHandlers() {
  mockServer.resetHandlers();
}
