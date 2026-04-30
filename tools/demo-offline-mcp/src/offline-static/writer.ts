import fs from 'node:fs/promises';
import path from 'node:path';

import { createIssue } from '../errors.js';
import { computePackageSha256, sha256Hex } from '../hash.js';
import type {
  CompiledDemoScenarioPackage,
  DemoOfflineArtifact,
  OfflineStaticActivationResult,
  RuntimeScenarioMeta,
  ToolEnvelope,
  ValidationIssue,
} from '../types.js';
import type { SemanticQualityReport } from '../semantic/types.js';
import { errorEnvelope, okEnvelope } from '../types.js';
import { readOfflineStaticContract } from './contract.js';
import { dryRunImportRuntimePackage } from './import-dry-run.js';
import { validateRuntimeInvariants } from './invariants.js';
import {
  assertOfflineStaticScenarioWritePath,
  failedReleaseDirectoryPath,
  relativeToOfflineRoot,
  releaseDirectoryPath,
  stagingReleaseDirectoryPath,
  type OfflineStaticTargetPaths,
} from './paths.js';
import {
  summarizeRuntimeValidation,
  validateRuntimeMeta,
  validateRuntimeScenarioPackage,
} from './scenario-validation.js';
import {
  assertReleaseExportSafe,
  assertRuntimePackageManifest,
  assertRuntimePackagePointer,
  assembleScenarioPackageFromRelease,
  createRuntimePackageV2Release,
  manifestPathForReleaseId,
  validateDescriptorJsonIntegrity,
  validateRuntimePackageProvenance,
  RUNTIME_PACKAGE_V2_ACTIVE_POINTER_PATH,
  RUNTIME_PACKAGE_V2_PREVIOUS_POINTER_PATH,
  type RuntimePackagePointer,
  type RuntimePackageV2MaterializationReason,
  type RuntimePackageTimelineEvent,
  type RuntimePackageV2Manifest,
  type RuntimePackageV2ReleaseFiles,
  type RuntimeSliceDescriptor,
} from './release-store.js';

async function readJsonFile<T>(filePath: string): Promise<T> {
  return JSON.parse(await fs.readFile(filePath, 'utf8')) as T;
}

async function writeJsonFile(paths: OfflineStaticTargetPaths, filePath: string, value: unknown): Promise<void> {
  await assertOfflineStaticScenarioWritePath(paths, filePath);
  assertReleaseExportSafe(value);
  await fs.mkdir(path.dirname(filePath), { recursive: true });
  await fs.writeFile(filePath, `${JSON.stringify(value, null, 2)}\n`, 'utf8');
}

async function pathExists(filePath: string): Promise<boolean> {
  return fs
    .access(filePath)
    .then(() => true)
    .catch(() => false);
}

function createReleaseId(meta: RuntimeScenarioMeta): string {
  const topic = meta.topicKey
    .toLowerCase()
    .replace(/[^a-z0-9._-]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 48);
  return `${topic || meta.scenarioId}-${meta.seed.slice(0, 12)}`.slice(0, 80);
}

function pointerForManifest(manifest: RuntimePackageV2Manifest, activatedAt = new Date().toISOString()): RuntimePackagePointer {
  return {
    formatVersion: 2,
    releaseId: manifest.releaseId,
    manifestPath: manifestPathForReleaseId(manifest.releaseId),
    manifestSha256: manifest.rootSha256,
    activatedAt,
    contractFingerprint: manifest.contractFingerprint,
    scenarioFingerprint: manifest.scenarioFingerprint,
  };
}

function materializationReasonsFromDomc(
  contractBundle: Awaited<ReturnType<typeof readOfflineStaticContract>>
): Partial<Record<string, RuntimePackageV2MaterializationReason>> {
  return Object.fromEntries(
    contractBundle.domcRegistry.modules.flatMap((moduleContract) =>
      moduleContract.materializationPolicy.map((policy) => [
        policy.sourcePath,
        policy.materializationReason,
      ])
    )
  );
}

function createMetaFromManifest(
  manifest: RuntimePackageV2Manifest,
  validationSummary: RuntimeScenarioMeta['validationSummary']
): RuntimeScenarioMeta {
  return {
    scenarioId: manifest.scenarioId,
    topicKey: manifest.scenarioId,
    schemaVersion: manifest.schemaVersion,
    contractFingerprint: manifest.contractFingerprint,
    generatorVersion: manifest.generatorVersion,
    seed: manifest.seed,
    generatedAt: manifest.generatedAt,
    validationSummary,
    sourceTarget: 'offline-static',
    scenarioFingerprint: manifest.scenarioFingerprint,
    packageSha256: '',
    releaseId: manifest.releaseId,
    manifestPath: manifestPathForReleaseId(manifest.releaseId),
    manifestSha256: manifest.rootSha256,
    provenancePath: `demo-scenarios/releases/${manifest.releaseId}/provenance.json`,
    domcRegistryFingerprint: manifest.domcRegistryFingerprint,
    moduleContractFingerprints: manifest.moduleContractFingerprints,
    adapterVersions: manifest.adapterVersions,
    adapterCapabilitySummary: manifest.adapterCapabilitySummary,
  };
}

