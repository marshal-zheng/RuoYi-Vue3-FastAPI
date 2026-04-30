import crypto from 'node:crypto';

import { Dexie } from 'dexie';
import { IDBKeyRange, indexedDB } from 'fake-indexeddb';

import { createIssue } from '../errors.js';
import type {
  CompiledDemoScenarioPackage,
  DemoOfflineContractManifest,
  ImportDryRunSummary,
  ToolEnvelope,
  ValidationIssue,
} from '../types.js';
import { errorEnvelope, okEnvelope } from '../types.js';

Dexie.dependencies.indexedDB = indexedDB;
Dexie.dependencies.IDBKeyRange = IDBKeyRange;

function getPath(value: unknown, pathName: string): unknown[] {
  const resolved = pathName.split('.').reduce<unknown>((current, key) => {
    if (!current || typeof current !== 'object') return undefined;
    return (current as Record<string, unknown>)[key];
  }, value);

  return Array.isArray(resolved) ? resolved : [];
}

function dexieStores(contract: DemoOfflineContractManifest): Record<string, string> {
  return Object.fromEntries(
    contract.indexedDbMapping.tables.map((table) => [
      table.table,
      [`&${table.primaryKey}`, ...table.indexes].join(', '),
    ])
  );
}

export async function dryRunImportRuntimePackage(
  contract: DemoOfflineContractManifest,
  scenarioPackage: CompiledDemoScenarioPackage
): Promise<ToolEnvelope<ImportDryRunSummary>> {
  const startedAt = Date.now();
  const dbName = `demo-offline-dry-run-${scenarioPackage.scenario.id}-${crypto.randomUUID()}`;
  const db = new Dexie(dbName);
  const inserted: Record<string, number> = {};

  db.version(contract.indexedDbMapping.dbVersion).stores(dexieStores(contract));

  try {
    await db.transaction('rw', contract.indexedDbMapping.tables.map((table) => db.table(table.table)), async () => {
      for (const table of contract.indexedDbMapping.tables) {
        const records = getPath(scenarioPackage, table.sourcePath);
        await db.table(table.table).bulkPut(records);
        inserted[table.table] = records.length;
      }
    });

    return okEnvelope('Runtime package import dry-run succeeded.', {
      dbName,
      inserted,
      activeScenario: {
        scenarioId: scenarioPackage.scenario.id,
        fingerprint: scenarioPackage.scenario.fingerprint,
      },
      durationMs: Date.now() - startedAt,
    });
  } catch (error) {
    const issue: ValidationIssue = createIssue({
      path: 'indexeddb',
      code: 'runtime_import_dry_run_failed',
      severity: 'error',
      actual: error instanceof Error ? error.message : String(error),
      expected: 'Successful Dexie import in fake-indexeddb',
      fixHint: 'Fix schema/invariant errors or primary-key collisions before activating the package.',
      autoRepairable: false,
    });
    return errorEnvelope('Runtime package import dry-run failed.', [issue]);
  } finally {
    db.close();
    await Dexie.delete(dbName).catch(() => undefined);
  }
}
