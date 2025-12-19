// @ts-nocheck
import { setupServer, type SetupServerApi } from 'msw/node'

import { createScenarioHandlers } from './scenarios'
import type { MockScenario, MockStrategy } from './types'

export function createMockServer(
  strategy: MockStrategy = 'fallback',
  scenario: MockScenario = strategy === 'pure' ? 'pure' : 'default'
): SetupServerApi {
  return setupServer(...createScenarioHandlers(strategy, scenario))
}