function validationFailedEnvelope(input: {
  paths: OfflineStaticTargetPaths;
  manifest?: RuntimePackageV2Manifest;
  scenarioPackage?: CompiledDemoScenarioPackage;
  errors: ValidationIssue[];
  phase?: OfflineStaticActivationResult['phase'];
}): ToolEnvelope<OfflineStaticActivationResult> {
  const manifest = input.manifest;
  const scenarioPackage = input.scenarioPackage;

  return errorEnvelope('Runtime v2 release validation failed; active pointer was not changed.', input.errors, {
    data: {
      phase: input.phase ?? 'validation_failed',
      targetKind: 'offline-static',
      packageFormat: 'v2',
      targetRoot: input.paths.targetRoot,
      releaseId: manifest?.releaseId,
      scenarioId: manifest?.scenarioId ?? scenarioPackage?.scenario.id ?? '',
      topicKey: manifest?.scenarioId ?? '',
      seed: manifest?.seed ?? scenarioPackage?.scenario.seed ?? '',
      contractFingerprint: manifest?.contractFingerprint ?? '',
      scenarioFingerprint: manifest?.scenarioFingerprint ?? scenarioPackage?.scenario.fingerprint ?? '',
      validationSummary: manifest
        ? {
            schemaValid: false,
            contractValid: false,
            invariantValid: false,
            issueCount: input.errors.length,
          }
        : undefined,
      paths: [],
    },
    nextActions: ['Regenerate the v2 release package, then activate it again.'],
  });
}

function releaseLoadIssue(paths: OfflineStaticTargetPaths, releaseId: string, fromStaging: boolean, error: unknown): ValidationIssue {
  const releaseDir = fromStaging ? stagingReleaseDirectoryPath(paths, releaseId) : releaseDirectoryPath(paths, releaseId);
  return createIssue({
    path: relativeToOfflineRoot(paths, path.join(releaseDir, 'manifest.json')),
    code: 'runtime_v2_manifest_schema_invalid',
    severity: 'error',
    actual: error instanceof Error ? error.message : String(error),
    expected: 'Readable v2 release manifest with valid descriptors',
    fixHint: 'Regenerate v2 release so manifest schema, descriptor metadata, and root hash are valid.',
    autoRepairable: false,
  });
}

async function quarantineStagingRelease(paths: OfflineStaticTargetPaths, releaseId: string): Promise<string | undefined> {
  const stagingDir = stagingReleaseDirectoryPath(paths, releaseId);
  if (!(await pathExists(stagingDir))) return undefined;

  const failedDir = failedReleaseDirectoryPath(paths, releaseId);
  await fs.mkdir(paths.failedRoot, { recursive: true });
  await fs.rm(failedDir, { recursive: true, force: true });
  await fs.rename(stagingDir, failedDir).catch(async () => {
    await fs.rm(stagingDir, { recursive: true, force: true }).catch(() => undefined);
  });

  return relativeToOfflineRoot(paths, failedDir);
}

export async function appendOfflineStaticAudit(
  paths: OfflineStaticTargetPaths,
  event: Record<string, unknown>
): Promise<void> {
  await fs.mkdir(path.dirname(paths.auditLogPath), { recursive: true });
  await fs.appendFile(
    paths.auditLogPath,
    `${JSON.stringify({ time: new Date().toISOString(), ...event })}\n`,
    'utf8'
  );
}

export async function appendRuntimePackageTimeline(
  paths: OfflineStaticTargetPaths,
  event: Omit<RuntimePackageTimelineEvent, 'eventId' | 'time'>
): Promise<ValidationIssue | undefined> {
  const entry: RuntimePackageTimelineEvent = {
    eventId: sha256Hex(`${event.eventType}:${event.releaseId}:${Date.now()}:${Math.random()}`).slice(0, 32),
    time: new Date().toISOString(),
    ...event,
  };

  try {
    await assertOfflineStaticScenarioWritePath(paths, paths.timelinePath);
    const existing = await fs
      .readFile(paths.timelinePath, 'utf8')
      .then((source) => JSON.parse(source) as RuntimePackageTimelineEvent[])
      .catch(() => []);
    const timeline = Array.isArray(existing) ? existing : [];
    const tempPath = `${paths.timelinePath}.tmp`;
    await fs.writeFile(tempPath, `${JSON.stringify([...timeline, entry], null, 2)}\n`, 'utf8');
    await fs.rename(tempPath, paths.timelinePath);
    return undefined;
  } catch (error) {
    return createIssue({
      path: 'demo-scenarios/timeline.json',
      code: 'runtime_v2_timeline_write_failed',
      severity: 'warning',
      actual: error instanceof Error ? error.message : String(error),
      expected: 'Append timeline event',
      fixHint: 'Check filesystem permissions; release activation can proceed without timeline.',
      autoRepairable: false,
    });
  }
}

