import type { MockRuntimeHandler, MockScenario, MockStrategy } from '../types';

import { createDefaultScenarioHandlers } from './default';
import { createPureScenarioHandlers } from './pure';

export function createScenarioHandlers(
  strategy: MockStrategy,
  scenario: MockScenario = 'default'
): MockRuntimeHandler[] {
  if (scenario === 'pure') {
    return createPureScenarioHandlers();
  }

  return createDefaultScenarioHandlers(strategy);
}
