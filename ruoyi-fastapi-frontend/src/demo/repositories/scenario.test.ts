import 'fake-indexeddb/auto';

import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import { DemoOfflineDb } from '@/demo/db';
import { defaultDemoScenario, type DemoScenarioPackage } from '@/demo/scenarios';

import { ProjectRepository } from './project';
import { ScenarioRepository } from './scenario';

let db: DemoOfflineDb;
let scenarioRepository: ScenarioRepository;

describe('ScenarioRepository', () => {
  beforeEach(() => {
    db = new DemoOfflineDb(`scenario-repository-test-${crypto.randomUUID()}`);
    scenarioRepository = new ScenarioRepository(db);
  });

  afterEach(async () => {
    await db.delete();
  });

  it('imports the default scenario on first open', async () => {
    const result = await scenarioRepository.ensureScenario(defaultDemoScenario);

    expect(result.imported).toBe(true);
    expect(result.activeScenario).toMatchObject({
      scenarioId: 'default',
      fingerprint: 'default-demo-offline-v4',
    });
    await expect(db.projects.count()).resolves.toBe(1);
    await expect(db.projectVersions.count()).resolves.toBe(1);
    await expect(db.systemUsers.count()).resolves.toBe(4);
    await expect(db.dictTypes.count()).resolves.toBe(3);
    await expect(db.posts.count()).resolves.toBe(3);
    await expect(db.sequences.get('projects')).resolves.toMatchObject({
      value: 1002,
    });
  });

  it('keeps customer-edited data when scenario identity is unchanged', async () => {
    await scenarioRepository.ensureScenario(defaultDemoScenario);

    const projectRepository = new ProjectRepository(db);
    await projectRepository.create({ projectName: '客户现场新增项目' });

    const result = await scenarioRepository.ensureScenario(defaultDemoScenario);

    expect(result.imported).toBe(false);
    await expect(db.projects.count()).resolves.toBe(2);
  });

  it('resets current data when explicitly requested', async () => {
    await scenarioRepository.ensureScenario(defaultDemoScenario);

    const projectRepository = new ProjectRepository(db);
    await projectRepository.create({ projectName: '客户现场新增项目' });

    const result = await scenarioRepository.resetScenario(defaultDemoScenario);

    expect(result.imported).toBe(true);
    await expect(db.projects.count()).resolves.toBe(1);
  });

  it('switches scenarios transactionally without mixing previous local data', async () => {
    await scenarioRepository.ensureScenario(defaultDemoScenario);

    const projectRepository = new ProjectRepository(db);
    const localProject = await projectRepository.create({ projectName: '客户现场新增项目' });
    const nextScenario: DemoScenarioPackage = {
      ...defaultDemoScenario,
      scenario: {
        ...defaultDemoScenario.scenario,
        id: 'customer-a',
        name: '客户 A 演示场景',
        version: '1.0.0',
        fingerprint: 'customer-a-v1',
      },
      project: {
        projects: [
          {
            ...defaultDemoScenario.project.projects[0],
            projectId: 3001,
            projectName: '客户 A 星载项目',
          },
        ],
        versions: [
          {
            ...defaultDemoScenario.project.versions[0],
            versionId: 4001,
            projectId: 3001,
          },
        ],
        topologies: [
          {
            ...defaultDemoScenario.project.topologies[0],
            id: 'topology-customer-a',
            projectId: 3001,
            versionId: 4001,
          },
        ],
      },
      simulation: {
        ...defaultDemoScenario.simulation,
        sessions: [
          {
            ...defaultDemoScenario.simulation.sessions[0],
            projectId: 3001,
            versionId: 4001,
          },
        ],
      },
    };

    const result = await scenarioRepository.switchScenario(nextScenario);

    expect(result).toMatchObject({
      imported: true,
      activeScenario: {
        scenarioId: 'customer-a',
        fingerprint: 'customer-a-v1',
      },
    });
    await expect(db.projects.toArray()).resolves.toEqual([
      expect.objectContaining({
        projectId: 3001,
        projectName: '客户 A 星载项目',
      }),
    ]);
    await expect(db.projects.get(1001)).resolves.toBeUndefined();
    await expect(db.projects.get(localProject.projectId)).resolves.toBeUndefined();
    await expect(db.projectVersions.toArray()).resolves.toEqual([
      expect.objectContaining({
        versionId: 4001,
        projectId: 3001,
      }),
    ]);
  });

  it('exports current data using the standard scenario package shape', async () => {
    await scenarioRepository.ensureScenario(defaultDemoScenario);

    const exported = await scenarioRepository.exportCurrentScenario();

    expect(exported).toMatchObject({
      schemaVersion: 1,
      scenario: {
        id: 'default',
        fingerprint: 'default-demo-offline-v4',
      },
      auth: {
        accounts: expect.any(Array),
      },
      system: {
        users: expect.any(Array),
        posts: expect.any(Array),
        dictTypes: expect.any(Array),
      },
      project: {
        projects: expect.any(Array),
      },
      simulation: {
        streamFrames: expect.any(Array),
      },
    });
  });

  it('rejects unsupported scenario schema versions', async () => {
    const invalidPackage = {
      ...defaultDemoScenario,
      schemaVersion: 2,
    } as unknown as DemoScenarioPackage;

    await expect(scenarioRepository.ensureScenario(invalidPackage)).rejects.toThrow(
      'Unsupported demo scenario schema version "2"'
    );
  });
});
