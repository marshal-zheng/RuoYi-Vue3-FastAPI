import type { RuntimeConfig, RuntimeMode } from './mode';
import type { DemoRuntimeLogger } from './logger';
import {
  exportDemoRuntimeScenario,
  resetDemoRuntimeScenario,
  type DemoRuntimeSnapshot,
  type DemoScenarioSnapshot,
} from './state';
import type { DemoScenarioPackage } from '@/demo/scenarios';

export interface DemoRuntimeDevtools {
  getMode(): RuntimeMode;
  getScenario(): DemoScenarioSnapshot;
  getSnapshot(): DemoRuntimeSnapshot;
  resetScenario(): Promise<DemoScenarioSnapshot>;
  exportScenario(): Promise<DemoScenarioPackage>;
}

declare global {
  interface Window {
    __DEMO_RUNTIME__?: DemoRuntimeDevtools;
  }
}

export function clearDemoRuntimeDevtools() {
  if (typeof window === 'undefined') {
    return;
  }

  delete window.__DEMO_RUNTIME__;
}

export function exposeDemoRuntimeDevtools(
  config: RuntimeConfig,
  snapshot: DemoRuntimeSnapshot,
  logger: DemoRuntimeLogger
) {
  clearDemoRuntimeDevtools();

  if (typeof window === 'undefined' || !config.debug) {
    return;
  }

  let currentSnapshot = snapshot;

  window.__DEMO_RUNTIME__ = Object.freeze({
    getMode: () => config.mode,
    getScenario: () => currentSnapshot.scenario,
    getSnapshot: () => currentSnapshot,
    resetScenario: async () => {
      currentSnapshot = await resetDemoRuntimeScenario(config, logger);
      return currentSnapshot.scenario;
    },
    exportScenario: () => exportDemoRuntimeScenario(),
  });

  logger.info('window.__DEMO_RUNTIME__ 调试入口已暴露。', {
    scenarioId: snapshot.scenario.id,
  });
}
