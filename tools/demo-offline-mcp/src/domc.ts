import { createIssue } from './errors.js';
import { sha256CanonicalJson } from './hash.js';
import type {
  DemoDomcModuleContract,
  DemoDomcRegistry,
  DemoIndexedDbTableMapping,
  DemoOfflineBlockerIssue,
  DemoOfflineContractManifest,
  ValidationIssue,
} from './types.js';

function isPlainObject(value: unknown): value is Record<string, unknown> {
  return Object.prototype.toString.call(value) === '[object Object]';
}

export function createDomcRegistryFingerprintInput(registry: DemoDomcRegistry): unknown {
  const { domcFingerprint: _domcFingerprint, generatedAt: _generatedAt, ...stableRegistry } = registry;
  return stableRegistry;
}

export function computeDomcRegistryFingerprint(registry: DemoDomcRegistry): string {
  return sha256CanonicalJson(createDomcRegistryFingerprintInput(registry));
}

export function computeDomcModuleFingerprint(moduleContract: DemoDomcModuleContract): string {
  return sha256CanonicalJson(moduleContract);
}

export function computeDomcModuleFingerprints(registry: DemoDomcRegistry): Record<string, string> {
  return Object.fromEntries(
    registry.modules.map((moduleContract) => [
      moduleContract.moduleId,
      computeDomcModuleFingerprint(moduleContract),
    ])
  );
}

export function createDomcBlocker(input: {
  path: string;
  code: string;
  actual?: unknown;
  expected: string;
  fixHint: string;
  gate: DemoOfflineBlockerIssue['gate'];
  missingArtifacts?: string[];
  nextActions?: string[];
}): DemoOfflineBlockerIssue {
  return {
    ...createIssue({
      path: input.path,
      code: input.code,
      severity: 'error',
      actual: input.actual,
      expected: input.expected,
      fixHint: input.fixHint,
      autoRepairable: false,
    }),
    gate: input.gate,
    missingArtifacts: input.missingArtifacts ?? [],
    nextActions: input.nextActions ?? [],
  };
}

function modulePath(moduleContract: DemoDomcModuleContract): string {
  return `domc.modules[${moduleContract.moduleId}]`;
}

