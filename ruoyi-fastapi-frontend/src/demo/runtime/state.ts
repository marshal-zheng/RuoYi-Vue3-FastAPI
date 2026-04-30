import type { RuntimeConfig } from './mode';
import type { DemoRuntimeLogger } from './logger';
import { getDemoOfflineDb } from '@/demo/db';
import { defaultDemoScenario, type DemoScenarioPackage } from '@/demo/scenarios';
import {
  ScenarioRepository,
  type DemoActiveScenarioMeta,
  type DemoScenarioImportResult,
} from '@/demo/repositories';
import { loadRuntimeScenarioPackage } from './scenario-package-loader';

export interface DemoScenarioSnapshot {
  id: string;
  name: string;
  version: string;
  schemaVersion: 1;
  fingerprint: string;
  source: DemoActiveScenarioMeta['source'];
  contractFingerprint?: string;
  fallbackReason?: DemoActiveScenarioMeta['fallbackReason'];
  validationSummary?: DemoActiveScenarioMeta['validationSummary'];
  loadedAt: string;
}

export interface DemoRuntimeSnapshot {
  mode: 'demo-offline';
  apiPrefix: string;
  debug: boolean;
  scenario: DemoScenarioSnapshot;
  persistence: 'indexeddb';
  dbName: string;
  startedAt: string;
}

function createScenarioSnapshot(activeScenario: DemoActiveScenarioMeta): DemoScenarioSnapshot {
  return {
    id: activeScenario.scenarioId,
    name: activeScenario.name,
    version: activeScenario.scenarioVersion,
    schemaVersion: activeScenario.schemaVersion,
    fingerprint: activeScenario.fingerprint,
    source: activeScenario.source ?? 'bundle-default-v2',
    contractFingerprint: activeScenario.contractFingerprint,
    fallbackReason: activeScenario.fallbackReason,
    validationSummary: activeScenario.validationSummary,
    loadedAt: activeScenario.importedAt,
  };
}

export async function initializeDemoRuntimeState(
  config: RuntimeConfig,
  logger: DemoRuntimeLogger
): Promise<DemoRuntimeSnapshot> {
  const db = getDemoOfflineDb();
  const scenarioRepository = new ScenarioRepository(db);
  const selection = await loadRuntimeScenarioPackage<DemoScenarioImportResult>(config, logger, {
    importScenario: (candidate) =>
      scenarioRepository.ensureScenario(candidate.package, {
        source: candidate.source,
        contractFingerprint: candidate.meta?.contractFingerprint,
        fallbackReason: candidate.fallbackReason,
        validationSummary: candidate.meta?.validationSummary,
      }),
  });
  const result = selection.importResult;

  if (!result) {
    throw new Error('Runtime scenario loader did not import a scenario.');
  }

  const scenario = createScenarioSnapshot(result.activeScenario);

  logger.info('初始化离线演示运行态边界。', {
    apiPrefix: config.apiPrefix,
    scenarioId: scenario.id,
    source: scenario.source,
    persistence: 'indexeddb',
    dbName: db.name,
  });
  logger.info(
    result.imported ? '运行态场景已导入 IndexedDB。' : '运行态场景已匹配，保留本地演示数据。',
    {
      scenarioId: scenario.id,
      schemaVersion: scenario.schemaVersion,
      fingerprint: scenario.fingerprint,
      source: scenario.source,
      fallbackReason: scenario.fallbackReason,
    }
  );

  return {
    mode: 'demo-offline',
    apiPrefix: config.apiPrefix,
    debug: config.debug,
    scenario,
    persistence: 'indexeddb',
    dbName: db.name,
    startedAt: new Date().toISOString(),
  };
}

export async function resetDemoRuntimeScenario(
  config: RuntimeConfig,
  logger: DemoRuntimeLogger
): Promise<DemoRuntimeSnapshot> {
  logger.info('收到显式重置场景请求。', {
    scenarioId: defaultDemoScenario.scenario.id,
  });
  const db = getDemoOfflineDb();
  const scenarioRepository = new ScenarioRepository(db);
  const result = await scenarioRepository.resetScenario(defaultDemoScenario, {
    source: 'bundle-default-v2',
  });
  const scenario = createScenarioSnapshot(result.activeScenario);

  logger.info('场景已重置并重新导入 IndexedDB。', {
    scenarioId: scenario.id,
    fingerprint: scenario.fingerprint,
  });

  return {
    mode: 'demo-offline',
    apiPrefix: config.apiPrefix,
    debug: config.debug,
    scenario,
    persistence: 'indexeddb',
    dbName: db.name,
    startedAt: new Date().toISOString(),
  };
}

export async function exportDemoRuntimeScenario(): Promise<DemoScenarioPackage> {
  const db = getDemoOfflineDb();
  const scenarioRepository = new ScenarioRepository(db);
  return scenarioRepository.exportCurrentScenario();
}