export async function createRuntimeScenarioMeta(input: {
  scenarioPackage: CompiledDemoScenarioPackage;
  topicKey: string;
  seed: string;
  contractFingerprint: string;
  generatorVersion: string;
  validationSummary: RuntimeScenarioMeta['validationSummary'];
  generatedAt?: string;
}): Promise<RuntimeScenarioMeta> {
  return {
    scenarioId: input.scenarioPackage.scenario.id,
    topicKey: input.topicKey,
    schemaVersion: input.scenarioPackage.schemaVersion,
    contractFingerprint: input.contractFingerprint,
    generatorVersion: input.generatorVersion,
    seed: input.seed,
    generatedAt: input.generatedAt ?? new Date().toISOString(),
    validationSummary: input.validationSummary,
    sourceTarget: 'offline-static',
    scenarioFingerprint: input.scenarioPackage.scenario.fingerprint,
    packageSha256: computePackageSha256(input.scenarioPackage),
  };
}

async function writeReleaseFiles(
  paths: OfflineStaticTargetPaths,
  stagingDir: string,
  release: RuntimePackageV2ReleaseFiles
): Promise<string[]> {
  const changedPaths: string[] = [];

  await fs.rm(stagingDir, { recursive: true, force: true });
  await fs.mkdir(path.join(stagingDir, 'slices'), { recursive: true });

  for (const slice of release.slices) {
    const filePath = path.join(stagingDir, slice.descriptor.path);
    await writeJsonFile(paths, filePath, slice.data);
    changedPaths.push(relativeToOfflineRoot(paths, filePath));
  }

  for (const artifact of release.artifacts) {
    const filePath = path.join(stagingDir, artifact.descriptor.path);
    await writeJsonFile(paths, filePath, artifact.data);
    changedPaths.push(relativeToOfflineRoot(paths, filePath));
  }

  const provenancePath = path.join(stagingDir, 'provenance.json');
  await writeJsonFile(paths, provenancePath, release.provenance);
  changedPaths.push(relativeToOfflineRoot(paths, provenancePath));

  const manifestPath = path.join(stagingDir, 'manifest.json');
  await writeJsonFile(paths, manifestPath, release.manifest);
  changedPaths.push(relativeToOfflineRoot(paths, manifestPath));

  return changedPaths;
}

