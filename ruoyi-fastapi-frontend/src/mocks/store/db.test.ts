import 'fake-indexeddb/auto';

import { afterEach, describe, expect, it } from 'vitest';

import { mockDataset, type MockDataset } from '../data';
import { MOCK_DEMO_DB_NAME, MOCK_DEMO_SCHEMA_VERSION, MockDemoDb, replaceMockDemoDb } from './db';
import { resetMockDemoDb } from './reset';
import { ensureMockDemoDbSeeded, fingerprintDataset } from './seed';

describe('MockDemoDb seed/reset', () => {
  let db: MockDemoDb | undefined;

  afterEach(async () => {
    replaceMockDemoDb(undefined);
    if (db) {
      await db.delete();
      db = undefined;
    }
  });

  function createTestDb() {
    db = new MockDemoDb(`${MOCK_DEMO_DB_NAME}-test`);
    replaceMockDemoDb(db);
    return db;
  }

  function getInitialProject() {
    const [initialProject] = mockDataset.project.projects;
    if (!initialProject) {
      throw new Error('Mock dataset requires at least one project for store tests.');
    }
    return initialProject;
  }

  it('seeds the independent mock dataset store with metadata', async () => {
    const testDb = createTestDb();

    await ensureMockDemoDbSeeded(testDb);

    await expect(testDb.projects.count()).resolves.toBe(mockDataset.project.projects.length);
    await expect(testDb.projectVersions.count()).resolves.toBe(mockDataset.project.versions.length);
    await expect(testDb.topologies.count()).resolves.toBe(mockDataset.project.topologies.length);
    await expect(testDb.simulationFrames.count()).resolves.toBe(
      mockDataset.simulation.frames.length
    );

    await expect(testDb.meta.get('datasetVersion')).resolves.toMatchObject({
      value: mockDataset.version,
    });
    await expect(testDb.meta.get('datasetFingerprint')).resolves.toMatchObject({
      value: fingerprintDataset(mockDataset),
    });
    await expect(testDb.meta.get('schemaVersion')).resolves.toMatchObject({
      value: MOCK_DEMO_SCHEMA_VERSION,
    });
    await expect(testDb.meta.get('seededAt')).resolves.toBeTruthy();
    await expect(testDb.meta.get('lastResetAt')).resolves.toBeTruthy();
  });

  it('keeps persisted edits until an explicit reset restores the typed dataset', async () => {
    const testDb = createTestDb();
    const initialProject = getInitialProject();

    await ensureMockDemoDbSeeded(testDb);
    await testDb.projects.update(initialProject.projectId, {
      projectName: '本地演示修改',
    });
    await ensureMockDemoDbSeeded(testDb);

    await expect(testDb.projects.get(initialProject.projectId)).resolves.toMatchObject({
      projectName: '本地演示修改',
    });

    await resetMockDemoDb(testDb);

    await expect(testDb.projects.get(initialProject.projectId)).resolves.toMatchObject({
      projectName: initialProject.projectName,
    });
  });

  it('resets incompatible schema metadata to the current typed dataset', async () => {
    const testDb = createTestDb();
    const initialProject = getInitialProject();

    await ensureMockDemoDbSeeded(testDb);
    await testDb.projects.update(initialProject.projectId, {
      projectName: '旧 schema 修改',
    });
    await testDb.meta.put({
      key: 'schemaVersion',
      value: MOCK_DEMO_SCHEMA_VERSION - 1,
      updatedAt: mockDataset.referenceTime,
    });

    await ensureMockDemoDbSeeded(testDb);

    await expect(testDb.meta.get('schemaVersion')).resolves.toMatchObject({
      value: MOCK_DEMO_SCHEMA_VERSION,
    });
    await expect(testDb.projects.get(initialProject.projectId)).resolves.toMatchObject({
      projectName: initialProject.projectName,
    });
  });

  it('records compatible dataset upgrades without overwriting local demo edits', async () => {
    const testDb = createTestDb();
    const initialProject = getInitialProject();
    const upgradedDataset: MockDataset = {
      ...mockDataset,
      version: 'mock-dataset-v2',
      project: {
        ...mockDataset.project,
        projects: [
          {
            ...initialProject,
            projectName: '上游数据集新名称',
          },
          ...mockDataset.project.projects.slice(1),
        ],
      },
    };

    await ensureMockDemoDbSeeded(testDb);
    await testDb.projects.update(initialProject.projectId, {
      projectName: '本地演示保留',
    });

    await ensureMockDemoDbSeeded(testDb, upgradedDataset);

    await expect(testDb.projects.get(initialProject.projectId)).resolves.toMatchObject({
      projectName: '本地演示保留',
    });
    await expect(testDb.meta.get('datasetVersion')).resolves.toMatchObject({
      value: mockDataset.version,
    });
    await expect(testDb.meta.get('pendingDatasetVersion')).resolves.toMatchObject({
      value: upgradedDataset.version,
    });
    await expect(testDb.meta.get('pendingDatasetFingerprint')).resolves.toMatchObject({
      value: fingerprintDataset(upgradedDataset),
    });
  });
});
