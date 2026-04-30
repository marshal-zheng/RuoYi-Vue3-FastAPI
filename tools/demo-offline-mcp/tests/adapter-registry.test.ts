import { describe, expect, it } from 'vitest';

import {
  resolveDemoGeneratorAdapters,
  validateAdapterMaterializations,
} from '../src/adapters/registry.js';
import { projectSimulationAdapter } from '../src/adapters/project-simulation/adapter.js';
import type { DemoDomcModuleContract, DemoDomcRegistry } from '../src/types.js';

function moduleContract(input: {
  moduleId: string;
  capability?: 'generatable' | 'copyOnly';
  lifecycle?: DemoDomcModuleContract['lifecycle'];
  adapterId?: string;
  adapterVersionRange?: string;
  sourcePaths: string[];
}): DemoDomcModuleContract {
  return {
    moduleId: input.moduleId,
    moduleVersion: '1.0.0',
    lifecycle: input.lifecycle ?? 'active',
    capability: input.capability ?? 'generatable',
    owner: 'unit-test',
    sourcePaths: input.sourcePaths,
    indexedDbTables: [],
    handlerCoverage: [],
    uiJourneys: [],
    entities: [],
    stateMachines: [],
    invariants: [],
    diversityRules: [],
    materializationPolicy: input.sourcePaths.map((sourcePath, index) => ({
      sourcePath,
      order: (index + 1) * 100000,
      materializationReason: input.capability === 'copyOnly' ? 'copied-default' : 'semantic-generated',
      minItems: 0,
    })),
    ...(input.capability === 'copyOnly'
      ? {
          copyOnly: {
            source: 'demo-contract/default-scenario.json',
            sourcePaths: input.sourcePaths,
            reason: 'unit-test',
            minItems: {},
          },
        }
      : {
          adapterRef: {
            adapterId: input.adapterId ?? 'project-simulation',
            adapterVersionRange: input.adapterVersionRange ?? '^1.0.0',
            capabilities: ['business-blueprint', 'sourcePath-materialization', 'semantic-anchor-bindings', 'deterministic-seed'],
            outputSourcePaths: input.sourcePaths,
            priority: 100,
          },
        }),
    migrationSources: ['unit-test'],
  };
}

function registry(modules: DemoDomcModuleContract[]): DemoDomcRegistry {
  return {
    schemaVersion: 1,
    registryVersion: 'unit-test',
    generatedAt: '2026-04-29T00:00:00.000Z',
    domcFingerprint: 'a'.repeat(64),
    contractVersion: 1,
    platformLayer: 'DOMC',
    modules,
    qualityGates: [],
    migrationSources: ['unit-test'],
  };
}

