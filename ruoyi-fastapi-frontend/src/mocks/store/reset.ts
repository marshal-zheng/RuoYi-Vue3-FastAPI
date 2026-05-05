import type { MockDataset } from '../data';
import { MOCK_REFERENCE_TIME, mockDataset } from '../data';
import {
  MOCK_DEMO_SCHEMA_VERSION,
  getMockDemoDb,
  type MockDemoDb,
  type MockMetaRecord,
} from './db';
import { fingerprintDataset } from './seed';

interface ResetMockDemoDbOptions {
  resetAt?: string;
  seededAt?: string;
}

export async function resetMockDemoDb(
  db: MockDemoDb = getMockDemoDb(),
  dataset: MockDataset = mockDataset,
  options: ResetMockDemoDbOptions = {}
): Promise<void> {
  const resetAt = options.resetAt ?? MOCK_REFERENCE_TIME;
  const seededAt = options.seededAt ?? resetAt;
  const datasetFingerprint = fingerprintDataset(dataset);

  const metaRecords: MockMetaRecord[] = [
    { key: 'schemaVersion', value: MOCK_DEMO_SCHEMA_VERSION, updatedAt: resetAt },
    { key: 'datasetVersion', value: dataset.version, updatedAt: resetAt },
    { key: 'datasetFingerprint', value: datasetFingerprint, updatedAt: resetAt },
    { key: 'seededAt', value: seededAt, updatedAt: resetAt },
    { key: 'lastResetAt', value: resetAt, updatedAt: resetAt },
  ];

  await db.transaction(
    'rw',
    [
      db.meta,
      db.accounts,
      db.authSessions,
      db.roles,
      db.menus,
      db.dicts,
      db.departments,
      db.projects,
      db.projectVersions,
      db.topologies,
      db.simulationSessions,
      db.simulationMessages,
      db.simulationEvents,
      db.simulationFrames,
      db.sequences,
    ],
    async () => {
      await Promise.all([
        db.meta.clear(),
        db.accounts.clear(),
        db.authSessions.clear(),
        db.roles.clear(),
        db.menus.clear(),
        db.dicts.clear(),
        db.departments.clear(),
        db.projects.clear(),
        db.projectVersions.clear(),
        db.topologies.clear(),
        db.simulationSessions.clear(),
        db.simulationMessages.clear(),
        db.simulationEvents.clear(),
        db.simulationFrames.clear(),
        db.sequences.clear(),
      ]);

      await Promise.all([
        db.accounts.bulkPut(dataset.auth.accounts),
        db.roles.bulkPut(dataset.auth.roles),
        db.menus.bulkPut(dataset.system.menus),
        db.dicts.bulkPut(dataset.system.dicts),
        db.departments.bulkPut(dataset.system.departments),
        db.projects.bulkPut(dataset.project.projects),
        db.projectVersions.bulkPut(dataset.project.versions),
        db.topologies.bulkPut(dataset.project.topologies),
        db.simulationSessions.bulkPut(dataset.simulation.sessions),
        db.simulationMessages.bulkPut(dataset.simulation.messages),
        db.simulationEvents.bulkPut(dataset.simulation.events),
        db.simulationFrames.bulkPut(dataset.simulation.frames),
        db.sequences.bulkPut([
          {
            name: 'projectId',
            value: Math.max(...dataset.project.projects.map((item) => item.projectId)) + 1,
          },
          {
            name: 'versionId',
            value: Math.max(...dataset.project.versions.map((item) => item.versionId)) + 1,
          },
        ]),
        db.meta.bulkPut(metaRecords),
      ]);
    }
  );
}
