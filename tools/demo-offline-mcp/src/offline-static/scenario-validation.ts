import { Ajv2020, type ErrorObject, type ValidateFunction } from 'ajv/dist/2020.js';

import { createIssue } from '../errors.js';
import { computePackageSha256 } from '../hash.js';
import type {
  CompiledDemoScenarioPackage,
  DemoOfflineContractManifest,
  RuntimeScenarioMeta,
  RuntimeValidationSummary,
  ValidationIssue,
} from '../types.js';

const schemaValidatorCache = new WeakMap<object, ValidateFunction>();

function getPath(value: unknown, pathName: string): unknown {
  return pathName.split('.').reduce<unknown>((current, key) => {
    if (!current || typeof current !== 'object') return undefined;
    return (current as Record<string, unknown>)[key];
  }, value);
}

function getJsonPointerValue(value: unknown, pointer: string): unknown {
  if (!pointer) return value;

  return pointer
    .split('/')
    .slice(1)
    .map((segment) => segment.replace(/~1/g, '/').replace(/~0/g, '~'))
    .reduce<unknown>((current, segment) => {
      if (current === undefined || current === null) return undefined;
      if (Array.isArray(current)) return current[Number(segment)];
      if (typeof current !== 'object') return undefined;
      return (current as Record<string, unknown>)[segment];
    }, value);
}

function jsonPointerToPath(pointer: string): string {
  if (!pointer) return '$';

  return pointer
    .split('/')
    .slice(1)
    .map((segment) => segment.replace(/~1/g, '/').replace(/~0/g, '~'))
    .reduce((pathName, segment) => {
      if (/^\d+$/.test(segment)) return `${pathName}[${segment}]`;
      return pathName === '$' ? segment : `${pathName}.${segment}`;
    }, '$');
}

function appendPropertyPath(basePath: string, property: string): string {
  if (/^[A-Za-z_$][\w$]*$/.test(property)) {
    return basePath === '$' ? property : `${basePath}.${property}`;
  }

  return `${basePath}[${JSON.stringify(property)}]`;
}

function ajvIssuePath(error: ErrorObject): string {
  const basePath = jsonPointerToPath(error.instancePath);
  const additionalProperty =
    error.keyword === 'additionalProperties' &&
    typeof error.params === 'object' &&
    error.params &&
    'additionalProperty' in error.params &&
    typeof error.params.additionalProperty === 'string'
      ? error.params.additionalProperty
      : undefined;

  return additionalProperty ? appendPropertyPath(basePath, additionalProperty) : basePath;
}

function getAjvIssueActual(scenarioPackage: CompiledDemoScenarioPackage, error: ErrorObject): unknown {
  if (
    error.keyword === 'additionalProperties' &&
    typeof error.params === 'object' &&
    error.params &&
    'additionalProperty' in error.params &&
    typeof error.params.additionalProperty === 'string'
  ) {
    const parent = getJsonPointerValue(scenarioPackage, error.instancePath);
    return parent && typeof parent === 'object'
      ? (parent as Record<string, unknown>)[error.params.additionalProperty]
      : undefined;
  }

  return getJsonPointerValue(scenarioPackage, error.instancePath);
}

function getScenarioSchemaValidator(scenarioSchema: unknown): ValidateFunction {
  if (!scenarioSchema || typeof scenarioSchema !== 'object' || Array.isArray(scenarioSchema)) {
    throw new Error('demo-contract/scenario.schema.json must be a JSON object.');
  }

  const cached = schemaValidatorCache.get(scenarioSchema);
  if (cached) return cached;

  const ajv = new Ajv2020({
    allErrors: true,
    strict: false,
    validateSchema: true,
  });
  const validator = ajv.compile(scenarioSchema);
  schemaValidatorCache.set(scenarioSchema, validator);
  return validator;
}

