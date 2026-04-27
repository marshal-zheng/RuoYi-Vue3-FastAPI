import type { MockRuntimeHandler, MockStrategy } from '../types';
import { createHandlers } from '../handlers';

export function createDefaultScenarioHandlers(strategy: MockStrategy): MockRuntimeHandler[] {
  return createHandlers(strategy);
}
