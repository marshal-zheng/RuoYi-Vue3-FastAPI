// @ts-nocheck
import { startBrowserMock } from './browser'
import type {
  MockMode,
  MockScenario,
  MockStrategy,
  StartMockOptions
} from './types'

function resolveModeFromEnv(): MockMode {
  const raw = import.meta.env.VITE_ENABLE_MOCK
  if (raw === 'pure') return 'pure'
  if (raw === 'fallback') return 'fallback'
  return 'off'
}

function resolveScenario(strategy: MockStrategy, scenario?: MockScenario) {
  if (scenario) return scenario
  return strategy === 'pure' ? 'pure' : 'default'
}

export async function setupBrowserMocks(
  options: StartMockOptions = {}
) {
  const mode = resolveModeFromEnv()
  const strategy =
    options.strategy ??
    (mode === 'off' ? undefined : (mode as MockStrategy))

  if (!strategy) {
    return undefined
  }

  const scenario = resolveScenario(strategy, options.scenario)

  return startBrowserMock({
    strategy,
    scenario,
    onUnhandledRequest: options.onUnhandledRequest
  })
}

export { resolveModeFromEnv }
export type { MockMode, MockScenario, MockStrategy, StartMockOptions }