export async function writeRuntimeCandidatePackage(
  paths: OfflineStaticTargetPaths,
  scenarioPackage: CompiledDemoScenarioPackage,
  meta: RuntimeScenarioMeta,
  options: { semanticReport?: SemanticQualityReport; businessDescription?: string } = {}
): Promise<ToolEnvelope<OfflineStaticActivationResult>> {
  const contractBundle = await readOfflineStaticContract(paths);
  const releaseId = createReleaseId(meta);
  const finalReleaseDir = releaseDirectoryPath(paths, releaseId);

  if (await pathExists(finalReleaseDir)) {
    const issue = createIssue({
      path: relativeToOfflineRoot(paths, finalReleaseDir),
      code: 'runtime_v2_release_already_exists',
      severity: 'error',
      actual: releaseId,
      expected: 'A new immutable releaseId',
      fixHint: 'Regenerate with a different seed/topic or remove only an unpublished staging release.',
      autoRepairable: false,
    });
    return validationFailedEnvelope({ paths, scenarioPackage, errors: [issue] });
  }

  let release: RuntimePackageV2ReleaseFiles;
  try {
    release = createRuntimePackageV2Release({
      releaseId,
      scenarioPackage,
      contractFingerprint: meta.contractFingerprint,
      generatorVersion: meta.generatorVersion,
      generatedAt: meta.generatedAt,
      topicKey: meta.topicKey,
      topicSummary: scenarioPackage.scenario.name,
      businessDescriptionSha256: options.businessDescription
        ? sha256Hex(options.businessDescription.trim())
        : undefined,
      seed: meta.seed,
      validationSummary: meta.validationSummary,
      materializationReason: options.semanticReport ? 'semantic-generated' : 'runtime-required',
      materializationReasonsBySourcePath: materializationReasonsFromDomc(contractBundle),
      tableMappings: contractBundle.contract.indexedDbMapping.tables,
      semanticReport: options.semanticReport,
      domcRegistryFingerprint: meta.domcRegistryFingerprint,
      moduleContractFingerprints: meta.moduleContractFingerprints,
      adapterVersions: meta.adapterVersions,
      adapterCapabilitySummary: meta.adapterCapabilitySummary,
    });
  } catch (error) {
    const issue = createIssue({
      path: 'demo-scenarios/releases/.staging',
      code: 'runtime_v2_release_materialization_failed',
      severity: 'error',
      actual: error instanceof Error ? error.message : String(error),
      expected: 'A complete v2 release candidate',
      fixHint: 'Repair the generated package or contract mapping, then regenerate the v2 release.',
      autoRepairable: false,
    });
    return validationFailedEnvelope({ paths, scenarioPackage, errors: [issue] });
  }
  const stagingDir = stagingReleaseDirectoryPath(paths, releaseId);
  const changedPaths = await writeReleaseFiles(paths, stagingDir, release);
  const timelineWarning = await appendRuntimePackageTimeline(paths, {
    eventType: 'staged',
    releaseId,
    actor: 'mcp',
    manifestSha256: release.manifest.rootSha256,
    result: 'success',
    summary: `Staged v2 runtime release ${releaseId}.`,
  });

  await appendOfflineStaticAudit(paths, {
    tool: 'offline_static_writer',
    phase: 'staged',
    packageFormat: 'v2',
    releaseId,
    scenarioId: scenarioPackage.scenario.id,
    topicKey: meta.topicKey,
    seed: meta.seed,
    contractFingerprint: meta.contractFingerprint,
    manifestSha256: release.manifest.rootSha256,
    paths: changedPaths,
    warnings: timelineWarning ? [{ code: timelineWarning.code, path: timelineWarning.path }] : [],
  });

  const artifacts: DemoOfflineArtifact[] = changedPaths.map((changedPath) => ({
    kind: changedPath.endsWith('semantic-report.json') ? 'report' : 'file',
    label: changedPath,
    path: path.join(paths.targetRoot, changedPath),
  }));
  const warnings = timelineWarning ? [timelineWarning] : undefined;

  return okEnvelope(
    'Runtime v2 release staged.',
    {
      phase: 'staged',
      targetKind: 'offline-static',
      packageFormat: 'v2',
      targetRoot: paths.targetRoot,
      releaseId,
      scenarioId: scenarioPackage.scenario.id,
      topicKey: meta.topicKey,
      seed: meta.seed,
      contractFingerprint: meta.contractFingerprint,
      scenarioFingerprint: scenarioPackage.scenario.fingerprint,
      domcRegistryFingerprint: meta.domcRegistryFingerprint,
      moduleContractFingerprints: meta.moduleContractFingerprints,
      adapterVersions: meta.adapterVersions,
      moduleTrace: undefined,
      manifestPath: relativeToOfflineRoot(paths, path.join(stagingDir, 'manifest.json')),
      provenancePath: relativeToOfflineRoot(paths, path.join(stagingDir, 'provenance.json')),
      validationSummary: meta.validationSummary,
      semanticQualitySummary: options.semanticReport?.summary,
      semanticReportPath: options.semanticReport
        ? relativeToOfflineRoot(paths, path.join(stagingDir, 'semantic-report.json'))
        : undefined,
      paths: changedPaths,
    },
    {
      artifacts,
      ...(warnings ? { errors: warnings } : {}),
    }
  );
}

export async function writeSemanticFailureReport(
  paths: OfflineStaticTargetPaths,
  semanticReport: SemanticQualityReport
): Promise<string> {
  await fs.mkdir(paths.demoScenariosRoot, { recursive: true });
  await writeJsonFile(paths, paths.semanticFailedReportPath, semanticReport);

  const reportPath = relativeToOfflineRoot(paths, paths.semanticFailedReportPath);
  await appendOfflineStaticAudit(paths, {
    tool: 'offline_static_writer',
    phase: 'semantic_validation_failed',
    packageFormat: 'v2',
    scenarioId: semanticReport.scenarioId,
    topicKey: semanticReport.topicKey,
    seed: semanticReport.seed,
    errorCount: semanticReport.summary.errorCount,
    warningCount: semanticReport.summary.warningCount,
    path: reportPath,
  });

  return reportPath;
}

async function latestStagingReleaseId(paths: OfflineStaticTargetPaths): Promise<string> {
  const entries = await fs.readdir(paths.stagingRoot, { withFileTypes: true }).catch(() => []);
  const directories = await Promise.all(
    entries
      .filter((entry) => entry.isDirectory())
      .map(async (entry) => {
        const dir = path.join(paths.stagingRoot, entry.name);
        const stat = await fs.stat(dir);
        return { releaseId: entry.name, mtimeMs: stat.mtimeMs };
      })
  );

  directories.sort((left, right) => right.mtimeMs - left.mtimeMs);
  const releaseId = directories[0]?.releaseId;
  if (!releaseId) {
    throw new Error('No staged v2 release is available to activate.');
  }
  return releaseId;
}