function requireArray(value: unknown, path: string, issues: ValidationIssue[], minItems = 0): void {
  if (!Array.isArray(value)) {
    issues.push(
      createIssue({
        path,
        code: 'runtime_package_array_missing',
        severity: 'error',
        actual: typeof value,
        expected: 'array',
        fixHint: `Ensure ${path} is an array in the DemoScenarioPackage.`,
        autoRepairable: false,
      })
    );
    return;
  }

  if (value.length < minItems) {
    issues.push(
      createIssue({
        path,
        code: 'runtime_package_min_items_failed',
        severity: 'error',
        actual: value.length,
        expected: `At least ${minItems} item(s)`,
        fixHint: `Regenerate the package so ${path} contains enough demo data.`,
        autoRepairable: false,
      })
    );
  }
}

function requireString(value: unknown, path: string, issues: ValidationIssue[]): void {
  if (typeof value !== 'string' || !value.trim()) {
    issues.push(
      createIssue({
        path,
        code: 'runtime_package_required_string_missing',
        severity: 'error',
        actual: value,
        expected: 'Non-empty string',
        fixHint: `Set ${path} to a stable non-empty string.`,
        autoRepairable: false,
      })
    );
  }
}

export function validateScenarioPackageSchema(
  scenarioPackage: CompiledDemoScenarioPackage,
  scenarioSchema: unknown
): ValidationIssue[] {
  let validator: ValidateFunction;

  try {
    validator = getScenarioSchemaValidator(scenarioSchema);
  } catch (error) {
    return [
      createIssue({
        path: 'demo-contract/scenario.schema.json',
        code: 'runtime_package_json_schema_invalid',
        severity: 'error',
        actual: error instanceof Error ? error.message : String(error),
        expected: 'A valid local JSON Schema Draft 2020-12 document',
        fixHint: 'Rebuild demo-offline so demo-contract/scenario.schema.json is valid and local.',
        autoRepairable: false,
      }),
    ];
  }

  if (validator(scenarioPackage)) {
    return [];
  }

  return (validator.errors ?? []).map((error) => {
    const pathName = ajvIssuePath(error);
    return createIssue({
      path: pathName,
      code: `runtime_package_schema_${error.keyword}`,
      severity: 'error',
      actual: getAjvIssueActual(scenarioPackage, error),
      expected: error.message ?? `Satisfy JSON Schema keyword ${error.keyword}`,
      fixHint: `Repair ${pathName} to satisfy demo-contract/scenario.schema.json.`,
      autoRepairable: false,
    });
  });
}

export function validateScenarioPackageShape(
  scenarioPackage: CompiledDemoScenarioPackage,
  contract?: DemoOfflineContractManifest
): ValidationIssue[] {
  const issues: ValidationIssue[] = [];

  if (scenarioPackage.schemaVersion !== 1) {
    issues.push(
      createIssue({
        path: 'schemaVersion',
        code: 'runtime_package_schema_version_unsupported',
        severity: 'error',
        actual: scenarioPackage.schemaVersion,
        expected: '1',
        fixHint: 'Regenerate the package for DemoScenarioPackage schemaVersion 1.',
        autoRepairable: false,
      })
    );
  }

  requireString(scenarioPackage.scenario?.id, 'scenario.id', issues);
  requireString(scenarioPackage.scenario?.name, 'scenario.name', issues);
  requireString(scenarioPackage.scenario?.version, 'scenario.version', issues);
  requireString(scenarioPackage.scenario?.fingerprint, 'scenario.fingerprint', issues);

  const minByPath = new Map((contract?.indexedDbMapping.tables ?? []).map((table) => [table.sourcePath, table.minItems ?? 0]));

  [
    'auth.accounts',
    'auth.roles',
    'auth.permissions',
    'system.menus',
    'system.dictTypes',
    'system.dicts',
    'system.departments',
    'system.posts',
    'system.users',
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
  ].forEach((pathName) => requireArray(getPath(scenarioPackage, pathName), pathName, issues, minByPath.get(pathName) ?? 0));

  return issues;
}

export function validateRuntimeScenarioPackage(
  scenarioPackage: CompiledDemoScenarioPackage,
  scenarioSchema: unknown,
  contract?: DemoOfflineContractManifest
): ValidationIssue[] {
  return [
    ...validateScenarioPackageSchema(scenarioPackage, scenarioSchema),
    ...validateScenarioPackageShape(scenarioPackage, contract),
  ];
}

