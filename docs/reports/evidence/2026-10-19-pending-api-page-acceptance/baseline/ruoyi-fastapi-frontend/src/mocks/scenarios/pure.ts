import { createHandlers } from '../handlers';
import type { MockRuntimeHandler } from '../types';

export function createPureScenarioHandlers(): MockRuntimeHandler[] {
  return createHandlers('pure');
}
