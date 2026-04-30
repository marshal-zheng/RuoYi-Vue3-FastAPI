import { compileScenarioPackage } from '../../compiler.js';
import { createDomcBlocker } from '../../domc.js';
import type { DemoDomcEntityContract, DemoDomcModuleContract, ValidationIssue } from '../../types.js';
import type {
  AdapterMaterialization,
  DemoAdapterCanGenerateInput,
  DemoAdapterCompileInput,
  DemoAdapterCompileResult,
  DemoAdapterValidateInput,
  DemoGeneratorAdapter,
} from '../types.js';

const ADAPTER_ID = 'project-simulation';
const ADAPTER_VERSION = '1.0.0';
const SUPPORTED_MODULES = ['project', 'simulation'];
const OUTPUT_SOURCE_PATHS = [
  'project.projects',
  'project.versions',
  'project.topologies',
  'simulation.sessions',
  'simulation.messages',
  'simulation.bandwidth',
  'simulation.alarms',
  'simulation.faults',
  'simulation.events',
  'simulation.streamFrames',
];

function getPath(value: unknown, pathName: string): unknown {
  return pathName.split('.').reduce<unknown>((current, key) => {
    if (!current || typeof current !== 'object') return undefined;
    return (current as Record<string, unknown>)[key];
  }, value);
}

function modulesForAdapter(input: DemoAdapterCanGenerateInput): DemoDomcModuleContract[] {
  return input.moduleContracts.filter((moduleContract) => SUPPORTED_MODULES.includes(moduleContract.moduleId));
}

function sourcePathFromRecordPath(recordPath: string): string {
  return recordPath.replace(/\[\d+\]/g, '');
}

function sourcePathOrder(moduleContract: DemoDomcModuleContract, sourcePath: string): number {
  return (
    moduleContract.materializationPolicy.find((policy) => policy.sourcePath === sourcePath)?.order ??
    (OUTPUT_SOURCE_PATHS.indexOf(sourcePath) + 1) * 100000
  );
}

function findEntity(
  moduleContracts: DemoDomcModuleContract[],
  sourcePath: string
): DemoDomcEntityContract | undefined {
  return moduleContracts.flatMap((moduleContract) => moduleContract.entities).find((entity) => entity.sourcePath === sourcePath);
}

function validateRecords(input: {
  moduleContracts: DemoDomcModuleContract[];
  materialization: AdapterMaterialization;
}): ValidationIssue[] {
  const issues: ValidationIssue[] = [];
  const entity = findEntity(input.moduleContracts, input.materialization.sourcePath);

  if (!entity) {
    return [
      createDomcBlocker({
        path: `adapter.${ADAPTER_ID}.${input.materialization.sourcePath}`,
        code: 'adapter_domc_entity_missing',
        actual: input.materialization.sourcePath,
        expected: 'DOMC entity contract for materialized sourcePath',
        fixHint: 'Declare an entity contract before allowing adapter output.',
        gate: 'adapter-capability',
      }),
    ];
  }

  if (input.materialization.records.length < entity.minItems) {
    issues.push(
      createDomcBlocker({
        path: `adapter.${ADAPTER_ID}.${input.materialization.sourcePath}`,
        code: 'adapter_min_items_not_met',
        actual: input.materialization.records.length,
        expected: `At least ${entity.minItems} records`,
        fixHint: 'Increase targetCounts or repair the adapter materialization logic.',
        gate: 'adapter-regression',
      })
    );
  }

  input.materialization.records.forEach((record, recordIndex) => {
    if (record[entity.primaryKey] === undefined || record[entity.primaryKey] === null) {
      issues.push(
        createDomcBlocker({
          path: `adapter.${ADAPTER_ID}.${input.materialization.sourcePath}[${recordIndex}].${entity.primaryKey}`,
          code: 'adapter_primary_key_missing',
          actual: record,
          expected: `Record primary key ${entity.primaryKey}`,
          fixHint: 'Repair adapter output so every record has its DOMC primary key.',
          gate: 'adapter-regression',
        })
      );
    }

    entity.fields
      .filter((field) => field.required)
      .forEach((field) => {
        if (record[field.name] !== undefined && record[field.name] !== null) return;
        issues.push(
          createDomcBlocker({
            path: `adapter.${ADAPTER_ID}.${input.materialization.sourcePath}[${recordIndex}].${field.name}`,
            code: 'adapter_required_field_missing',
            actual: record[field.name],
            expected: `Required field ${field.name}`,
            fixHint: 'Repair adapter output or DOMC required field metadata.',
            gate: 'adapter-regression',
          })
        );
      });
  });

  return issues;
}