function requireMetaString(
  meta: Partial<RuntimeScenarioMeta>,
  field: keyof RuntimeScenarioMeta,
  issues: ValidationIssue[]
): void {
  const value = meta[field];
  if (typeof value !== 'string' || !value.trim()) {
    issues.push(
      createIssue({
        path: `runtime-release.metadata.${field}`,
        code: 'runtime_meta_required_string_missing',
        severity: 'error',
        actual: value,
        expected: 'Non-empty string',
        fixHint: `Regenerate the v2 release metadata with a non-empty ${field}.`,
        autoRepairable: true,
      })
    );
  }
}

function validateRuntimeValidationSummary(value: unknown, issues: ValidationIssue[]): void {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    issues.push(
      createIssue({
        path: 'runtime-release.metadata.validationSummary',
        code: 'runtime_meta_validation_summary_missing',
        severity: 'error',
        actual: value,
        expected: 'RuntimeValidationSummary object',
        fixHint: 'Regenerate the v2 release metadata with validationSummary from the validation pipeline.',
        autoRepairable: true,
      })
    );
    return;
  }

  const summary = value as Partial<RuntimeValidationSummary>;
  (['schemaValid', 'contractValid', 'invariantValid'] as const).forEach((field) => {
    if (typeof summary[field] !== 'boolean') {
      issues.push(
        createIssue({
          path: `runtime-release.metadata.validationSummary.${field}`,
          code: 'runtime_meta_validation_summary_boolean_missing',
          severity: 'error',
          actual: summary[field],
          expected: 'boolean',
          fixHint: `Regenerate the v2 release metadata with validationSummary.${field} as a boolean.`,
          autoRepairable: true,
        })
      );
    }
  });

  if (summary.dryRunValid !== undefined && typeof summary.dryRunValid !== 'boolean') {
    issues.push(
      createIssue({
        path: 'runtime-release.metadata.validationSummary.dryRunValid',
        code: 'runtime_meta_validation_summary_boolean_missing',
        severity: 'error',
        actual: summary.dryRunValid,
        expected: 'boolean',
        fixHint: 'Regenerate the v2 release metadata with validationSummary.dryRunValid as a boolean.',
        autoRepairable: true,
      })
    );
  }

  if (typeof summary.issueCount !== 'number' || !Number.isFinite(summary.issueCount)) {
    issues.push(
      createIssue({
        path: 'runtime-release.metadata.validationSummary.issueCount',
        code: 'runtime_meta_validation_summary_issue_count_missing',
        severity: 'error',
        actual: summary.issueCount,
        expected: 'finite number',
        fixHint: 'Regenerate the v2 release metadata with validationSummary.issueCount from validation results.',
        autoRepairable: true,
      })
    );
  }
}

