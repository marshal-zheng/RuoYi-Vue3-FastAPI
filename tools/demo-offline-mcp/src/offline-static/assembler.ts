import { createDomcBlocker } from '../domc.js';
import { computeScenarioFingerprint } from '../hash.js';
import type { AdapterMaterialization } from '../adapters/types.js';
import type {
  CompiledDemoScenarioPackage,
  DemoDomcModuleContract,
  DemoDomcRegistry,
  RuntimeScenarioMeta,
  ValidationIssue,
} from '../types.js';

function clone<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T;
}

function getPath(value: unknown, pathName: string): unknown {
  return pathName.split('.').reduce<unknown>((current, key) => {
    if (!current || typeof current !== 'object') return undefined;
    return (current as Record<string, unknown>)[key];
  }, value);
}

function setPath(target: Record<string, unknown>, pathName: string, value: unknown): void {
  const segments = pathName.split('.');
  let current = target;
  segments.slice(0, -1).forEach((segment) => {
    if (!current[segment] || typeof current[segment] !== 'object') {
      current[segment] = {};
    }
    current = current[segment] as Record<string, unknown>;
  });
  current[segments[segments.length - 1]] = value;
}

function moduleFromSourcePath(sourcePath: string): string {
  return sourcePath.split('.')[0];
}

function entityForSourcePath(registry: DemoDomcRegistry, sourcePath: string) {
  return registry.modules.flatMap((moduleContract) => moduleContract.entities).find((entity) => entity.sourcePath === sourcePath);
}

function referenceValues(value: unknown): unknown[] {
  if (Array.isArray(value)) return value;
  if (value === undefined || value === null) return [];
  return [value];
}

function validateMaterializedRecords(input: {
  registry: DemoDomcRegistry;
  sourcePath: string;
  records: Array<Record<string, unknown>>;
}): ValidationIssue[] {
  const entity = entityForSourcePath(input.registry, input.sourcePath);
  if (!entity) {
    return [
      createDomcBlocker({
        path: `assembler.${input.sourcePath}`,
        code: 'assembler_domc_entity_missing',
        actual: input.sourcePath,
        expected: 'DOMC entity for materialized sourcePath',
        fixHint: 'Declare entity metadata before materializing this sourcePath.',
        gate: 'domc-registry-integrity',
      }),
    ];
  }

  const issues: ValidationIssue[] = [];
  if (input.records.length < entity.minItems) {
    issues.push(
      createDomcBlocker({
        path: `assembler.${input.sourcePath}`,
        code: 'assembler_min_items_not_met',
        actual: input.records.length,
        expected: `At least ${entity.minItems} records`,
        fixHint: 'Regenerate adapter output or adjust DOMC minItems after review.',
        gate: 'adapter-regression',
      })
    );
  }

  input.records.forEach((record, index) => {
    if (record[entity.primaryKey] === undefined || record[entity.primaryKey] === null) {
      issues.push(
        createDomcBlocker({
          path: `assembler.${input.sourcePath}[${index}].${entity.primaryKey}`,
          code: 'assembler_primary_key_missing',
          actual: record,
          expected: `Primary key ${entity.primaryKey}`,
          fixHint: 'Repair adapter materialization primary keys.',
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
            path: `assembler.${input.sourcePath}[${index}].${field.name}`,
            code: 'assembler_required_field_missing',
            actual: record[field.name],
            expected: `Required field ${field.name}`,
            fixHint: 'Repair adapter materialization required fields.',
            gate: 'adapter-regression',
          })
        );
      });
  });

  return issues;
}

function validateGeneratedMaterializationPolicies(input: {
  moduleContracts: DemoDomcModuleContract[];
  materializations: AdapterMaterialization[];
}): ValidationIssue[] {
  const materializationBySourcePath = new Map(
    input.materializations.map((materialization) => [materialization.sourcePath, materialization])
  );
  const issues: ValidationIssue[] = [];

  input.moduleContracts.forEach((moduleContract) => {
    moduleContract.materializationPolicy.forEach((policy) => {
      const materialization = materializationBySourcePath.get(policy.sourcePath);
      if (!materialization) return;

      if (materialization.order !== policy.order) {
        issues.push(
          createDomcBlocker({
            path: `assembler.materializations.${policy.sourcePath}.order`,
            code: 'assembler_materialization_order_drift',
            actual: materialization.order,
            expected: String(policy.order),
            fixHint: 'Adapter materialization order must match DOMC materializationPolicy.order.',
            gate: 'contract-drift',
          })
        );
      }

      if (materialization.materializationReason !== policy.materializationReason) {
        issues.push(
          createDomcBlocker({
            path: `assembler.materializations.${policy.sourcePath}.materializationReason`,
            code: 'assembler_materialization_reason_drift',
            actual: materialization.materializationReason,
            expected: policy.materializationReason,
            fixHint: 'Adapter materialization reason must match DOMC materializationPolicy.',
            gate: 'domc-provenance',
          })
        );
      }
    });
  });

  return issues;
}

