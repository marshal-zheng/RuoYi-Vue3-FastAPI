import fs from 'node:fs/promises';
import path from 'node:path';

import { createIssue, ToolError } from '../errors.js';
import { sha256CanonicalJson } from '../hash.js';
import {
  assertDemoDomcRegistry,
  validateDomcRegistryCompatibility,
} from '../domc.js';
import type { DemoDomcRegistry, DemoOfflineContractManifest } from '../types.js';
import { assertOfflineStaticReadPath, type OfflineStaticTargetPaths } from './paths.js';

export interface OfflineStaticContractBundle {
  contract: DemoOfflineContractManifest;
  domcRegistry: DemoDomcRegistry;
  domcRegistrySchema: unknown;
  scenarioSchema: unknown;
  defaultScenario: import('../types.js').CompiledDemoScenarioPackage;
}

async function readJsonFile<T>(filePath: string): Promise<T> {
  const source = await fs.readFile(filePath, 'utf8').catch(() => undefined);

  if (!source) {
    throw new ToolError(
      createIssue({
        path: filePath,
        code: 'offline_static_contract_file_missing',
        severity: 'error',
        actual: filePath,
        expected: 'Existing JSON contract file',
        fixHint: 'Rebuild or repair the offline package so demo-contract/** exists.',
        autoRepairable: false,
      })
    );
  }

  try {
    return JSON.parse(source) as T;
  } catch (error) {
    throw new ToolError(
      createIssue({
        path: filePath,
        code: 'offline_static_contract_json_invalid',
        severity: 'error',
        actual: error instanceof Error ? error.message : String(error),
        expected: 'Valid JSON',
        fixHint: 'Rebuild the offline package or restore the contract file from a known-good package.',
        autoRepairable: false,
      })
    );
  }
}

export function createContractFingerprintInput(contract: DemoOfflineContractManifest, scenarioSchema: unknown): unknown {
  const { contractFingerprint: _contractFingerprint, generatedAt: _generatedAt, ...stableContract } = contract;
  return {
    contract: stableContract,
    scenarioSchema,
  };
}

export function computeContractFingerprint(contract: DemoOfflineContractManifest, scenarioSchema: unknown): string {
  return sha256CanonicalJson(createContractFingerprintInput(contract, scenarioSchema));
}

export async function readOfflineStaticContract(
  paths: OfflineStaticTargetPaths
): Promise<OfflineStaticContractBundle> {
  const contractPath = await assertOfflineStaticReadPath(paths, path.join(paths.demoContractRoot, 'contract.json'));
  const domcRegistryPath = await assertOfflineStaticReadPath(paths, path.join(paths.demoContractRoot, 'domc.registry.json'));
  const domcRegistrySchemaPath = await assertOfflineStaticReadPath(paths, path.join(paths.demoContractRoot, 'domc.registry.schema.json'));
  const schemaPath = await assertOfflineStaticReadPath(paths, path.join(paths.demoContractRoot, 'scenario.schema.json'));
  const defaultPath = await assertOfflineStaticReadPath(paths, path.join(paths.demoContractRoot, 'default-scenario.json'));
  const contract = await readJsonFile<DemoOfflineContractManifest>(contractPath);
  const domcRegistry = assertDemoDomcRegistry(await readJsonFile<unknown>(domcRegistryPath));
  const domcRegistrySchema = await readJsonFile<unknown>(domcRegistrySchemaPath);
  const scenarioSchema = await readJsonFile<unknown>(schemaPath);
  const defaultScenario = await readJsonFile<import('../types.js').CompiledDemoScenarioPackage>(defaultPath);
  const actualFingerprint = computeContractFingerprint(contract, scenarioSchema);

  if (contract.contractFingerprint !== actualFingerprint) {
    throw new ToolError(
      createIssue({
        path: 'demo-contract/contract.json.contractFingerprint',
        code: 'contract_fingerprint_mismatch',
        severity: 'error',
        actual: contract.contractFingerprint,
        expected: actualFingerprint,
        fixHint: 'Rebuild demo-offline so contract.json matches scenario.schema.json and adapter versions.',
        autoRepairable: false,
      })
    );
  }

  const domcIssues = validateDomcRegistryCompatibility({ registry: domcRegistry, contract });
  const domcErrors = domcIssues.filter((issue) => issue.severity === 'error');
  if (domcErrors.length) {
    throw new ToolError(domcErrors[0]);
  }

  return { contract, domcRegistry, domcRegistrySchema, scenarioSchema, defaultScenario };
}