export async function inspectReleaseRetention(paths: OfflineStaticTargetPaths): Promise<ValidationIssue[]> {
  const issues: ValidationIssue[] = [];
  const releaseEntries = await fs.readdir(paths.releasesRoot, { withFileTypes: true }).catch(() => []);
  const releaseIds = releaseEntries
    .filter((entry) => entry.isDirectory() && !entry.name.startsWith('.'))
    .map((entry) => entry.name);
  const protectedPointers = [
    { label: 'active', path: paths.activePointerPath },
    { label: 'previous', path: paths.previousPointerPath },
  ];

  for (const pointer of protectedPointers) {
    const pointerValue = await fs
      .readFile(pointer.path, 'utf8')
      .then((source) => assertRuntimePackagePointer(JSON.parse(source)) as RuntimePackagePointer)
      .catch(() => undefined);

    if (pointerValue && !(await pathExists(releaseDirectoryPath(paths, pointerValue.releaseId)))) {
      issues.push(
        createIssue({
          path: relativeToOfflineRoot(paths, pointer.path),
          code: 'runtime_v2_retained_release_missing',
          severity: 'error',
          actual: pointerValue.releaseId,
          expected: `${pointer.label} pointer release must be retained`,
          fixHint: 'Restore the referenced release or activate a valid retained release.',
          autoRepairable: false,
        })
      );
    }
  }

  if (releaseIds.length > 10) {
    issues.push(
      createIssue({
        path: 'demo-scenarios/releases',
        code: 'runtime_v2_release_store_retention_warning',
        severity: 'warning',
        actual: releaseIds.length,
        expected: 'At most 10 retained verified releases by default',
        fixHint: 'Plan a future GC run that preserves active/previous and recent verified releases.',
        autoRepairable: false,
      })
    );
  }

  return issues;
}

export async function loadRuntimeReleasePackage(
  paths: OfflineStaticTargetPaths,
  releaseId: string,
  options: { fromStaging?: boolean } = {}
): Promise<{
  manifest: RuntimePackageV2Manifest;
  scenarioPackage?: CompiledDemoScenarioPackage;
  issues: ValidationIssue[];
}> {
  const releaseDir = options.fromStaging
    ? stagingReleaseDirectoryPath(paths, releaseId)
    : releaseDirectoryPath(paths, releaseId);
  const manifest = assertRuntimePackageManifest(await readJsonFile(path.join(releaseDir, 'manifest.json')));
  const slices: Array<{ descriptor: RuntimeSliceDescriptor; data: unknown }> = [];
  const issues: ValidationIssue[] = [];
  let provenanceDescriptorCount = 0;

  for (const descriptor of manifest.descriptors) {
    const descriptorPath = path.join(releaseDir, descriptor.path);
    const descriptorValue = await readJsonFile<unknown>(descriptorPath).catch((error) => {
      issues.push(
        createIssue({
          path: relativeToOfflineRoot(paths, descriptorPath),
          code: 'runtime_v2_descriptor_file_missing',
          severity: 'error',
          actual: error instanceof Error ? error.message : String(error),
          expected: 'Existing descriptor file',
          fixHint: 'Regenerate v2 release so all manifest descriptors exist.',
          autoRepairable: false,
        })
      );
      return undefined;
    });
    if (descriptorValue === undefined) continue;

    issues.push(...validateDescriptorJsonIntegrity(descriptor, descriptorValue));
    if (descriptor.kind === 'slice') {
      slices.push({ descriptor, data: descriptorValue });
    } else if (descriptor.kind === 'provenance') {
      provenanceDescriptorCount += 1;
      issues.push(
        ...validateRuntimePackageProvenance(descriptorValue, {
          manifest,
          path: relativeToOfflineRoot(paths, descriptorPath),
        })
      );
    }
  }

  if (provenanceDescriptorCount === 0) {
    issues.push(
      createIssue({
        path: relativeToOfflineRoot(paths, path.join(releaseDir, 'manifest.json')),
        code: 'runtime_v2_provenance_descriptor_missing',
        severity: 'error',
        actual: 'missing',
        expected: 'Exactly one provenance descriptor',
        fixHint: 'Regenerate v2 release so manifest descriptors include provenance.json.',
        autoRepairable: false,
      })
    );
  } else if (provenanceDescriptorCount > 1) {
    issues.push(
      createIssue({
        path: relativeToOfflineRoot(paths, path.join(releaseDir, 'manifest.json')),
        code: 'runtime_v2_provenance_descriptor_duplicate',
        severity: 'error',
        actual: provenanceDescriptorCount,
        expected: 'Exactly one provenance descriptor',
        fixHint: 'Regenerate v2 release so manifest descriptors include only one provenance.json entry.',
        autoRepairable: false,
      })
    );
  }

  let scenarioPackage: CompiledDemoScenarioPackage | undefined;
  try {
    scenarioPackage = assembleScenarioPackageFromRelease({ manifest, slices });
  } catch (error) {
    issues.push(
      createIssue({
        path: relativeToOfflineRoot(paths, path.join(releaseDir, 'manifest.json')),
        code: 'runtime_v2_package_assembly_failed',
        severity: 'error',
        actual: error instanceof Error ? error.message : String(error),
        expected: 'Manifest slices assemble into a valid DemoScenarioPackage',
        fixHint: 'Regenerate v2 release so all required slices are present and ordered correctly.',
        autoRepairable: false,
      })
    );
  }

  return { manifest, scenarioPackage, issues };
}