function recordsByEntity(moduleContracts: DemoDomcModuleContract[], materializations: AdapterMaterialization[]) {
  return new Map(
    moduleContracts.flatMap((moduleContract) =>
      moduleContract.entities.map((entity) => {
        const materialization = materializations.find((item) => item.sourcePath === entity.sourcePath);
        return [entity.entity, { entity, records: materialization?.records ?? [] }] as const;
      })
    )
  );
}

function referenceValues(value: unknown): unknown[] {
  if (Array.isArray(value)) return value;
  if (value === undefined || value === null) return [];
  return [value];
}

function validateReferences(input: {
  moduleContracts: DemoDomcModuleContract[];
  materializations: AdapterMaterialization[];
}): ValidationIssue[] {
  const issues: ValidationIssue[] = [];
  const entities = recordsByEntity(input.moduleContracts, input.materializations);

  input.moduleContracts.flatMap((moduleContract) => moduleContract.entities).forEach((entity) => {
    const source = entities.get(entity.entity);
    if (!source) return;

    entity.references.forEach((reference) => {
      const target = entities.get(reference.targetEntity);
      if (!target) {
        issues.push(
          createDomcBlocker({
            path: `adapter.${ADAPTER_ID}.${entity.sourcePath}.${reference.field}`,
            code: 'adapter_reference_target_entity_missing',
            actual: reference.targetEntity,
            expected: 'Referenced DOMC target entity materialized by this adapter run',
            fixHint: 'Include the referenced module/sourcePath in the adapter plan or repair DOMC references.',
            gate: 'adapter-regression',
          })
        );
        return;
      }

      const targetIds = new Set(target.records.map((record) => record[reference.targetField]));
      source.records.forEach((record, recordIndex) => {
        const values = referenceValues(record[reference.field]);
        if (!values.length && !reference.required) return;
        if (!values.length && reference.required) {
          issues.push(
            createDomcBlocker({
              path: `adapter.${ADAPTER_ID}.${entity.sourcePath}[${recordIndex}].${reference.field}`,
              code: 'adapter_required_reference_missing',
              actual: record[reference.field],
              expected: `Reference to ${reference.targetEntity}.${reference.targetField}`,
              fixHint: 'Repair adapter output so required DOMC references are present.',
              gate: 'adapter-regression',
            })
          );
          return;
        }

        values.forEach((value) => {
          if (targetIds.has(value)) return;
          issues.push(
            createDomcBlocker({
              path: `adapter.${ADAPTER_ID}.${entity.sourcePath}[${recordIndex}].${reference.field}`,
              code: 'adapter_reference_target_missing',
              actual: value,
              expected: `${reference.targetEntity}.${reference.targetField}`,
              fixHint: 'Repair adapter output so cross-sourcePath references resolve within materializations.',
              gate: 'adapter-regression',
            })
          );
        });
      });
    });
  });

  return issues;
}

