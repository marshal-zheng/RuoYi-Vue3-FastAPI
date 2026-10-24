import type { MockRuntimeHandler, MockScenario, MockStrategy } from '../types';
import { createMockHandlers } from '../handlers';
import { isMockErrorScenario } from '../handlers/error-common';

import { createDefaultScenarioHandlers } from './default';
import { createErrorProfileHandlers } from './error';
import { createPureScenarioHandlers } from './pure';

export function createScenarioHandlers(
  strategy: MockStrategy,
  scenario: MockScenario = 'default'
): MockRuntimeHandler[] {
  if (isMockErrorScenario(scenario)) {
    return createErrorProfileHandlers(scenario);
  }

  if (scenario === 'pure') {
    return createMockHandlers({ strategy: 'pure' });
  }

  return createMockHandlers({ strategy });
}

export { createDefaultScenarioHandlers, createErrorProfileHandlers, createPureScenarioHandlers };