function validateGeneratedReferences(input: {
  moduleContracts: DemoDomcModuleContract[];
  materializations: AdapterMaterialization[];
}): ValidationIssue[] {
  const issues: ValidationIssue[] = [];
  const recordsBySourcePath = new Map(
    input.materializations.map((materialization) => [materialization.sourcePath, materialization.records])
  );
  const entitiesByName = new Map(
    input.moduleContracts.flatMap((moduleContract) =>
      moduleContract.entities.map((entity) => [entity.entity, entity] as const)
    )
  );

  input.moduleContracts.flatMap((moduleContract) => moduleContract.entities).forEach((entity) => {
    const records = recordsBySourcePath.get(entity.sourcePath) ?? [];

    entity.references.forEach((reference) => {
      const targetEntity = entitiesByName.get(reference.targetEntity);
      const targetRecords = targetEntity
        ? recordsBySourcePath.get(targetEntity.sourcePath) ?? []
        : undefined;

      if (!targetEntity || !targetRecords) {
        issues.push(
          createDomcBlocker({
            path: `assembler.references.${entity.sourcePath}.${reference.field}`,
            code: 'assembler_reference_target_entity_missing',
            actual: reference.targetEntity,
            expected: 'Referenced DOMC entity included in generated materializations',
            fixHint: 'Include the dependent sourcePath in the generation plan or repair DOMC references.',
            gate: 'contract-drift',
          })
        );
        return;
      }

      const targetIds = new Set(targetRecords.map((record) => record[reference.targetField]));
      records.forEach((record, recordIndex) => {
        const values = referenceValues(record[reference.field]);
        if (!values.length && !reference.required) return;
        if (!values.length && reference.required) {
          issues.push(
            createDomcBlocker({
              path: `assembler.${entity.sourcePath}[${recordIndex}].${reference.field}`,
              code: 'assembler_required_reference_missing',
              actual: record[reference.field],
              expected: `Reference to ${reference.targetEntity}.${reference.targetField}`,
              fixHint: 'Repair adapter output before assembling the runtime package.',
              gate: 'adapter-regression',
            })
          );
          return;
        }

        values.forEach((value) => {
          if (targetIds.has(value)) return;
          issues.push(
            createDomcBlocker({
              path: `assembler.${entity.sourcePath}[${recordIndex}].${reference.field}`,
              code: 'assembler_reference_target_missing',
              actual: value,
              expected: `${reference.targetEntity}.${reference.targetField}`,
              fixHint: 'Repair adapter output so generated sourcePath references resolve.',
              gate: 'adapter-regression',
            })
          );
        });
      });
    });
  });

  return issues;
}

export interface AssembleDemoScenarioPackageInput {
  scenario: CompiledDemoScenarioPackage['scenario'];
  defaultScenarioPackage: CompiledDemoScenarioPackage;
  domcRegistry: DemoDomcRegistry;
  generatedMaterializations: AdapterMaterialization[];
  copyOnlyModules: string[];
}

export interface AssembleDemoScenarioPackageResult {
  scenarioPackage?: CompiledDemoScenarioPackage;
  issues: ValidationIssue[];
}