function validateMaterializationPolicies(input: {
  moduleContracts: DemoDomcModuleContract[];
  materializations: AdapterMaterialization[];
}): ValidationIssue[] {
  const issues: ValidationIssue[] = [];
  const materializationBySourcePath = new Map(
    input.materializations.map((materialization) => [materialization.sourcePath, materialization])
  );

  input.moduleContracts.forEach((moduleContract) => {
    moduleContract.materializationPolicy.forEach((policy) => {
      const materialization = materializationBySourcePath.get(policy.sourcePath);
      if (!materialization) {
        issues.push(
          createDomcBlocker({
            path: `adapter.${ADAPTER_ID}.materializations.${policy.sourcePath}`,
            code: 'adapter_materialization_missing',
            actual: 'missing',
            expected: 'Materialization for every DOMC materializationPolicy sourcePath',
            fixHint: 'Emit sourcePath materialization for the requested DOMC module.',
            gate: 'adapter-regression',
          })
        );
        return;
      }

      if (materialization.order !== policy.order) {
        issues.push(
          createDomcBlocker({
            path: `adapter.${ADAPTER_ID}.materializations.${policy.sourcePath}.order`,
            code: 'adapter_materialization_order_drift',
            actual: materialization.order,
            expected: String(policy.order),
            fixHint: 'Use DOMC materializationPolicy.order as the adapter output order.',
            gate: 'adapter-regression',
          })
        );
      }

      if (materialization.materializationReason !== policy.materializationReason) {
        issues.push(
          createDomcBlocker({
            path: `adapter.${ADAPTER_ID}.materializations.${policy.sourcePath}.materializationReason`,
            code: 'adapter_materialization_reason_drift',
            actual: materialization.materializationReason,
            expected: policy.materializationReason,
            fixHint: 'Use DOMC materializationPolicy.materializationReason for descriptor provenance.',
            gate: 'adapter-regression',
          })
        );
      }
    });
  });

  return issues;
}

function validateSemanticAnchors(input: DemoAdapterValidateInput): ValidationIssue[] {
  const issues: ValidationIssue[] = [];
  const bindingsBySourcePath = new Map<string, typeof input.compileResult.semanticBindings>();

  input.compileResult.semanticBindings.forEach((binding) => {
    const sourcePath = sourcePathFromRecordPath(binding.recordPath);
    const existing = bindingsBySourcePath.get(sourcePath) ?? [];
    bindingsBySourcePath.set(sourcePath, [...existing, binding]);
  });

  modulesForAdapter(input).forEach((moduleContract) => {
    moduleContract.semanticAnchors?.forEach((rule) => {
      const bindings = bindingsBySourcePath.get(rule.sourcePath) ?? [];
      const materialization = input.compileResult.materializations.find(
        (item) => item.sourcePath === rule.sourcePath
      );
      if (!bindings.length && (materialization?.records.length ?? 0) > 0) {
        issues.push(
          createDomcBlocker({
            path: `adapter.${ADAPTER_ID}.semanticBindings.${rule.sourcePath}`,
            code: 'adapter_semantic_anchor_binding_missing',
            actual: 0,
            expected: `Bindings for ${rule.sourcePath}`,
            fixHint: 'Emit SemanticAnchorBinding entries for DOMC semantic anchor rules.',
            gate: 'adapter-regression',
          })
        );
        return;
      }

      bindings.forEach((binding, bindingIndex) => {
        const anchorTypes = new Set(binding.anchors.map((anchor) => anchor.type));
        const missingRequired = rule.requiredAnchorTypes.filter((type) => !anchorTypes.has(type));
        if (anchorTypes.size < rule.minAnchorTypes || missingRequired.length) {
          issues.push(
            createDomcBlocker({
              path: `adapter.${ADAPTER_ID}.semanticBindings.${rule.sourcePath}[${bindingIndex}].anchors`,
              code: 'adapter_semantic_anchor_rule_not_met',
              actual: [...anchorTypes],
              expected: `At least ${rule.minAnchorTypes} anchor types including ${rule.requiredAnchorTypes.join(', ')}`,
              fixHint: 'Regenerate semantic anchor bindings from the Business Blueprint.',
              gate: 'adapter-regression',
            })
          );
        }
      });
    });
  });

  return issues;
}

