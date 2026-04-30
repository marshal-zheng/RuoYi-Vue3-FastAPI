import { DEMO_HANDLER_COVERAGE, DEMO_INDEXED_DB_MAPPING } from '../scenarios/contract';
import { computeDomcRegistryFingerprint } from './fingerprint';
import type {
  DemoDomcModuleContract,
  DemoDomcQualityGateId,
  DemoDomcRegistry,
  DemoDomcRegistryDraft,
  DemoDomcValidationIssue,
  DemoDomcValidationResult,
} from './types';

const REMOTE_REF_PATTERN = /^[a-z][a-z0-9+.-]*:\/\//i;
const ABSOLUTE_FILE_PATH_PATTERN =
  /^(?:[A-Za-z]:[\\/]|\\\\|\/(?:Users|home|var|tmp|private|etc|Volumes|opt|usr|root)\b)/;
const SENSITIVE_VALUE_PATTERN =
  /(sk-[a-z0-9]{16,}|akia[0-9a-z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----)/i;
const SOURCE_PATH_PATTERN = /^[a-z][a-z0-9-]*(?:\.[a-z][a-zA-Z0-9]*)+$/;

function isPlainObject(value: unknown): value is Record<string, unknown> {
  return Object.prototype.toString.call(value) === '[object Object]';
}

function issue(input: {
  path: string;
  code: string;
  actual?: unknown;
  expected: string;
  fixHint: string;
  gate: DemoDomcQualityGateId;
  severity?: 'error' | 'warning';
}): DemoDomcValidationIssue {
  return {
    severity: input.severity ?? 'error',
    ...input,
  };
}

function validateExportSafety(
  value: unknown,
  issues: DemoDomcValidationIssue[],
  path = '$'
): void {
  if (typeof value === 'string') {
    if (ABSOLUTE_FILE_PATH_PATTERN.test(value)) {
      issues.push(
        issue({
          path,
          code: 'domc_unsafe_absolute_path',
          actual: value,
          expected: 'No local absolute filesystem paths',
          fixHint: 'Use repository-relative source paths or artifact names in DOMC.',
          gate: 'domc-registry-integrity',
        })
      );
    }
    if (SENSITIVE_VALUE_PATTERN.test(value)) {
      issues.push(
        issue({
          path,
          code: 'domc_unsafe_secret_like_value',
          actual: value,
          expected: 'No secret-like values',
          fixHint: 'Remove keys, tokens, or private values from DOMC artifacts.',
          gate: 'domc-registry-integrity',
        })
      );
    }
    return;
  }

  if (!value || typeof value !== 'object') return;
  if (Array.isArray(value)) {
    value.forEach((item, index) => validateExportSafety(item, issues, `${path}[${index}]`));
    return;
  }
  Object.entries(value as Record<string, unknown>).forEach(([key, child]) => {
    const childPath = `${path}.${key}`;
    if (key === '$ref' && typeof child === 'string' && REMOTE_REF_PATTERN.test(child)) {
      issues.push(
        issue({
          path: childPath,
          code: 'domc_remote_ref_rejected',
          actual: child,
          expected: 'Local schema only; remote $ref is forbidden',
          fixHint: 'Inline DOMC schema fragments or use local build-time constants.',
          gate: 'domc-schema',
        })
      );
    }
    validateExportSafety(child, issues, childPath);
  });
}

function validateModuleShape(
  moduleContract: DemoDomcModuleContract,
  moduleIndex: number,
  issues: DemoDomcValidationIssue[]
): void {
  const modulePath = `modules[${moduleIndex}]`;
  const sourcePathSet = new Set(moduleContract.sourcePaths);
  const tableBySourcePath = new Map<string, (typeof DEMO_INDEXED_DB_MAPPING.tables)[number]>(
    DEMO_INDEXED_DB_MAPPING.tables.map((table) => [table.sourcePath, table])
  );
  const handlerSources = new Set<string>(DEMO_HANDLER_COVERAGE.map((handler) => handler.source));

  if (!moduleContract.moduleId.trim()) {
    issues.push(
      issue({
        path: `${modulePath}.moduleId`,
        code: 'domc_module_id_missing',
        actual: moduleContract.moduleId,
        expected: 'Stable non-empty moduleId',
        fixHint: 'Set moduleId to the business module id used by scenario source paths.',
        gate: 'domc-schema',
      })
    );
  }

  moduleContract.sourcePaths.forEach((sourcePath, sourcePathIndex) => {
    if (!SOURCE_PATH_PATTERN.test(sourcePath)) {
      issues.push(
        issue({
          path: `${modulePath}.sourcePaths[${sourcePathIndex}]`,
          code: 'domc_source_path_invalid',
          actual: sourcePath,
          expected: 'module.slice source path',
          fixHint: 'Use source paths such as project.projects or simulation.sessions.',
          gate: 'domc-schema',
        })
      );
    }
    if (!tableBySourcePath.has(sourcePath)) {
      issues.push(
        issue({
          path: `${modulePath}.sourcePaths[${sourcePathIndex}]`,
          code: 'domc_source_path_table_mapping_missing',
          actual: sourcePath,
          expected: 'Source path declared by DEMO_INDEXED_DB_MAPPING',
          fixHint: 'Add an IndexedDB mapping before exposing this sourcePath in DOMC.',
          gate: 'handler-mapping-coverage',
        })
      );
    }
  });

  moduleContract.indexedDbTables.forEach((table, tableIndex) => {
    const canonical = tableBySourcePath.get(table.sourcePath);
    if (!canonical || canonical.table !== table.table || canonical.primaryKey !== table.primaryKey) {
      issues.push(
        issue({
          path: `${modulePath}.indexedDbTables[${tableIndex}]`,
          code: 'domc_table_mapping_drift',
          actual: table,
          expected: 'DOMC table ref matches DEMO_INDEXED_DB_MAPPING',
          fixHint: 'Regenerate the DOMC table reference from DEMO_INDEXED_DB_MAPPING.',
          gate: 'contract-drift',
        })
      );
    }
  });

  moduleContract.handlerCoverage.forEach((handler, handlerIndex) => {
    if (!handlerSources.has(handler.source) || !handler.coveredRoutes.length) {
      issues.push(
        issue({
          path: `${modulePath}.handlerCoverage[${handlerIndex}]`,
          code: 'domc_handler_coverage_invalid',
          actual: handler,
          expected: 'Existing handler coverage with covered routes',
          fixHint: 'Declare handler coverage migrated from DEMO_HANDLER_COVERAGE.',
          gate: 'handler-mapping-coverage',
        })
      );
    }
  });

  moduleContract.entities.forEach((entity, entityIndex) => {
    const entityPath = `${modulePath}.entities[${entityIndex}]`;
    const mapping = tableBySourcePath.get(entity.sourcePath);
    if (!sourcePathSet.has(entity.sourcePath)) {
      issues.push(
        issue({
          path: `${entityPath}.sourcePath`,
          code: 'domc_entity_source_path_not_declared',
          actual: entity.sourcePath,
          expected: 'Entity sourcePath listed in module.sourcePaths',
          fixHint: 'Add the entity sourcePath to module.sourcePaths or remove the entity.',
          gate: 'domc-registry-integrity',
        })
      );
    }
    if (!mapping || mapping.primaryKey !== entity.primaryKey || mapping.table !== entity.indexedDbTable) {
      issues.push(
        issue({
          path: entityPath,
          code: 'domc_entity_table_drift',
          actual: entity,
          expected: 'Entity table and primaryKey match IndexedDB mapping',
          fixHint: 'Sync entity.indexedDbTable and primaryKey from DEMO_INDEXED_DB_MAPPING.',
          gate: 'contract-drift',
        })
      );
    }
    const fields = new Set(entity.fields.map((field) => field.name));
    if (!fields.has(entity.primaryKey)) {
      issues.push(
        issue({
          path: `${entityPath}.primaryKey`,
          code: 'domc_primary_key_field_missing',
          actual: entity.primaryKey,
          expected: 'Primary key field appears in entity.fields',
          fixHint: 'Add the primary key field contract with semanticKind identifier.',
          gate: 'domc-schema',
        })
      );
    }
    entity.references.forEach((reference, referenceIndex) => {
      if (!fields.has(reference.field.replace(/\[]$/, ''))) {
        issues.push(
          issue({
            path: `${entityPath}.references[${referenceIndex}].field`,
            code: 'domc_reference_field_missing',
            actual: reference.field,
            expected: 'Reference field appears in entity.fields',
            fixHint: 'Add the foreignKey field contract or repair the reference field name.',
            gate: 'domc-schema',
          })
        );
      }
    });
  });

  moduleContract.uiJourneys.forEach((journey, journeyIndex) => {
    const allJourneyPaths = [journey.primarySourcePath, ...journey.requiredSupportSourcePaths];
    allJourneyPaths.forEach((sourcePath) => {
      if (!sourcePathSet.has(sourcePath)) {
        issues.push(
          issue({
            path: `${modulePath}.uiJourneys[${journeyIndex}]`,
            code: 'domc_ui_journey_source_path_missing',
            actual: sourcePath,
            expected: 'UI journey references declared module sourcePaths',
            fixHint: 'Repair the UI journey primary/support source paths.',
            gate: 'ui-journey-coverage',
          })
        );
      }
    });
  });

  if (moduleContract.capability === 'generatable') {
    if (!moduleContract.adapterRef) {
      issues.push(
        issue({
          path: `${modulePath}.adapterRef`,
          code: 'domc_adapter_ref_missing',
          actual: 'missing',
          expected: 'Generatable module declares compatible adapterRef',
          fixHint: 'Declare the MCP-side generator adapter id, version range, and output source paths.',
          gate: 'adapter-registry',
        })
      );
    } else {
      moduleContract.adapterRef.outputSourcePaths.forEach((sourcePath) => {
        if (!sourcePathSet.has(sourcePath)) {
          issues.push(
            issue({
              path: `${modulePath}.adapterRef.outputSourcePaths`,
              code: 'domc_adapter_output_source_path_not_declared',
              actual: sourcePath,
              expected: 'Adapter output only targets module.sourcePaths',
              fixHint: 'Limit adapter outputSourcePaths to DOMC-declared source paths.',
              gate: 'adapter-capability',
            })
          );
        }
      });
    }
  }

  if (moduleContract.capability === 'copyOnly' && !moduleContract.copyOnly) {
    issues.push(
      issue({
        path: `${modulePath}.copyOnly`,
        code: 'domc_copy_only_policy_missing',
        actual: 'missing',
        expected: 'copyOnly module declares default-scenario copy policy',
        fixHint: 'Declare copyOnly.sourcePaths, source, minItems, and reason.',
        gate: 'module-blocker',
      })
    );
  }

  if (moduleContract.copyOnly) {
    moduleContract.copyOnly.sourcePaths.forEach((sourcePath) => {
      if (!sourcePathSet.has(sourcePath)) {
        issues.push(
          issue({
            path: `${modulePath}.copyOnly.sourcePaths`,
            code: 'domc_copy_only_source_path_not_declared',
            actual: sourcePath,
            expected: 'copyOnly sourcePath declared by module.sourcePaths',
            fixHint: 'Sync copyOnly.sourcePaths with module.sourcePaths.',
            gate: 'module-blocker',
          })
        );
      }
    });
  }

  if (moduleContract.capability === 'unsupported' && !moduleContract.unsupportedReason?.trim()) {
    issues.push(
      issue({
        path: `${modulePath}.unsupportedReason`,
        code: 'domc_unsupported_reason_missing',
        actual: moduleContract.unsupportedReason,
        expected: 'Unsupported modules explain the missing capability',
        fixHint: 'Add a structured unsupportedReason before exposing the module in the registry.',
        gate: 'module-blocker',
      })
    );
  }
}

export async function validateDemoDomcRegistry(
  registry: unknown
): Promise<DemoDomcValidationResult> {
  const issues: DemoDomcValidationIssue[] = [];

  if (!isPlainObject(registry)) {
    return {
      valid: false,
      issues: [
        issue({
          path: '$',
          code: 'domc_registry_not_object',
          actual: typeof registry,
          expected: 'DemoDomcRegistry JSON object',
          fixHint: 'Export a DOMC registry object from src/demo/domc.',
          gate: 'domc-schema',
        }),
      ],
    };
  }

  const value = registry as DemoDomcRegistry | DemoDomcRegistryDraft;
  validateExportSafety(value, issues);

  if (value.schemaVersion !== 1) {
    issues.push(
      issue({
        path: 'schemaVersion',
        code: 'domc_schema_version_unsupported',
        actual: value.schemaVersion,
        expected: '1',
        fixHint: 'Use DOMC registry schemaVersion 1.',
        gate: 'domc-schema',
      })
    );
  }
  if (value.platformLayer !== 'DOMC') {
    issues.push(
      issue({
        path: 'platformLayer',
        code: 'domc_platform_layer_invalid',
        actual: value.platformLayer,
        expected: 'DOMC',
        fixHint: 'Set platformLayer to DOMC.',
        gate: 'domc-schema',
      })
    );
  }
  if (!Array.isArray(value.modules) || !value.modules.length) {
    issues.push(
      issue({
        path: 'modules',
        code: 'domc_modules_missing',
        actual: value.modules,
        expected: 'At least one DOMC module contract',
        fixHint: 'Declare module contracts for auth, system, project, and simulation.',
        gate: 'domc-schema',
      })
    );
  } else {
    const seenModules = new Set<string>();
    value.modules.forEach((moduleContract, moduleIndex) => {
      if (seenModules.has(moduleContract.moduleId)) {
        issues.push(
          issue({
            path: `modules[${moduleIndex}].moduleId`,
            code: 'domc_module_id_duplicate',
            actual: moduleContract.moduleId,
            expected: 'Unique moduleId',
            fixHint: 'Keep exactly one DOMC contract per moduleId.',
            gate: 'domc-registry-integrity',
          })
        );
      }
      seenModules.add(moduleContract.moduleId);
      validateModuleShape(moduleContract, moduleIndex, issues);
    });
  }

  if ('domcFingerprint' in value && value.domcFingerprint) {
    const actualFingerprint = await computeDomcRegistryFingerprint(value);
    if (value.domcFingerprint !== actualFingerprint) {
      issues.push(
        issue({
          path: 'domcFingerprint',
          code: 'domc_fingerprint_mismatch',
          actual: value.domcFingerprint,
          expected: actualFingerprint,
          fixHint: 'Recompute DOMC registry fingerprint from canonical JSON.',
          gate: 'domc-fingerprint',
        })
      );
    }
  }

  return {
    valid: !issues.some((item) => item.severity === 'error'),
    issues,
  };
}