export async function validateRuntimeRelease(
  paths: OfflineStaticTargetPaths,
  releaseId: string,
  options: { fromStaging?: boolean } = {}
): Promise<ToolEnvelope<OfflineStaticActivationResult>> {
  const contractBundle = await readOfflineStaticContract(paths);
  let loaded: Awaited<ReturnType<typeof loadRuntimeReleasePackage>>;
  try {
    loaded = await loadRuntimeReleasePackage(paths, releaseId, options);
  } catch (error) {
    return validationFailedEnvelope({
      paths,
      errors: [releaseLoadIssue(paths, releaseId, Boolean(options.fromStaging), error)],
    });
  }
  if (!loaded.scenarioPackage) {
    return validationFailedEnvelope({
      paths,
      manifest: loaded.manifest,
      errors: loaded.issues.filter((issue) => issue.severity === 'error'),
    });
  }
  const meta = createMetaFromManifest(loaded.manifest, {
    schemaValid: true,
    contractValid: true,
    invariantValid: true,
    issueCount: 0,
  });
  meta.packageSha256 = computePackageSha256(loaded.scenarioPackage);
  const schemaIssues = validateRuntimeScenarioPackage(
    loaded.scenarioPackage,
    contractBundle.scenarioSchema,
    contractBundle.contract
  );
  const contractIssues = validateRuntimeMeta(loaded.scenarioPackage, meta, contractBundle.contract);
  const invariantIssues = validateRuntimeInvariants(loaded.scenarioPackage);
  const validationSummary = summarizeRuntimeValidation(schemaIssues, contractIssues, invariantIssues);
  const retentionIssues = await inspectReleaseRetention(paths);
  const allIssues = [
    ...loaded.issues,
    ...schemaIssues,
    ...contractIssues,
    ...invariantIssues,
    ...retentionIssues,
  ];
  const errors = allIssues.filter((issue) => issue.severity === 'error');
  const warnings = allIssues.filter((issue) => issue.severity === 'warning');

  if (errors.length) {
    return validationFailedEnvelope({
      paths,
      manifest: loaded.manifest,
      scenarioPackage: loaded.scenarioPackage,
      errors,
    });
  }

  return okEnvelope(
    'Runtime v2 release validation succeeded.',
    {
      phase: 'published',
      targetKind: 'offline-static',
      packageFormat: 'v2',
      targetRoot: paths.targetRoot,
      releaseId,
      scenarioId: loaded.manifest.scenarioId,
      topicKey: loaded.manifest.scenarioId,
      seed: loaded.manifest.seed,
      contractFingerprint: loaded.manifest.contractFingerprint,
      scenarioFingerprint: loaded.manifest.scenarioFingerprint,
      domcRegistryFingerprint: loaded.manifest.domcRegistryFingerprint,
      moduleContractFingerprints: loaded.manifest.moduleContractFingerprints,
      adapterVersions: loaded.manifest.adapterVersions,
      manifestPath: relativeToOfflineRoot(
        paths,
        path.join(
          options.fromStaging ? stagingReleaseDirectoryPath(paths, releaseId) : releaseDirectoryPath(paths, releaseId),
          'manifest.json'
        )
      ),
      provenancePath: relativeToOfflineRoot(
        paths,
        path.join(
          options.fromStaging ? stagingReleaseDirectoryPath(paths, releaseId) : releaseDirectoryPath(paths, releaseId),
          'provenance.json'
        )
      ),
      validationSummary,
      paths: [],
    },
    warnings.length ? { errors: warnings } : {}
  );
}

