import type { MockErrorScenario, MockRuntimeHandler } from '../types';
import { createErrorScenarioHandlers, mockErrorScenarios } from '../handlers/error-common';

export function createErrorProfileHandlers(scenario: MockErrorScenario): MockRuntimeHandler[] {
  return createErrorScenarioHandlers(scenario);
}

export { mockErrorScenarios };