export function assembleDemoScenarioPackage(
  input: AssembleDemoScenarioPackageInput
): AssembleDemoScenarioPackageResult {
  const issues: ValidationIssue[] = [];
  const packageDraft = clone(input.defaultScenarioPackage) as unknown as Record<string, unknown>;
  const moduleById = new Map(input.domcRegistry.modules.map((moduleContract) => [moduleContract.moduleId, moduleContract]));
  const declaredSourcePaths = new Set(input.domcRegistry.modules.flatMap((moduleContract) => moduleContract.sourcePaths));
  const generatedModuleContracts = input.domcRegistry.modules.filter(
    (moduleContract) =>
      moduleContract.capability === 'generatable' &&
      input.generatedMaterializations.some((materialization) => materialization.moduleId === moduleContract.moduleId)
  );

  setPath(packageDraft, 'scenario', { ...input.scenario, fingerprint: '' });

  issues.push(
    ...validateGeneratedMaterializationPolicies({
      moduleContracts: generatedModuleContracts,
      materializations: input.generatedMaterializations,
    })
  );

  input.copyOnlyModules.forEach((moduleId) => {
    const moduleContract = moduleById.get(moduleId);
    if (!moduleContract || moduleContract.capability !== 'copyOnly' || !moduleContract.copyOnly) {
      issues.push(
        createDomcBlocker({
          path: `assembler.copyOnlyModules[${moduleId}]`,
          code: 'assembler_copy_only_policy_missing',
          actual: moduleContract,
          expected: 'copyOnly DOMC module with copyOnly policy',
          fixHint: 'Declare copyOnly policy or remove the module from copyOnly assembly.',
          gate: 'module-blocker',
        })
      );
      return;
    }

    moduleContract.copyOnly.sourcePaths.forEach((sourcePath) => {
      const copiedRecords = getPath(input.defaultScenarioPackage, sourcePath);
      if (!Array.isArray(copiedRecords)) {
        issues.push(
          createDomcBlocker({
            path: `assembler.${sourcePath}`,
            code: 'assembler_copy_only_source_missing',
            actual: typeof copiedRecords,
            expected: 'Array records in default scenario',
            fixHint: 'Repair default-scenario.json before copying this module.',
            gate: 'module-blocker',
          })
        );
        return;
      }
      issues.push(
        ...validateMaterializedRecords({
          registry: input.domcRegistry,
          sourcePath,
          records: copiedRecords as Array<Record<string, unknown>>,
        })
      );
    });
  });

  input.generatedMaterializations
    .slice()
    .sort((left, right) => left.order - right.order)
    .forEach((materialization) => {
      if (!declaredSourcePaths.has(materialization.sourcePath)) {
        issues.push(
          createDomcBlocker({
            path: `assembler.materializations.${materialization.sourcePath}`,
            code: 'assembler_source_path_not_declared',
            actual: materialization.sourcePath,
            expected: 'DOMC-declared sourcePath',
            fixHint: 'Do not write sourcePaths that are absent from DOMC.',
            gate: 'adapter-registry',
          })
        );
        return;
      }
      const moduleContract = moduleById.get(moduleFromSourcePath(materialization.sourcePath));
      if (!moduleContract || moduleContract.capability !== 'generatable') {
        issues.push(
          createDomcBlocker({
            path: `assembler.materializations.${materialization.sourcePath}`,
            code: 'assembler_module_not_generatable',
            actual: moduleContract?.capability ?? 'missing',
            expected: 'Generatable DOMC module',
            fixHint: 'Only generator adapters may materialize generatable modules.',
            gate: 'module-blocker',
          })
        );
        return;
      }
      issues.push(
        ...validateMaterializedRecords({
          registry: input.domcRegistry,
          sourcePath: materialization.sourcePath,
          records: materialization.records,
        })
      );
      setPath(packageDraft, materialization.sourcePath, materialization.records);
    });

  issues.push(
    ...validateGeneratedReferences({
      moduleContracts: generatedModuleContracts,
      materializations: input.generatedMaterializations,
    })
  );

  if (issues.some((issue) => issue.severity === 'error')) {
    return { issues };
  }

  const scenarioPackage = packageDraft as unknown as CompiledDemoScenarioPackage;
  scenarioPackage.scenario.fingerprint = computeScenarioFingerprint(scenarioPackage);
  return { scenarioPackage, issues };
}

export function domcAuditFromRegistry(registry: DemoDomcRegistry): Pick<
  RuntimeScenarioMeta,
  'domcRegistryFingerprint' | 'moduleContractFingerprints' | 'adapterVersions'
> {
  return {
    domcRegistryFingerprint: registry.domcFingerprint,
    moduleContractFingerprints: {},
    adapterVersions: Object.fromEntries(
      registry.modules
        .filter((moduleContract) => moduleContract.adapterRef)
        .map((moduleContract) => [moduleContract.moduleId, moduleContract.adapterRef!.adapterVersionRange])
    ),
  };
}
