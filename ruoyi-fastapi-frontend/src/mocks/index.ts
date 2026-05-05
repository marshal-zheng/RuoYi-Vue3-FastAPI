import { startBrowserMock } from './browser';
import { isMockRuntimeMode, resolveRuntimeConfig, strategyForRuntimeMode } from './runtime/mode';
import type { MockNetworkStrategy, MockScenario, MockStrategy, StartMockOptions } from './types';

function resolveStrategyFromEnv(): MockStrategy | undefined {
  const runtimeMode = resolveRuntimeConfig().mode;
  return isMockRuntimeMode(runtimeMode) ? strategyForRuntimeMode(runtimeMode) : undefined;
}

function resolveScenario(strategy: MockNetworkStrategy, scenario?: MockScenario): MockScenario {
  if (scenario) return scenario;
  return strategy === 'pure' ? 'pure' : 'default';
}

export async function setupBrowserMocks(options: StartMockOptions = {}) {
  const strategy = options.strategy ?? resolveStrategyFromEnv();

  if (!strategy) {
    return undefined;
  }

  const scenario = resolveScenario(strategy, options.scenario);

  return startBrowserMock({
    ...options,
    strategy,
    scenario,
  });
}

export { resolveStrategyFromEnv };
export type { MockNetworkStrategy, MockScenario, MockStrategy, StartMockOptions };