function validateModuleContract(input: {
  moduleContract: DemoDomcModuleContract;
  contract: DemoOfflineContractManifest;
  tableBySourcePath: Map<string, DemoIndexedDbTableMapping>;
}): ValidationIssue[] {
  const issues: ValidationIssue[] = [];
  const { moduleContract, tableBySourcePath } = input;
  const path = modulePath(moduleContract);
  const sourcePaths = new Set(moduleContract.sourcePaths);

  if (!moduleContract.moduleId || !moduleContract.sourcePaths.length) {
    issues.push(
      createDomcBlocker({
        path,
        code: 'domc_module_contract_invalid',
        actual: moduleContract,
        expected: 'Module contract with stable moduleId and sourcePaths',
        fixHint: 'Regenerate demo-contract/domc.registry.json from the frontend DOMC source.',
        gate: 'domc-schema',
        missingArtifacts: ['ruoyi-fastapi-frontend/src/demo/domc/**'],
        nextActions: ['Repair the DOMC module contract, then rebuild demo-offline.'],
      })
    );
  }

  moduleContract.sourcePaths.forEach((sourcePath) => {
    if (!tableBySourcePath.has(sourcePath)) {
      issues.push(
        createDomcBlocker({
          path: `${path}.sourcePaths`,
          code: 'domc_source_path_table_mapping_missing',
          actual: sourcePath,
          expected: 'Every DOMC sourcePath exists in contract.indexedDbMapping.tables',
          fixHint: 'Add IndexedDB mapping, scenario schema, and repository import support before declaring this sourcePath.',
          gate: 'handler-mapping-coverage',
          missingArtifacts: ['DEMO_INDEXED_DB_MAPPING', 'scenario.schema.json'],
          nextActions: ['Update the runtime contract and rebuild demo-offline.'],
        })
      );
    }
  });

  moduleContract.entities.forEach((entity, entityIndex) => {
    const mapping = tableBySourcePath.get(entity.sourcePath);
    if (!sourcePaths.has(entity.sourcePath)) {
      issues.push(
        createDomcBlocker({
          path: `${path}.entities[${entityIndex}].sourcePath`,
          code: 'domc_entity_source_path_not_declared',
          actual: entity.sourcePath,
          expected: 'Entity sourcePath listed in module.sourcePaths',
          fixHint: 'Sync DOMC entity source paths with the module sourcePath list.',
          gate: 'domc-registry-integrity',
        })
      );
    }
    if (!mapping || mapping.table !== entity.indexedDbTable || mapping.primaryKey !== entity.primaryKey) {
      issues.push(
        createDomcBlocker({
          path: `${path}.entities[${entityIndex}]`,
          code: 'domc_entity_table_drift',
          actual: entity,
          expected: 'Entity indexedDbTable and primaryKey match contract mapping',
          fixHint: 'Regenerate the DOMC entity from the current contract mapping.',
          gate: 'contract-drift',
          missingArtifacts: ['demo-contract/contract.json', 'demo-contract/domc.registry.json'],
          nextActions: ['Rebuild the offline shell so DOMC and contract mapping match.'],
        })
      );
    }
    const fields = new Set(entity.fields.map((field) => field.name));
    if (!fields.has(entity.primaryKey)) {
      issues.push(
        createDomcBlocker({
          path: `${path}.entities[${entityIndex}].primaryKey`,
          code: 'domc_entity_primary_key_field_missing',
          actual: entity.primaryKey,
          expected: 'Primary key represented as an entity field',
          fixHint: 'Add the primary key field contract before marking the module generatable.',
          gate: 'domc-schema',
        })
      );
    }
  });

  moduleContract.uiJourneys.forEach((journey, journeyIndex) => {
    [journey.primarySourcePath, ...journey.requiredSupportSourcePaths].forEach((sourcePath) => {
      if (!sourcePaths.has(sourcePath)) {
        issues.push(
          createDomcBlocker({
            path: `${path}.uiJourneys[${journeyIndex}]`,
            code: 'domc_ui_journey_source_path_missing',
            actual: sourcePath,
            expected: 'Journey source paths declared by the same module DOMC',
            fixHint: 'Add the sourcePath to DOMC or adjust the UI journey support record list.',
            gate: 'ui-journey-coverage',
            missingArtifacts: ['DOMC uiJourneys'],
            nextActions: ['Repair DOMC UI journey coverage and rebuild demo-offline.'],
          })
        );
      }
    });
  });

  if (moduleContract.capability === 'generatable') {
    if (!moduleContract.adapterRef) {
      issues.push(
        createDomcBlocker({
          path: `${path}.adapterRef`,
          code: 'domc_adapter_ref_missing',
          actual: 'missing',
          expected: 'Generatable module declares adapterRef',
          fixHint: 'Implement a MCP-side adapter and declare adapterRef in DOMC.',
          gate: 'adapter-registry',
          missingArtifacts: [`tools/demo-offline-mcp/src/adapters/${moduleContract.moduleId}/adapter.ts`],
          nextActions: ['Create and register a compatible generator adapter.'],
        })
      );
    }
  }

  if (moduleContract.capability === 'copyOnly' && !moduleContract.copyOnly) {
    issues.push(
      createDomcBlocker({
        path: `${path}.copyOnly`,
        code: 'domc_copy_only_policy_missing',
        actual: 'missing',
        expected: 'copyOnly policy with default scenario sourcePaths',
        fixHint: 'Declare copyOnly policy before allowing the module to be copied.',
        gate: 'module-blocker',
      })
    );
  }

  return issues;
}

