// @ts-nocheck
import type { MockStrategy } from '../types'
import { createHandlers } from '../handlers'

export function createDefaultScenarioHandlers(strategy: MockStrategy) {
  return createHandlers(strategy)
}