export async function activateRuntimePackage(
  paths: OfflineStaticTargetPaths,
  options: { releaseId?: string } = {}
): Promise<ToolEnvelope<OfflineStaticActivationResult>> {
  const releaseId = options.releaseId ?? (await latestStagingReleaseId(paths));
  const stagingDir = stagingReleaseDirectoryPath(paths, releaseId);
  const finalDir = releaseDirectoryPath(paths, releaseId);

  if (!(await pathExists(stagingDir))) {
    throw new Error(`Staged v2 release "${releaseId}" does not exist.`);
  }

  if (await pathExists(finalDir)) {
    const issue = createIssue({
      path: relativeToOfflineRoot(paths, finalDir),
      code: 'runtime_v2_release_already_exists',
      severity: 'error',
      actual: releaseId,
      expected: 'A new immutable releaseId',
      fixHint: 'Choose a new releaseId; published releases are immutable and cannot be overwritten.',
      autoRepairable: false,
    });
    return validationFailedEnvelope({ paths, errors: [issue] });
  }

  const contractBundle = await readOfflineStaticContract(paths);
  let loaded: Awaited<ReturnType<typeof loadRuntimeReleasePackage>>;
  try {
    loaded = await loadRuntimeReleasePackage(paths, releaseId, { fromStaging: true });
  } catch (error) {
    await quarantineStagingRelease(paths, releaseId);
    await appendRuntimePackageTimeline(paths, {
      eventType: 'verified',
      releaseId,
      actor: 'mcp',
      result: 'error',
      summary: `Validation failed before loading v2 runtime release ${releaseId}.`,
    });
    return validationFailedEnvelope({
      paths,
      errors: [releaseLoadIssue(paths, releaseId, true, error)],
    });
  }
  if (!loaded.scenarioPackage) {
    const validationErrors = loaded.issues.filter((issue) => issue.severity === 'error');
    await quarantineStagingRelease(paths, releaseId);
    await appendRuntimePackageTimeline(paths, {
      eventType: 'verified',
      releaseId,
      actor: 'mcp',
      manifestSha256: loaded.manifest.rootSha256,
      result: 'error',
      summary: `Validation failed for v2 runtime release ${releaseId}.`,
    });
    return validationFailedEnvelope({
      paths,
      manifest: loaded.manifest,
      errors: validationErrors,
    });
  }
  const meta = createMetaFromManifest(loaded.manifest, {
    schemaValid: true,
    contractValid: true,
    invariantValid: true,
    issueCount: 0,
  });
  meta.packageSha256 = computePackageSha256(loaded.scenarioPackage);

  const schemaIssues = validateRuntimeScenarioPackage(
    loaded.scenarioPackage,
    contractBundle.scenarioSchema,
    contractBundle.contract
  );
  const contractIssues = validateRuntimeMeta(loaded.scenarioPackage, meta, contractBundle.contract);
  const invariantIssues = validateRuntimeInvariants(loaded.scenarioPackage);
  const validationSummary = summarizeRuntimeValidation(schemaIssues, contractIssues, invariantIssues);
  const validationErrors = [...loaded.issues, ...schemaIssues, ...contractIssues, ...invariantIssues].filter(
    (issue) => issue.severity === 'error'
  );

  if (validationErrors.length) {
    await quarantineStagingRelease(paths, releaseId);
    await appendRuntimePackageTimeline(paths, {
      eventType: 'verified',
      releaseId,
      actor: 'mcp',
      manifestSha256: loaded.manifest.rootSha256,
      result: 'error',
      summary: `Validation failed for v2 runtime release ${releaseId}.`,
    });
    return validationFailedEnvelope({
      paths,
      manifest: loaded.manifest,
      scenarioPackage: loaded.scenarioPackage,
      errors: validationErrors,
    });
  }

  const dryRun = await dryRunImportRuntimePackage(contractBundle.contract, loaded.scenarioPackage);
  if (!dryRun.ok || !dryRun.data) {
    const errors = dryRun.errors ?? [
      createIssue({
        path: 'indexeddb',
        code: 'runtime_import_dry_run_failed',
        severity: 'error',
        actual: 'unknown',
        expected: 'Successful dry-run',
        fixHint: 'Inspect dry-run logs and regenerate the v2 release.',
        autoRepairable: false,
      }),
    ];
    await quarantineStagingRelease(paths, releaseId);
    await appendRuntimePackageTimeline(paths, {
      eventType: 'verified',
      releaseId,
      actor: 'mcp',
      manifestSha256: loaded.manifest.rootSha256,
      result: 'error',
      summary: `Import dry-run failed for v2 runtime release ${releaseId}.`,
    });
    return errorEnvelope('Runtime v2 release dry-run failed; active pointer was not changed.', errors, {
      data: {
        phase: 'dry_run_failed',
        targetKind: 'offline-static',
        packageFormat: 'v2',
        targetRoot: paths.targetRoot,
        releaseId,
        scenarioId: loaded.manifest.scenarioId,
        topicKey: loaded.manifest.scenarioId,
        seed: loaded.manifest.seed,
        contractFingerprint: loaded.manifest.contractFingerprint,
        scenarioFingerprint: loaded.manifest.scenarioFingerprint,
        validationSummary,
        paths: [],
      },
    });
  }

  const verifiedTimelineWarning = await appendRuntimePackageTimeline(paths, {
    eventType: 'verified',
    releaseId,
    actor: 'mcp',
    manifestSha256: loaded.manifest.rootSha256,
    result: 'success',
    summary: `Verified v2 runtime release ${releaseId}.`,
  });

  await fs.mkdir(paths.releasesRoot, { recursive: true });
  await fs.rename(stagingDir, finalDir);

  const changedPaths: string[] = [];
  const activePointer = pointerForManifest(loaded.manifest);

  if (await pathExists(paths.activePointerPath)) {
    const currentPointer = assertRuntimePackagePointer(await readJsonFile(paths.activePointerPath));
    await writeJsonFile(paths, paths.previousPointerPath, currentPointer);
    changedPaths.push(RUNTIME_PACKAGE_V2_PREVIOUS_POINTER_PATH);
  }

  const activePointerTempPath = `${paths.activePointerPath}.tmp`;
  await writeJsonFile(paths, activePointerTempPath, activePointer);
  await fs.rename(activePointerTempPath, paths.activePointerPath);
  changedPaths.push(RUNTIME_PACKAGE_V2_ACTIVE_POINTER_PATH);

  const publishedManifestPath = path.join(finalDir, 'manifest.json');
  const publishedProvenancePath = path.join(finalDir, 'provenance.json');
  changedPaths.push(
    relativeToOfflineRoot(paths, publishedManifestPath),
    relativeToOfflineRoot(paths, publishedProvenancePath)
  );

  const activatedTimelineWarning = await appendRuntimePackageTimeline(paths, {
    eventType: 'activated',
    releaseId,
    actor: 'mcp',
    manifestSha256: loaded.manifest.rootSha256,
    result: 'success',
    summary: `Activated v2 runtime release ${releaseId}.`,
  });
  const warnings = [verifiedTimelineWarning, activatedTimelineWarning].filter(
    (warning): warning is ValidationIssue => Boolean(warning)
  );

  await appendOfflineStaticAudit(paths, {
    tool: 'offline_static_writer',
    phase: 'activated',
    packageFormat: 'v2',
    releaseId,
    scenarioId: loaded.manifest.scenarioId,
    seed: loaded.manifest.seed,
    contractFingerprint: loaded.manifest.contractFingerprint,
    manifestSha256: loaded.manifest.rootSha256,
    changedPaths,
    warnings: warnings.map((warning) => ({ code: warning.code, path: warning.path })),
  });

  const semanticReportDescriptor = loaded.manifest.descriptors.find(
    (descriptor) => descriptor.kind === 'artifact' && descriptor.path === 'semantic-report.json'
  );
  const semanticReportPath = semanticReportDescriptor
    ? relativeToOfflineRoot(paths, path.join(finalDir, semanticReportDescriptor.path))
    : undefined;

  const artifacts: DemoOfflineArtifact[] = changedPaths.map((changedPath) => ({
    kind: changedPath.endsWith('semantic-report.json') ? 'report' : 'file',
    label: changedPath,
    path: path.join(paths.targetRoot, changedPath),
  }));

  return okEnvelope(
    `Activated runtime v2 release ${releaseId}.`,
    {
      phase: 'activated',
      targetKind: 'offline-static',
      packageFormat: 'v2',
      targetRoot: paths.targetRoot,
      releaseId,
      scenarioId: loaded.manifest.scenarioId,
      topicKey: loaded.manifest.scenarioId,
      seed: loaded.manifest.seed,
      contractFingerprint: loaded.manifest.contractFingerprint,
      scenarioFingerprint: loaded.manifest.scenarioFingerprint,
      domcRegistryFingerprint: loaded.manifest.domcRegistryFingerprint,
      moduleContractFingerprints: loaded.manifest.moduleContractFingerprints,
      adapterVersions: loaded.manifest.adapterVersions,
      activePointerPath: RUNTIME_PACKAGE_V2_ACTIVE_POINTER_PATH,
      previousPointerPath: changedPaths.includes(RUNTIME_PACKAGE_V2_PREVIOUS_POINTER_PATH)
        ? RUNTIME_PACKAGE_V2_PREVIOUS_POINTER_PATH
        : undefined,
      manifestPath: relativeToOfflineRoot(paths, publishedManifestPath),
      provenancePath: relativeToOfflineRoot(paths, publishedProvenancePath),
      validationSummary,
      dryRunSummary: dryRun.data,
      semanticReportPath,
      paths: changedPaths,
    },
    {
      artifacts,
      ...(warnings.length ? { errors: warnings } : {}),
    }
  );
}
