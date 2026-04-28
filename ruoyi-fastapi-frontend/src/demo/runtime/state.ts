import type { RuntimeConfig } from './mode';
import type { DemoRuntimeLogger } from './logger';
import { getDemoOfflineDb } from '@/demo/db';
import { getDemoScenarioPackage, type DemoScenarioPackage } from '@/demo/scenarios';
import { ScenarioRepository, type DemoActiveScenarioMeta } from '@/demo/repositories';

export interface DemoScenarioSnapshot {
  id: string;
  name: string;
  version: string;
  schemaVersion: 1;
  fingerprint: string;
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
    loadedAt: activeScenario.importedAt,
  };
}

export async function initializeDemoRuntimeState(
  config: RuntimeConfig,
  logger: DemoRuntimeLogger
): Promise<DemoRuntimeSnapshot> {
  const db = getDemoOfflineDb();
  const scenarioRepository = new ScenarioRepository(db);
  const scenarioPackage = getDemoScenarioPackage(config.scenarioId, {
    allowCandidateScenarios: config.allowCandidateScenarios,
  });
  const result = await scenarioRepository.ensureScenario(scenarioPackage);
  const scenario = createScenarioSnapshot(result.activeScenario);

  logger.info('初始化离线演示运行态边界。', {
    apiPrefix: config.apiPrefix,
    scenarioId: scenario.id,
    persistence: 'indexeddb',
    dbName: db.name,
  });
  logger.info(
    result.imported ? '默认场景已导入 IndexedDB。' : '默认场景已匹配，保留本地演示数据。',
    {
      scenarioId: scenario.id,
      schemaVersion: scenario.schemaVersion,
      fingerprint: scenario.fingerprint,
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
    scenarioId: config.scenarioId,
  });
  const db = getDemoOfflineDb();
  const scenarioRepository = new ScenarioRepository(db);
  const scenarioPackage = getDemoScenarioPackage(config.scenarioId, {
    allowCandidateScenarios: config.allowCandidateScenarios,
  });
  const result = await scenarioRepository.resetScenario(scenarioPackage);
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