export function assertDemoDomcRegistry(value: unknown): DemoDomcRegistry {
  if (!isPlainObject(value)) {
    throw new Error('DOMC registry must be a JSON object.');
  }
  const registry = value as Partial<DemoDomcRegistry>;
  if (registry.schemaVersion !== 1) throw new Error('DOMC registry schemaVersion must be 1.');
  if (registry.platformLayer !== 'DOMC') throw new Error('DOMC registry platformLayer must be DOMC.');
  if (!Array.isArray(registry.modules) || !registry.modules.length) {
    throw new Error('DOMC registry modules must be a non-empty array.');
  }
  if (typeof registry.domcFingerprint !== 'string' || !/^[a-f0-9]{64}$/.test(registry.domcFingerprint)) {
    throw new Error('DOMC registry fingerprint must be a SHA-256 hex string.');
  }
  return registry as DemoDomcRegistry;
}

export function validateDomcRegistryCompatibility(input: {
  registry: DemoDomcRegistry;
  contract: DemoOfflineContractManifest;
}): ValidationIssue[] {
  const issues: ValidationIssue[] = [];
  const actualDomcFingerprint = computeDomcRegistryFingerprint(input.registry);
  const tableBySourcePath = new Map(input.contract.indexedDbMapping.tables.map((table) => [table.sourcePath, table]));
  const moduleFingerprints = computeDomcModuleFingerprints(input.registry);

  if (input.registry.domcFingerprint !== actualDomcFingerprint) {
    issues.push(
      createDomcBlocker({
        path: 'demo-contract/domc.registry.json.domcFingerprint',
        code: 'domc_fingerprint_mismatch',
        actual: input.registry.domcFingerprint,
        expected: actualDomcFingerprint,
        fixHint: 'Rebuild the offline shell so DOMC fingerprint matches canonical registry JSON.',
        gate: 'domc-fingerprint',
        missingArtifacts: ['demo-contract/domc.registry.json'],
        nextActions: ['Run build:demo-offline and retry the MCP action.'],
      })
    );
  }
  if (input.contract.domcRegistryFingerprint !== input.registry.domcFingerprint) {
    issues.push(
      createDomcBlocker({
        path: 'demo-contract/contract.json.domcRegistryFingerprint',
        code: 'contract_domc_fingerprint_mismatch',
        actual: input.contract.domcRegistryFingerprint,
        expected: input.registry.domcFingerprint,
        fixHint: 'Rebuild demo-offline so contract.json and domc.registry.json are emitted together.',
        gate: 'contract-drift',
        missingArtifacts: ['demo-contract/contract.json', 'demo-contract/domc.registry.json'],
        nextActions: ['Regenerate the offline contract artifacts.'],
      })
    );
  }

  for (const [moduleId, fingerprint] of Object.entries(moduleFingerprints)) {
    if (input.contract.moduleContractFingerprints[moduleId] !== fingerprint) {
      issues.push(
        createDomcBlocker({
          path: `demo-contract/contract.json.moduleContractFingerprints.${moduleId}`,
          code: 'domc_module_fingerprint_mismatch',
          actual: input.contract.moduleContractFingerprints[moduleId],
          expected: fingerprint,
          fixHint: 'Rebuild demo-offline so module fingerprints match DOMC module contracts.',
          gate: 'contract-drift',
          missingArtifacts: ['demo-contract/contract.json', 'demo-contract/domc.registry.json'],
          nextActions: ['Regenerate contract artifacts before publishing or activating releases.'],
        })
      );
    }
  }

  const moduleIds = new Set<string>();
  input.registry.modules.forEach((moduleContract) => {
    if (moduleIds.has(moduleContract.moduleId)) {
      issues.push(
        createDomcBlocker({
          path: `domc.modules[${moduleContract.moduleId}]`,
          code: 'domc_module_duplicate',
          actual: moduleContract.moduleId,
          expected: 'Unique DOMC module ids',
          fixHint: 'Keep a single module contract per module id.',
          gate: 'domc-registry-integrity',
        })
      );
    }
    moduleIds.add(moduleContract.moduleId);
    issues.push(...validateModuleContract({ moduleContract, contract: input.contract, tableBySourcePath }));
  });

  return issues;
}

export function getDomcModule(registry: DemoDomcRegistry, moduleId: string): DemoDomcModuleContract | undefined {
  return registry.modules.find((moduleContract) => moduleContract.moduleId === moduleId);
}
