import { createDomcBlocker } from '../domc.js';
import type {
  DemoDomcModuleContract,
  DemoDomcRegistry,
  DemoOfflineBlockerIssue,
} from '../types.js';
import { projectSimulationAdapter } from './project-simulation/adapter.js';
import type {
  AdapterMaterialization,
  DemoAdapterCapability,
  DemoAdapterCanGenerateInput,
  DemoGeneratorAdapter,
} from './types.js';

export const registeredDemoGeneratorAdapters: DemoGeneratorAdapter[] = [projectSimulationAdapter];

function versionSatisfies(version: string, range: string): boolean {
  if (range === version || range === '*') return true;
  if (range.startsWith('^')) {
    const [major] = version.split('.');
    const [rangeMajor] = range.slice(1).split('.');
    return major === rangeMajor;
  }
  return false;
}

function requiredCapabilities(moduleContracts: DemoDomcModuleContract[]): Set<DemoAdapterCapability> {
  return new Set(
    moduleContracts.flatMap((moduleContract) => moduleContract.adapterRef?.capabilities ?? [])
  ) as Set<DemoAdapterCapability>;
}

function defaultCanGenerateInput(input: {
  domcRegistry: DemoDomcRegistry;
  moduleContracts: DemoDomcModuleContract[];
  contractFingerprint?: string;
  targetCounts?: DemoAdapterCanGenerateInput['targetCounts'];
}): DemoAdapterCanGenerateInput {
  return {
    domcRegistry: input.domcRegistry,
    moduleContracts: input.moduleContracts,
    contractFingerprint: input.contractFingerprint ?? '',
    domcFingerprint: input.domcRegistry.domcFingerprint,
    targetCounts:
      input.targetCounts ??
      {
        projects: 1,
        versionsPerProject: 1,
        sessionsPerProject: 1,
      },
  };
}

export function validateAdapterMaterializations(input: {
  domcRegistry: DemoDomcRegistry;
  adapter: DemoGeneratorAdapter;
  materializations: AdapterMaterialization[];
}): DemoOfflineBlockerIssue[] {
  const blockers: DemoOfflineBlockerIssue[] = [];
  const modulesById = new Map(input.domcRegistry.modules.map((moduleContract) => [moduleContract.moduleId, moduleContract]));

  input.materializations.forEach((materialization, index) => {
    const moduleContract = modulesById.get(materialization.moduleId);
    if (!moduleContract || !moduleContract.sourcePaths.includes(materialization.sourcePath)) {
      blockers.push(
        createDomcBlocker({
          path: `adapter.${input.adapter.adapterId}.materializations[${index}].sourcePath`,
          code: 'adapter_output_source_path_not_declared',
          actual: materialization.sourcePath,
          expected: 'Adapter materialization sourcePath declared by DOMC module contract',
          fixHint: 'Restrict adapter output to DOMC-declared sourcePaths.',
          gate: 'adapter-registry',
          missingArtifacts: ['ruoyi-fastapi-frontend/src/demo/domc/**'],
          nextActions: ['Repair DOMC adapterRef.outputSourcePaths or adapter materialization output.'],
        })
      );
    }
    if ('scenarioPackage' in (materialization as unknown as Record<string, unknown>)) {
      blockers.push(
        createDomcBlocker({
          path: `adapter.${input.adapter.adapterId}.materializations[${index}]`,
          code: 'adapter_full_package_output_rejected',
          actual: 'scenarioPackage',
          expected: 'sourcePath-level AdapterMaterialization only',
          fixHint: 'Return sourcePath materializations and let the shared assembler build DemoScenarioPackage.',
          gate: 'adapter-registry',
        })
      );
    }
  });

  return blockers;
}

