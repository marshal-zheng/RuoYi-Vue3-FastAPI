import { resolveRuntimeConfig } from '@/demo/runtime/mode';
import { startBrowserMock } from './browser';
import type { MockMode, MockScenario, MockStrategy, StartMockOptions } from './types';

function resolveModeFromEnv(): MockMode {
  return resolveRuntimeConfig().mockMode;
}

function resolveScenario(strategy: MockStrategy, scenario?: MockScenario): MockScenario {
  if (scenario) return scenario;
  return strategy === 'pure' ? 'pure' : 'default';
}

export async function setupBrowserMocks(options: StartMockOptions = {}) {
  const mode = resolveModeFromEnv();
  const strategy = options.strategy ?? (mode === 'off' ? undefined : (mode as MockStrategy));

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

export { resolveModeFromEnv };
export type { MockMode, MockScenario, MockStrategy, StartMockOptions };
