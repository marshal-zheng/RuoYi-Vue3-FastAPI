import 'fake-indexeddb/auto';

import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import { DemoOfflineDb } from '@/demo/db';
import {
  ProjectRepository,
  ProjectVersionRepository,
  ScenarioRepository,
  SimulationRepository,
  TopologyRepository,
} from '@/demo/repositories';
import { getDemoScenarioPackage, validateDemoScenarioPackage } from '@/demo/scenarios';
import { DemoProjectService, DemoSimulationService } from '@/demo/services';

import { realEstateP0AcceptanceDemoScenario } from './real-estate-p0-acceptance-demo';

let db: DemoOfflineDb;
let projectService: DemoProjectService;
let simulationService: DemoSimulationService;

describe('realEstateP0AcceptanceDemoScenario', () => {
  beforeEach(async () => {
    db = new DemoOfflineDb(`real-estate-p0-acceptance-demo-test-${crypto.randomUUID()}`);
    await new ScenarioRepository(db).ensureScenario(realEstateP0AcceptanceDemoScenario);
    projectService = new DemoProjectService(
      new ProjectRepository(db),
      new ProjectVersionRepository(db),
      new TopologyRepository(db)
    );
    simulationService = new DemoSimulationService(
      new ProjectRepository(db),
      new ProjectVersionRepository(db),
      new SimulationRepository(db)
    );
  });

  afterEach(async () => {
    await db.delete();
  });

  it('registers and validates the promoted P0 acceptance scenario package', () => {
    expect(getDemoScenarioPackage('real-estate-p0-acceptance-demo')).toStrictEqual(
      validateDemoScenarioPackage(realEstateP0AcceptanceDemoScenario)
    );
  });

  it('imports generated project and simulation slices into IndexedDB', async () => {
    await expect(db.projects.count()).resolves.toBe(6);
    await expect(db.projectVersions.count()).resolves.toBe(6);
    await expect(db.topologies.count()).resolves.toBe(6);
    await expect(db.simulationSessions.count()).resolves.toBe(6);

    await expect(projectService.listProjects({ projectName: '交付整改' })).resolves.toMatchObject({
      total: 1,
      items: [
        expect.objectContaining({
          projectId: 7001,
          projectName: '滨江云著一期交付整改专项',
          riskLevel: 'high',
        }),
      ],
    });

    await expect(
      simulationService.getStatus('real-estate-p0-acceptance-demo-session-1-1')
    ).resolves.toMatchObject({
      sessionId: 'real-estate-p0-acceptance-demo-session-1-1',
      status: 'running',
      messageCount: 1,
      alarmCount: 1,
    });
  });

  it('keeps generated semantic content free of generic placeholders', () => {
    const scenarioText = JSON.stringify(realEstateP0AcceptanceDemoScenario);

    expect(scenarioText).not.toContain('测试项目');
    expect(scenarioText).not.toContain('示例数据');
    expect(scenarioText).not.toContain('张三');
    expect(scenarioText).not.toContain('李四');
    expect(scenarioText).toContain('交付整改');
    expect(scenarioText).toContain('拿地测算');
    expect(scenarioText).toContain('客户维保');
  });
});