function validateDiversityRules(input: {
  moduleContracts: DemoDomcModuleContract[];
  materializations: AdapterMaterialization[];
}): ValidationIssue[] {
  const issues: ValidationIssue[] = [];
  const materializationBySourcePath = new Map(
    input.materializations.map((materialization) => [materialization.sourcePath, materialization])
  );

  input.moduleContracts.forEach((moduleContract) => {
    moduleContract.diversityRules.forEach((rule) => {
      const records = materializationBySourcePath.get(rule.primarySourcePath)?.records ?? [];
      if (records.length <= 1) return;

      const signatures = records.map((record) =>
        rule.fields.map((fieldName) => String(record[fieldName] ?? '')).join('\u0001')
      );
      const duplicateCount = signatures.length - new Set(signatures).size;
      const duplicateRatio = duplicateCount / signatures.length;
      if (duplicateRatio > rule.duplicateThreshold) {
        const issue = createDomcBlocker({
          path: `adapter.${ADAPTER_ID}.diversityRules.${rule.ruleId}`,
          code: 'adapter_diversity_duplicate_threshold_exceeded',
          actual: duplicateRatio,
          expected: `<= ${rule.duplicateThreshold}`,
          fixHint: 'Increase semantic variation across DOMC diversity fields before writing records.',
          gate: 'adapter-regression',
        });
        issue.severity = rule.severity;
        issues.push(issue);
      }
    });
  });

  return issues;
}