export function resolveDemoGeneratorAdapters(input: {
  domcRegistry: DemoDomcRegistry;
  requestedModules: string[];
  adapters?: DemoGeneratorAdapter[];
  contractFingerprint?: string;
  targetCounts?: DemoAdapterCanGenerateInput['targetCounts'];
}): {
  selected: DemoGeneratorAdapter[];
  blockers: DemoOfflineBlockerIssue[];
} {
  const adapters = input.adapters ?? registeredDemoGeneratorAdapters;
  const blockers: DemoOfflineBlockerIssue[] = [];
  const selected = new Map<string, DemoGeneratorAdapter>();
  const modules = input.requestedModules
    .map((moduleId) => input.domcRegistry.modules.find((moduleContract) => moduleContract.moduleId === moduleId))
    .filter((moduleContract): moduleContract is DemoDomcModuleContract => Boolean(moduleContract));
  const generatableModules = modules.filter((moduleContract) => moduleContract.capability === 'generatable');
  const modulesByAdapter = new Map<string, DemoDomcModuleContract[]>();

  generatableModules.forEach((moduleContract) => {
    if (moduleContract.lifecycle !== 'active') {
      blockers.push(
        createDomcBlocker({
          path: `domc.modules[${moduleContract.moduleId}].lifecycle`,
          code: 'domc_module_lifecycle_not_active',
          actual: moduleContract.lifecycle,
          expected: 'active',
          fixHint: 'Mark the DOMC module active only after handler, UI journey, invariant, and adapter gates pass.',
          gate: 'adapter-capability',
          missingArtifacts: ['ruoyi-fastapi-frontend/src/demo/domc/**'],
          nextActions: ['Repair DOMC lifecycle or exclude this module from generation.'],
        })
      );
      return;
    }

    if (!moduleContract.adapterRef) {
      blockers.push(
        createDomcBlocker({
          path: `domc.modules[${moduleContract.moduleId}].adapterRef`,
          code: 'domc_adapter_missing',
          actual: 'missing',
          expected: 'Compatible adapterRef declared in DOMC',
          fixHint: 'Implement a MCP-side adapter and declare adapterRef in DOMC.',
          gate: 'adapter-registry',
          missingArtifacts: [`tools/demo-offline-mcp/src/adapters/${moduleContract.moduleId}/adapter.ts`],
          nextActions: ['Create and register a compatible generator adapter.'],
        })
      );
      return;
    }
    const group = modulesByAdapter.get(moduleContract.adapterRef.adapterId) ?? [];
    group.push(moduleContract);
    modulesByAdapter.set(moduleContract.adapterRef.adapterId, group);
  });

  modulesByAdapter.forEach((moduleContracts, adapterId) => {
    const capabilitySet = requiredCapabilities(moduleContracts);
    const matches = adapters
      .filter((adapter) => adapter.adapterId === adapterId)
      .filter((adapter) =>
        moduleContracts.every((moduleContract) =>
          versionSatisfies(adapter.adapterVersion, moduleContract.adapterRef!.adapterVersionRange)
        )
      )
      .filter((adapter) =>
        moduleContracts.every((moduleContract) => adapter.supportedModules.includes(moduleContract.moduleId))
      )
      .filter((adapter) => adapter.supportedDomcVersions.includes(String(input.domcRegistry.schemaVersion)))
      .filter((adapter) =>
        moduleContracts.every((moduleContract) => moduleContract.sourcePaths.every((sourcePath) => adapter.outputSourcePaths.includes(sourcePath)))
      )
      .filter((adapter) => [...capabilitySet].every((capability) => adapter.capabilities.includes(capability)))
      .sort((left, right) => right.priority - left.priority);

    if (!matches.length) {
      blockers.push(
        createDomcBlocker({
          path: `domc.modules[${moduleContracts.map((moduleContract) => moduleContract.moduleId).join('+')}].adapterRef`,
          code: 'domc_adapter_missing',
          actual: moduleContracts.map((moduleContract) => moduleContract.adapterRef),
          expected: 'Registered compatible MCP adapter for every requested DOMC module',
          fixHint: 'Register an adapter with matching id, per-module version range, supportedModules, DOMC schema version, capabilities, and output sourcePaths.',
          gate: 'adapter-registry',
          missingArtifacts: [`tools/demo-offline-mcp/src/adapters/${adapterId}/adapter.ts`],
          nextActions: ['Implement the adapter or adjust DOMC adapterRef after review.'],
        })
      );
      return;
    }

    if (matches.length > 1 && matches[0].priority === matches[1].priority) {
      blockers.push(
        createDomcBlocker({
          path: `adapters.${adapterId}`,
          code: 'domc_adapter_selection_ambiguous',
          actual: matches.map((adapter) => `${adapter.adapterId}@${adapter.adapterVersion}`),
          expected: 'Exactly one highest-priority adapter',
          fixHint: 'Give one adapter higher priority or tighten DOMC adapterVersionRange.',
          gate: 'adapter-registry',
          nextActions: ['Resolve adapter priority/version ambiguity.'],
        })
      );
      return;
    }

    const selectedAdapter = matches[0];
    const decision = selectedAdapter.canGenerate(
      defaultCanGenerateInput({
        domcRegistry: input.domcRegistry,
        moduleContracts,
        contractFingerprint: input.contractFingerprint,
        targetCounts: input.targetCounts,
      })
    );

    if (!decision.ok) {
      blockers.push(
        decision.blocker ??
          createDomcBlocker({
            path: `adapters.${adapterId}.canGenerate`,
            code: 'adapter_can_generate_rejected',
            actual: decision.reason,
            expected: 'Adapter canGenerate returns ok',
            fixHint: selectedAdapter.explainBlocker(
              defaultCanGenerateInput({
                domcRegistry: input.domcRegistry,
                moduleContracts,
                contractFingerprint: input.contractFingerprint,
                targetCounts: input.targetCounts,
              })
            ).fixHint,
            gate: 'adapter-capability',
            nextActions: ['Repair DOMC capability/lifecycle or adapter canGenerate preconditions.'],
          })
      );
      return;
    }

    selected.set(adapterId, selectedAdapter);
  });

  return {
    selected: [...selected.values()],
    blockers,
  };
}
