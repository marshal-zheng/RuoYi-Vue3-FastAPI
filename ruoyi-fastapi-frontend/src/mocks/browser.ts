import { setupWorker, type SetupWorker } from 'msw/browser';

import { createScenarioHandlers } from './scenarios';
import type { MockRuntimeHandler, MockScenario, MockStrategy, StartMockOptions } from './types';

declare global {
  interface Window {
    __MSW_WORKER__?: SetupWorker;
    __MSW_STRATEGY__?: MockStrategy;
    __MSW_SCENARIO__?: MockScenario;
    __MSW_RUNTIME_HANDLERS__?: MockRuntimeHandler[];
  }
}

function ensureWorker(
  strategy: MockStrategy,
  scenario: MockScenario,
  handlers: MockRuntimeHandler[]
): SetupWorker {
  const existing = window.__MSW_WORKER__;
  if (existing) {
    existing.resetHandlers(...handlers);
    window.__MSW_STRATEGY__ = strategy;
    window.__MSW_SCENARIO__ = scenario;
    window.__MSW_RUNTIME_HANDLERS__ = handlers;
    return existing;
  }

  const worker = setupWorker(...handlers);
  window.__MSW_WORKER__ = worker;
  window.__MSW_STRATEGY__ = strategy;
  window.__MSW_SCENARIO__ = scenario;
  window.__MSW_RUNTIME_HANDLERS__ = handlers;
  return worker;
}

export async function startBrowserMock(
  options: StartMockOptions = {}
): Promise<SetupWorker | undefined> {
  if (typeof window === 'undefined') {
    return undefined;
  }

  const strategy: MockStrategy = options.strategy ?? 'fallback';
  const scenario: MockScenario = options.scenario ?? (strategy === 'pure' ? 'pure' : 'default');
  const handlers: MockRuntimeHandler[] =
    options.handlers ?? createScenarioHandlers(strategy, scenario);

  const worker = ensureWorker(strategy, scenario, handlers);
  await worker.start({
    onUnhandledRequest: options.onUnhandledRequest ?? 'bypass',
  });
  return worker;
}

// Vite HMR 热更新支持
if (import.meta.hot) {
  import.meta.hot.accept('./handlers/index', () => {
    const worker = window.__MSW_WORKER__;
    const strategy = window.__MSW_STRATEGY__ ?? 'fallback';
    const scenario = window.__MSW_SCENARIO__ ?? 'default';
    if (worker) {
      const handlers =
        window.__MSW_RUNTIME_HANDLERS__ ?? createScenarioHandlers(strategy, scenario);
      worker.resetHandlers(...handlers);
      console.log('[MSW] Handlers 已热更新');
    }
  });
}
