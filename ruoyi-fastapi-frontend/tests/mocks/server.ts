import { setupServer } from 'msw/node';

import { createScenarioHandlers } from '@/mocks/scenarios';

export const mockServer = setupServer(...createScenarioHandlers('pure', 'pure'));

export function resetMockServerHandlers() {
  mockServer.resetHandlers();
}

