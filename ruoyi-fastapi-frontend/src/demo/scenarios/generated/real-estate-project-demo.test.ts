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

import { realEstateProjectDemoScenario } from './real-estate-project-demo';

let db: DemoOfflineDb;
let projectService: DemoProjectService;
let simulationService: DemoSimulationService;

describe('realEstateProjectDemoScenario', () => {
  beforeEach(async () => {
    db = new DemoOfflineDb(`real-estate-project-demo-test-${crypto.randomUUID()}`);
    await new ScenarioRepository(db).ensureScenario(realEstateProjectDemoScenario);
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

  it('registers and validates the generated industry scenario package', () => {
    expect(getDemoScenarioPackage('real-estate-project-demo')).toStrictEqual(
      validateDemoScenarioPackage(realEstateProjectDemoScenario)
    );
  });

  it('imports real estate project data into IndexedDB for project services', async () => {
    await expect(db.projects.count()).resolves.toBe(6);
    await expect(db.projectVersions.count()).resolves.toBe(6);
    await expect(db.sequences.get('projects')).resolves.toMatchObject({
      value: 5207,
    });

    await expect(projectService.listProjects({ projectName: '预售' })).resolves.toMatchObject({
      total: 1,
      items: [
        expect.objectContaining({
          projectId: 5203,
          projectName: '南湖悦府预售筹备计划',
          projectDesc: expect.stringContaining('预售证办理'),
          owner: '营销项目经理-叶南乔',
          riskLevel: 'medium',
        }),
      ],
    });

    await expect(projectService.listProjectVersions({ projectId: 5201 })).resolves.toMatchObject({
      total: 1,
      items: [
        expect.objectContaining({
          versionId: 6201,
          versionName: '交付整改作战版',
          isLocked: '1',
        }),
      ],
    });
  });

  it('keeps the hand-authored project slice free of generic placeholder content', () => {
    const projectSlice = JSON.stringify(realEstateProjectDemoScenario.project);

    expect(projectSlice).not.toContain('测试项目');
    expect(projectSlice).not.toContain('示例数据');
    expect(projectSlice).not.toContain('张三');
    expect(projectSlice).not.toContain('李四');
    expect(projectSlice).toContain('交付整改');
    expect(projectSlice).toContain('预售');
    expect(projectSlice).toContain('拿地');
  });

  it('imports real estate simulation data for existing demo services', async () => {
    await expect(db.simulationSessions.count()).resolves.toBe(1);
    await expect(simulationService.getStatus('real-estate-session-5201')).resolves.toMatchObject({
      sessionId: 'real-estate-session-5201',
      status: 'running',
      messageCount: 1,
      alarmCount: 1,
    });
    await expect(simulationService.listMessages('real-estate-session-5201')).resolves.toEqual([
      expect.objectContaining({
        id: 'real-estate-message-1',
        senderNodeName: '工程整改组',
        receiverNodeName: '客户交付中心',
      }),
    ]);
    await expect(simulationService.listAlarms('real-estate-session-5201')).resolves.toEqual([
      expect.objectContaining({
        alarmId: 'real-estate-alarm-1',
        message: expect.stringContaining('交付整改关闭率'),
      }),
    ]);
  });
});
