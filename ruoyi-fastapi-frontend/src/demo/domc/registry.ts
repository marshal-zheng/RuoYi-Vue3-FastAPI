import { DEMO_OFFLINE_CONTRACT_VERSION } from '../scenarios/contract';
import { computeDomcRegistryFingerprint, computeDomcModuleFingerprints } from './fingerprint';
import { authDomcModule } from './modules/auth.domc';
import { projectDomcModule } from './modules/project.domc';
import { simulationDomcModule } from './modules/simulation.domc';
import { systemDomcModule } from './modules/system.domc';
import type {
  DemoDomcAdapterReferenceSummary,
  DemoDomcQualityGate,
  DemoDomcRegistry,
  DemoDomcRegistryDraft,
} from './types';
import { validateDemoDomcRegistry } from './validate';

export const DEMO_DOMC_REGISTRY_VERSION = 'demo-domc-registry-1.0.0';
export const DEMO_DOMC_REGISTRY_PATH = 'demo-contract/domc.registry.json' as const;
export const DEMO_DOMC_REGISTRY_SCHEMA_PATH = 'demo-contract/domc.registry.schema.json' as const;

export const DEMO_DOMC_QUALITY_GATES = [
  {
    gate: 'domc-schema',
    severity: 'error',
    description: 'DOMC JSON uses the local registry schema and contains no remote refs.',
  },
  {
    gate: 'domc-registry-integrity',
    severity: 'error',
    description: 'Module ids, sourcePaths, ownership, and copyOnly policies are internally consistent.',
  },
  {
    gate: 'domc-fingerprint',
    severity: 'error',
    description: 'Registry fingerprint is recomputable from canonical DOMC JSON excluding generatedAt.',
  },
  {
    gate: 'adapter-registry',
    severity: 'error',
    description: 'Generatable modules have exactly one compatible MCP-side adapter.',
  },
  {
    gate: 'adapter-capability',
    severity: 'error',
    description: 'Adapter capabilities and output sourcePaths satisfy DOMC requirements.',
  },
  {
    gate: 'module-blocker',
    severity: 'error',
    description: 'Missing DOMC, mapping, UI journey, handler, or adapter produces a strict blocker.',
  },
  {
    gate: 'ui-journey-coverage',
    severity: 'error',
    description: 'UI journeys reference declared sourcePaths and support the minimum demo chain.',
  },
  {
    gate: 'handler-mapping-coverage',
    severity: 'error',
    description: 'DOMC handler coverage and IndexedDB sourcePath mappings match runtime contract facts.',
  },
  {
    gate: 'contract-drift',
    severity: 'error',
    description: 'DOMC, scenario schema, IndexedDB mapping, handlers, and import dry-run must not drift.',
  },
  {
    gate: 'domc-provenance',
    severity: 'error',
    description: 'v2 release provenance records DOMC fingerprint and adapter audit information.',
  },
  {
    gate: 'adapter-regression',
    severity: 'error',
    description: 'Project/simulation adapter output remains deterministic and validates sourcePath boundaries.',
  },
] as const satisfies readonly DemoDomcQualityGate[];

export function createDemoDomcRegistryDraft(
  generatedAt = new Date().toISOString()
): DemoDomcRegistryDraft {
  return {
    schemaVersion: 1,
    registryVersion: DEMO_DOMC_REGISTRY_VERSION,
    generatedAt,
    contractVersion: DEMO_OFFLINE_CONTRACT_VERSION,
    platformLayer: 'DOMC',
    modules: [authDomcModule, systemDomcModule, projectDomcModule, simulationDomcModule],
    qualityGates: DEMO_DOMC_QUALITY_GATES,
    migrationSources: [
      'DemoOfflineContractManifest',
      'DEMO_MODULE_CONTRACTS',
      'DEMO_INDEXED_DB_MAPPING',
      'DEMO_HANDLER_COVERAGE',
      'DEMO_INVARIANTS',
      'Spec A semantic anchor bindings',
      'Spec B v2 release provenance',
    ],
  };
}

export async function createDemoDomcRegistry(
  generatedAt = new Date().toISOString()
): Promise<DemoDomcRegistry> {
  const draft = createDemoDomcRegistryDraft(generatedAt);
  const registry = {
    ...draft,
    domcFingerprint: await computeDomcRegistryFingerprint(draft),
  };
  const validation = await validateDemoDomcRegistry(registry);
  if (!validation.valid) {
    throw new Error(
      `DOMC registry validation failed: ${validation.issues
        .filter((issue) => issue.severity === 'error')
        .map((issue) => `${issue.code}@${issue.path}`)
        .join(', ')}`
    );
  }
  return registry;
}

export async function createDemoDomcModuleContractFingerprints(
  registry: DemoDomcRegistry | DemoDomcRegistryDraft
): Promise<Record<string, string>> {
  return computeDomcModuleFingerprints(registry);
}

export function createDemoDomcAdapterReferences(
  registry: DemoDomcRegistry | DemoDomcRegistryDraft
): DemoDomcAdapterReferenceSummary[] {
  return registry.modules.map((moduleContract) => ({
    moduleId: moduleContract.moduleId as DemoDomcAdapterReferenceSummary['moduleId'],
    adapterId:
      moduleContract.adapterRef?.adapterId ??
      (moduleContract.capability === 'copyOnly' ? 'copy-only-default-scenario' : 'unsupported'),
    adapterVersionRange:
      moduleContract.adapterRef?.adapterVersionRange ??
      (moduleContract.capability === 'copyOnly' ? 'default-scenario' : 'none'),
    capability: moduleContract.capability,
    outputSourcePaths: moduleContract.adapterRef?.outputSourcePaths ?? moduleContract.sourcePaths,
  }));
}
