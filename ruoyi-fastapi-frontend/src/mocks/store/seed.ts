import type { MockDataset } from '../data';
import { MOCK_REFERENCE_TIME, mockDataset } from '../data';
import { getMockDemoDb, MOCK_DEMO_SCHEMA_VERSION, type MockDemoDb } from './db';

import { fingerprintDataset } from './fingerprint';
import { resetMockDemoDb } from './reset';

export { fingerprintDataset, stableStringify } from './fingerprint';

async function recordPendingDatasetUpgrade(
  db: MockDemoDb,
  dataset: MockDataset,
  currentFingerprint: string
): Promise<void> {
  await db.meta.bulkPut([
    {
      key: 'pendingDatasetVersion',
      value: dataset.version,
      updatedAt: MOCK_REFERENCE_TIME,
    },
    {
      key: 'pendingDatasetFingerprint',
      value: currentFingerprint,
      updatedAt: MOCK_REFERENCE_TIME,
    },
    {
      key: 'datasetUpgradePolicy',
      value: 'preserve-user-edits-until-explicit-reset',
      updatedAt: MOCK_REFERENCE_TIME,
    },
  ]);
}

async function clearPendingDatasetUpgrade(db: MockDemoDb): Promise<void> {
  await db.meta.bulkDelete([
    'pendingDatasetVersion',
    'pendingDatasetFingerprint',
    'datasetUpgradePolicy',
  ]);
}

export async function ensureMockDemoDbSeeded(
  db: MockDemoDb = getMockDemoDb(),
  dataset: MockDataset = mockDataset
): Promise<void> {
  const [schemaVersion, datasetVersion, datasetFingerprint] = await Promise.all([
    db.meta.get('schemaVersion'),
    db.meta.get('datasetVersion'),
    db.meta.get('datasetFingerprint'),
  ]);

  if (!schemaVersion || !datasetVersion || !datasetFingerprint) {
    await resetMockDemoDb(db, dataset);
    return;
  }

  if (schemaVersion.value !== MOCK_DEMO_SCHEMA_VERSION) {
    await resetMockDemoDb(db, dataset);
    return;
  }

  const currentFingerprint = fingerprintDataset(dataset);
  if (datasetVersion.value !== dataset.version || datasetFingerprint.value !== currentFingerprint) {
    await recordPendingDatasetUpgrade(db, dataset, currentFingerprint);
    return;
  }

  await clearPendingDatasetUpgrade(db);
}