export function validateRuntimeMeta(
  scenarioPackage: CompiledDemoScenarioPackage,
  meta: unknown,
  contract: DemoOfflineContractManifest
): ValidationIssue[] {
  const issues: ValidationIssue[] = [];
  if (!meta || typeof meta !== 'object' || Array.isArray(meta)) {
    return [
      createIssue({
        path: 'runtime-release.metadata',
        code: 'runtime_meta_missing',
        severity: 'error',
        actual: meta,
        expected: 'RuntimeScenarioMeta object',
        fixHint: 'Create v2 release metadata from the candidate package before activation.',
        autoRepairable: true,
      }),
    ];
  }

  const metaValue = meta as Partial<RuntimeScenarioMeta>;

  (
    [
      'scenarioId',
      'topicKey',
      'contractFingerprint',
      'generatorVersion',
      'seed',
      'generatedAt',
      'sourceTarget',
      'scenarioFingerprint',
      'packageSha256',
    ] as const
  ).forEach((field) => requireMetaString(metaValue, field, issues));

  if (metaValue.schemaVersion !== 1) {
    issues.push(
      createIssue({
        path: 'runtime-release.metadata.schemaVersion',
        code: 'runtime_meta_schema_version_unsupported',
        severity: 'error',
        actual: metaValue.schemaVersion,
        expected: '1',
        fixHint: 'Regenerate the v2 release metadata for DemoScenarioPackage schemaVersion 1.',
        autoRepairable: true,
      })
    );
  }

  if (metaValue.sourceTarget !== undefined && metaValue.sourceTarget !== 'offline-static') {
    issues.push(
      createIssue({
        path: 'runtime-release.metadata.sourceTarget',
        code: 'runtime_meta_source_target_unsupported',
        severity: 'error',
        actual: metaValue.sourceTarget,
        expected: 'offline-static',
        fixHint: 'Regenerate the package with target.kind=offline-static.',
        autoRepairable: true,
      })
    );
  }

  validateRuntimeValidationSummary(metaValue.validationSummary, issues);

  if (
    typeof metaValue.scenarioId === 'string' &&
    metaValue.scenarioId.trim() &&
    metaValue.scenarioId !== scenarioPackage.scenario.id
  ) {
    issues.push(
      createIssue({
        path: 'runtime-release.metadata.scenarioId',
        code: 'runtime_meta_scenario_id_mismatch',
        severity: 'error',
        actual: metaValue.scenarioId,
        expected: scenarioPackage.scenario.id,
        fixHint: 'Regenerate the v2 release metadata from the candidate package being activated.',
        autoRepairable: true,
      })
    );
  }

  if (
    typeof metaValue.contractFingerprint === 'string' &&
    metaValue.contractFingerprint.trim() &&
    metaValue.contractFingerprint !== contract.contractFingerprint
  ) {
    issues.push(
      createIssue({
        path: 'runtime-release.metadata.contractFingerprint',
        code: 'runtime_meta_contract_fingerprint_mismatch',
        severity: 'error',
        actual: metaValue.contractFingerprint,
        expected: contract.contractFingerprint,
        fixHint: 'Regenerate the package against the current demo-contract/contract.json.',
        autoRepairable: false,
      })
    );
  }

  if (
    typeof metaValue.scenarioFingerprint === 'string' &&
    metaValue.scenarioFingerprint.trim() &&
    metaValue.scenarioFingerprint !== scenarioPackage.scenario.fingerprint
  ) {
    issues.push(
      createIssue({
        path: 'runtime-release.metadata.scenarioFingerprint',
        code: 'runtime_meta_scenario_fingerprint_mismatch',
        severity: 'error',
        actual: metaValue.scenarioFingerprint,
        expected: scenarioPackage.scenario.fingerprint,
        fixHint: 'Regenerate the v2 release metadata from the candidate package being activated.',
        autoRepairable: true,
      })
    );
  }

  const packageSha256 = computePackageSha256(scenarioPackage);
  if (
    typeof metaValue.packageSha256 === 'string' &&
    metaValue.packageSha256.trim() &&
    metaValue.packageSha256 !== packageSha256
  ) {
    issues.push(
      createIssue({
        path: 'runtime-release.metadata.packageSha256',
        code: 'runtime_meta_package_hash_mismatch',
        severity: 'error',
        actual: metaValue.packageSha256,
        expected: packageSha256,
        fixHint: 'Regenerate the v2 release metadata after the final candidate package content is settled.',
        autoRepairable: true,
      })
    );
  }

  return issues;
}

export function summarizeRuntimeValidation(
  schemaIssues: ValidationIssue[],
  contractIssues: ValidationIssue[],
  invariantIssues: ValidationIssue[],
  dryRunValid?: boolean
): RuntimeValidationSummary {
  return {
    schemaValid: schemaIssues.filter((issue) => issue.severity === 'error').length === 0,
    contractValid: contractIssues.filter((issue) => issue.severity === 'error').length === 0,
    invariantValid: invariantIssues.filter((issue) => issue.severity === 'error').length === 0,
    dryRunValid,
    issueCount: schemaIssues.length + contractIssues.length + invariantIssues.length,
  };
}
