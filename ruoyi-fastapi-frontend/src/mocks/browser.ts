// @ts-nocheck
import { setupWorker, type SetupWorkerApi } from 'msw/browser'

import { createScenarioHandlers } from './scenarios'
import type { MockScenario, MockStrategy, StartMockOptions } from './types'

declare global {
  interface Window {
    __MSW_WORKER__?: SetupWorkerApi
    __MSW_STRATEGY__?: MockStrategy
    __MSW_SCENARIO__?: MockScenario
  }
}

function ensureWorker(
  strategy: MockStrategy,
  scenario: MockScenario
): SetupWorkerApi {
  const handlers = createScenarioHandlers(strategy, scenario)
  const existing = window.__MSW_WORKER__
  if (existing) {
    existing.resetHandlers(...handlers)
    window.__MSW_STRATEGY__ = strategy
    window.__MSW_SCENARIO__ = scenario
    return existing
  }

  const worker = setupWorker(...handlers)
  window.__MSW_WORKER__ = worker
  window.__MSW_STRATEGY__ = strategy
  window.__MSW_SCENARIO__ = scenario
  return worker
}

export async function startBrowserMock(options: StartMockOptions = {}) {
  if (typeof window === 'undefined') {
    return undefined
  }

  const strategy: MockStrategy = options.strategy ?? 'fallback'
  const scenario: MockScenario =
    options.scenario ?? (strategy === 'pure' ? 'pure' : 'default')

  const worker = ensureWorker(strategy, scenario)
  await worker.start({
    onUnhandledRequest: options.onUnhandledRequest ?? 'bypass'
  })
  return worker
}