describe('DOMC adapter registry', () => {
  it('resolves the project-simulation adapter by DOMC adapterRef and version', () => {
    const result = resolveDemoGeneratorAdapters({
      domcRegistry: registry([
        moduleContract({ moduleId: 'project', sourcePaths: ['project.projects', 'project.versions', 'project.topologies'] }),
        moduleContract({
          moduleId: 'simulation',
          sourcePaths: [
            'simulation.sessions',
            'simulation.messages',
            'simulation.bandwidth',
            'simulation.alarms',
            'simulation.faults',
            'simulation.events',
            'simulation.streamFrames',
          ],
        }),
      ]),
      requestedModules: ['project', 'simulation'],
    });

    expect(result.blockers).toEqual([]);
    expect(result.selected).toEqual([expect.objectContaining({ adapterId: 'project-simulation' })]);
  });

  it('allows copyOnly modules without selecting a generator adapter', () => {
    const result = resolveDemoGeneratorAdapters({
      domcRegistry: registry([
        moduleContract({ moduleId: 'auth', capability: 'copyOnly', sourcePaths: ['auth.accounts'] }),
      ]),
      requestedModules: ['auth'],
    });

    expect(result).toMatchObject({ selected: [], blockers: [] });
  });

  it('returns blocker when a generatable module has no compatible adapter', () => {
    const result = resolveDemoGeneratorAdapters({
      domcRegistry: registry([
        moduleContract({ moduleId: 'customer', adapterId: 'customer-adapter', sourcePaths: ['customer.customers'] }),
      ]),
      requestedModules: ['customer'],
      adapters: [projectSimulationAdapter],
    });

    expect(result.blockers).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          code: 'domc_adapter_missing',
          gate: 'adapter-registry',
          missingArtifacts: expect.arrayContaining(['tools/demo-offline-mcp/src/adapters/customer-adapter/adapter.ts']),
        }),
      ])
    );
  });

  it('blocks inactive DOMC modules before adapter selection', () => {
    const result = resolveDemoGeneratorAdapters({
      domcRegistry: registry([
        moduleContract({
          moduleId: 'project',
          lifecycle: 'deprecated',
          sourcePaths: ['project.projects', 'project.versions', 'project.topologies'],
        }),
      ]),
      requestedModules: ['project'],
      adapters: [projectSimulationAdapter],
    });

    expect(result).toMatchObject({
      selected: [],
      blockers: [
        expect.objectContaining({
          code: 'domc_module_lifecycle_not_active',
          gate: 'adapter-capability',
        }),
      ],
    });
  });

  it('checks every module adapterRef version range and canGenerate decision', () => {
    const incompatibleVersion = resolveDemoGeneratorAdapters({
      domcRegistry: registry([
        moduleContract({ moduleId: 'project', adapterVersionRange: '^1.0.0', sourcePaths: ['project.projects'] }),
        moduleContract({
          moduleId: 'simulation',
          adapterVersionRange: '^2.0.0',
          sourcePaths: ['simulation.sessions'],
        }),
      ]),
      requestedModules: ['project', 'simulation'],
      adapters: [projectSimulationAdapter],
    });
    const canGenerateRejected = resolveDemoGeneratorAdapters({
      domcRegistry: registry([
        moduleContract({
          moduleId: 'simulation',
          sourcePaths: ['simulation.sessions'],
        }),
      ]),
      requestedModules: ['simulation'],
      adapters: [projectSimulationAdapter],
    });

    expect(incompatibleVersion.blockers).toEqual(
      expect.arrayContaining([expect.objectContaining({ code: 'domc_adapter_missing' })])
    );
    expect(canGenerateRejected.blockers).toEqual(
      expect.arrayContaining([expect.objectContaining({ code: 'adapter_dependency_module_missing' })])
    );
  });

  it('blocks ambiguous adapter selection and undeclared materialization sourcePaths', () => {
    const duplicate = { ...projectSimulationAdapter };
    const domcRegistry = registry([
      moduleContract({ moduleId: 'project', sourcePaths: ['project.projects', 'project.versions', 'project.topologies'] }),
      moduleContract({
        moduleId: 'simulation',
        sourcePaths: [
          'simulation.sessions',
          'simulation.messages',
          'simulation.bandwidth',
          'simulation.alarms',
          'simulation.faults',
          'simulation.events',
          'simulation.streamFrames',
        ],
      }),
    ]);
    const ambiguous = resolveDemoGeneratorAdapters({
      domcRegistry,
      requestedModules: ['project', 'simulation'],
      adapters: [projectSimulationAdapter, duplicate],
    });
    const materializationIssues = validateAdapterMaterializations({
      domcRegistry,
      adapter: projectSimulationAdapter,
      materializations: [
        {
          moduleId: 'project',
          sourcePath: 'project.unknown',
          order: 1,
          materializationReason: 'semantic-generated',
          records: [],
          domcModuleVersion: '1.0.0',
          adapterId: 'project-simulation',
          adapterVersion: '1.0.0',
        },
      ],
    });

    expect(ambiguous.blockers).toEqual(
      expect.arrayContaining([expect.objectContaining({ code: 'domc_adapter_selection_ambiguous' })])
    );
    expect(materializationIssues).toEqual(
      expect.arrayContaining([expect.objectContaining({ code: 'adapter_output_source_path_not_declared' })])
    );
  });

  it('validates adapter materialization order and DOMC materialization reason', () => {
    const projectModule = moduleContract({
      moduleId: 'project',
      sourcePaths: ['project.projects'],
    });
    const validation = projectSimulationAdapter.validate({
      domcRegistry: registry([projectModule]),
      moduleContracts: [projectModule],
      contractFingerprint: 'a'.repeat(64),
      domcFingerprint: 'b'.repeat(64),
      targetCounts: {
        projects: 1,
        versionsPerProject: 1,
        sessionsPerProject: 1,
      },
      compileResult: {
        adapterId: 'project-simulation',
        adapterVersion: '1.0.0',
        moduleIds: ['project'],
        materializations: [
          {
            moduleId: 'project',
            sourcePath: 'project.projects',
            order: 42,
            materializationReason: 'runtime-required',
            records: [],
            domcModuleVersion: '1.0.0',
            adapterId: 'project-simulation',
            adapterVersion: '1.0.0',
          },
        ],
        semanticBindings: [],
        summary: {},
      },
    });

    expect(validation.issues).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ code: 'adapter_materialization_order_drift' }),
        expect.objectContaining({ code: 'adapter_materialization_reason_drift' }),
      ])
    );
  });
});
