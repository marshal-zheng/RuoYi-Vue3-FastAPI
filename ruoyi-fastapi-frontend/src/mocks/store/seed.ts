import type { MockDataset } from '../data';
import { MOCK_REFERENCE_TIME, mockDataset } from '../data';
import { getMockDemoDb, MOCK_DEMO_SCHEMA_VERSION, type MockDemoDb } from './db';

export function stableStringify(value: unknown): string {
  if (Array.isArray(value)) {
    return `[${value.map((item) => stableStringify(item)).join(',')}]`;
  }
  if (value && typeof value === 'object') {
    const entries = Object.entries(value as Record<string, unknown>).sort(([left], [right]) =>
      left.localeCompare(right)
    );
    return `{${entries
      .map(([key, item]) => `${JSON.stringify(key)}:${stableStringify(item)}`)
      .join(',')}}`;
  }
  return JSON.stringify(value);
}

export function fingerprintDataset(dataset: MockDataset): string {
  const text = stableStringify(dataset);
  let hash = 0x811c9dc5;
  for (let index = 0; index < text.length; index += 1) {
    hash ^= text.charCodeAt(index);
    hash = Math.imul(hash, 0x01000193);
  }
  return `fnv1a-${(hash >>> 0).toString(16).padStart(8, '0')}`;
}

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
    const { resetMockDemoDb } = await import('./reset');
    await resetMockDemoDb(db, dataset);
    return;
  }

  if (schemaVersion.value !== MOCK_DEMO_SCHEMA_VERSION) {
    const { resetMockDemoDb } = await import('./reset');
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
