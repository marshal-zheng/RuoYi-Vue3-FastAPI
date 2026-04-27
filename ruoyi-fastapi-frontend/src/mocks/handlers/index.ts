import type { MockRuntimeHandler, MockStrategy } from '../types';

import { createSystemHandlers } from './system';
import { createUserHandlers } from './user';
import { createTestHandlers } from './test';
import { createMonitorHandlers } from './monitor';

export function createHandlers(strategy: MockStrategy): MockRuntimeHandler[] {
  return [
    ...createSystemHandlers(strategy),
    ...createUserHandlers(strategy),
    ...createTestHandlers(strategy),
    ...createMonitorHandlers(strategy),
  ];
}