export const projectSimulationAdapter: DemoGeneratorAdapter = {
  adapterId: ADAPTER_ID,
  adapterVersion: ADAPTER_VERSION,
  priority: 100,
  supportedModules: SUPPORTED_MODULES,
  supportedDomcVersions: ['1'],
  capabilities: ['business-blueprint', 'sourcePath-materialization', 'semantic-anchor-bindings', 'deterministic-seed'],
  inputKinds: ['business-blueprint', 'default-scenario', 'domc-registry'],
  outputSourcePaths: OUTPUT_SOURCE_PATHS,

  canGenerate(input) {
    const modules = modulesForAdapter(input);
    const unsupported = input.moduleContracts.filter(
      (moduleContract) => !SUPPORTED_MODULES.includes(moduleContract.moduleId)
    );
    if (unsupported.length) {
      return {
        ok: false,
        reason: 'Unsupported DOMC module contract.',
        blocker: this.explainBlocker(input),
      };
    }
    const requestsSimulation = modules.some((moduleContract) => moduleContract.moduleId === 'simulation');
    const requestsProject = modules.some((moduleContract) => moduleContract.moduleId === 'project');
    if (requestsSimulation && !requestsProject) {
      return {
        ok: false,
        reason: 'Simulation generation requires project sourcePath materializations for references.',
        blocker: createDomcBlocker({
          path: 'domc.modules[simulation].references',
          code: 'adapter_dependency_module_missing',
          actual: 'simulation without project',
          expected: 'project and simulation generated together',
          fixHint: 'Include project in the generation plan when simulation is requested.',
          gate: 'adapter-capability',
          missingArtifacts: ['demo-contract/domc.registry.json'],
          nextActions: ['Regenerate the plan with project and simulation together.'],
        }),
      };
    }
    const incompatible = modules.find(
      (moduleContract) =>
        moduleContract.capability !== 'generatable' ||
        moduleContract.lifecycle !== 'active' ||
        moduleContract.adapterRef?.adapterId !== ADAPTER_ID
    );
    if (incompatible) {
      return {
        ok: false,
        reason: `Module ${incompatible.moduleId} cannot be generated by ${ADAPTER_ID}.`,
        blocker: createDomcBlocker({
          path: `domc.modules[${incompatible.moduleId}]`,
          code: 'adapter_capability_mismatch',
          actual: {
            lifecycle: incompatible.lifecycle,
            capability: incompatible.capability,
            adapterRef: incompatible.adapterRef,
          },
          expected: `active generatable module with adapterRef ${ADAPTER_ID}`,
          fixHint: 'Adjust DOMC lifecycle/capability or implement a compatible adapter.',
          gate: 'adapter-capability',
          missingArtifacts: ['ruoyi-fastapi-frontend/src/demo/domc/**'],
          nextActions: ['Repair DOMC adapter capability before generating runtime data.'],
        }),
      };
    }
    return {
      ok: true,
      reason: 'project/simulation DOMC modules are active and adapter-compatible.',
    };
  },

  plan(input) {
    const modules = modulesForAdapter(input);
    return {
      adapterId: ADAPTER_ID,
      adapterVersion: ADAPTER_VERSION,
      moduleIds: modules.map((moduleContract) => moduleContract.moduleId),
      outputSourcePaths: modules.flatMap((moduleContract) => moduleContract.adapterRef?.outputSourcePaths ?? moduleContract.sourcePaths),
      evidence: [
        'demo-contract/domc.registry.json',
        'tools/demo-offline-mcp/src/adapters/project-simulation/adapter.ts',
        'Spec A Business Blueprint',
      ],
    };
  },

  async compile(input: DemoAdapterCompileInput): Promise<DemoAdapterCompileResult> {
    const modules = modulesForAdapter(input);
    const compiled = await compileScenarioPackage({
      plan: input.plan,
      draft: input.draft,
      defaultScenarioPackage: input.defaultScenarioPackage,
    });

    if (!compiled.ok || !compiled.data) {
      throw new Error(`Project/simulation adapter failed to compile sourcePath materializations: ${compiled.summary}`);
    }

    const scenarioPackage = compiled.data.scenarioPackage;
    const materializations = modules.flatMap((moduleContract) =>
      moduleContract.sourcePaths.map((sourcePath) => {
        const records = getPath(scenarioPackage, sourcePath);
        if (!Array.isArray(records)) {
          throw new Error(`Adapter sourcePath ${sourcePath} did not compile to an array.`);
        }
        return {
          moduleId: moduleContract.moduleId,
          sourcePath,
          order: sourcePathOrder(moduleContract, sourcePath),
          materializationReason: 'semantic-generated' as const,
          records: records as Array<Record<string, unknown>>,
          domcModuleVersion: moduleContract.moduleVersion,
          adapterId: ADAPTER_ID,
          adapterVersion: ADAPTER_VERSION,
        };
      })
    );

    return {
      adapterId: ADAPTER_ID,
      adapterVersion: ADAPTER_VERSION,
      moduleIds: modules.map((moduleContract) => moduleContract.moduleId),
      materializations,
      semanticBindings: input.bindings,
      summary: {
        projectCount: scenarioPackage.project.projects.length,
        versionCount: scenarioPackage.project.versions.length,
        sessionCount: scenarioPackage.simulation.sessions.length,
        outputSourcePaths: materializations.map((materialization) => materialization.sourcePath),
      },
    };
  },

  validate(input: DemoAdapterValidateInput) {
    const modules = modulesForAdapter(input);
    const issues = [
      ...validateMaterializationPolicies({
        moduleContracts: modules,
        materializations: input.compileResult.materializations,
      }),
      ...input.compileResult.materializations.flatMap((materialization) =>
        validateRecords({ moduleContracts: modules, materialization })
      ),
      ...validateReferences({
        moduleContracts: modules,
        materializations: input.compileResult.materializations,
      }),
      ...validateSemanticAnchors(input),
      ...validateDiversityRules({
        moduleContracts: modules,
        materializations: input.compileResult.materializations,
      }),
    ];
    return {
      valid: !issues.some((issue) => issue.severity === 'error'),
      issues,
    };
  },

  explainBlocker(input) {
    return createDomcBlocker({
      path: 'domc.modules[project+simulation]',
      code: 'project_simulation_adapter_unavailable',
      actual: input.moduleContracts.map((moduleContract) => ({
        moduleId: moduleContract.moduleId,
        lifecycle: moduleContract.lifecycle,
        capability: moduleContract.capability,
        adapterRef: moduleContract.adapterRef,
      })),
      expected: 'Active project and simulation DOMC modules with project-simulation adapterRef',
      fixHint: 'Repair DOMC registry or register project-simulation adapter before generation.',
      gate: 'adapter-registry',
      missingArtifacts: ['tools/demo-offline-mcp/src/adapters/project-simulation/adapter.ts'],
      nextActions: ['Verify DOMC registry and adapter registration.'],
    });
  },
};
