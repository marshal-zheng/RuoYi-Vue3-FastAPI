// @ts-nocheck
import type { MockScenario, MockStrategy } from '../types'

import { createDefaultScenarioHandlers } from './default'
import { createPureScenarioHandlers } from './pure'

export function createScenarioHandlers(
  strategy: MockStrategy,
  scenario: MockScenario = 'default'
) {
  if (scenario === 'pure') {
    return createPureScenarioHandlers()
  }

  return createDefaultScenarioHandlers(strategy)
}
