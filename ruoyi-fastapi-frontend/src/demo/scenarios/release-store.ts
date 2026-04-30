import {
  DEMO_INDEXED_DB_MAPPING,
  DEMO_OFFLINE_GENERATOR_ADAPTER_VERSION,
  type DemoIndexedDbTableMapping,
  type DemoScenarioModule,
  type RuntimeValidationSummary,
} from './contract';
import {
  canonicalJson,
  computeDemoScenarioFingerprint,
  sha256CanonicalJson,
} from './fingerprint';
import { validateDemoScenarioPackage, type DemoScenarioPackage } from './schema';

export const DEMO_SCENARIOS_ROOT_PATH = 'demo-scenarios';
export const RUNTIME_PACKAGE_V2_RELEASES_ROOT_PATH = 'demo-scenarios/releases';
export const RUNTIME_PACKAGE_V2_STAGING_ROOT_PATH = 'demo-scenarios/releases/.staging';
export const RUNTIME_PACKAGE_V2_FAILED_ROOT_PATH = 'demo-scenarios/releases/.failed';
export const RUNTIME_PACKAGE_V2_ACTIVE_POINTER_PATH = 'demo-scenarios/active.pointer.json';
export const RUNTIME_PACKAGE_V2_PREVIOUS_POINTER_PATH = 'demo-scenarios/previous.pointer.json';
export const RUNTIME_PACKAGE_V2_TIMELINE_PATH = 'demo-scenarios/timeline.json';
export const RUNTIME_PACKAGE_V2_BUNDLE_DEFAULT_RELEASE_ID = 'bundle-default';
export const RUNTIME_PACKAGE_V2_BUNDLE_DEFAULT_MANIFEST_PATH =
  'demo-scenarios/releases/bundle-default/manifest.json';

export const RUNTIME_PACKAGE_V2_SLICE_MEDIA_TYPE =
  'application/vnd.ruoyi.demo.slice+json;version=2';
export const RUNTIME_PACKAGE_V2_PROVENANCE_MEDIA_TYPE =
  'application/vnd.ruoyi.demo.provenance+json;version=1';
export const RUNTIME_PACKAGE_V2_SEMANTIC_REPORT_MEDIA_TYPE =
  'application/vnd.ruoyi.demo.semantic-report+json;version=1';
export const RUNTIME_PACKAGE_V2_MAX_SLICE_RECORDS = 2000;
export const RUNTIME_PACKAGE_V2_MAX_SLICE_BYTES = 200 * 1024;

export type RuntimePackageV2Source =
  | 'runtime-active-v2'
  | 'runtime-previous-v2'
  | 'bundle-default-v2';

export type RuntimePackageV2LoadStage =
  | 'fetch'
  | 'parse'
  | 'pointer'
  | 'manifest'
  | 'descriptor'
  | 'hash'
  | 'schema'
  | 'contract'
  | 'import';

export type RuntimePackageV2DescriptorKind =
  | 'slice'
  | 'artifact'
  | 'provenance'
  | 'blueprint'
  | 'scenario-graph'
  | 'recipe';

export type RuntimePackageV2MaterializationReason =
  | 'copied-default'
  | 'semantic-generated'
  | 'runtime-required'
  | 'reviewability'
  | 'recipe-not-yet-supported';

export interface RuntimePackagePointer {
  formatVersion: 2;
  releaseId: string;
  manifestPath: string;
  manifestSha256: string;
  activatedAt: string;
  contractFingerprint: string;
  scenarioFingerprint: string;
}

export interface RuntimeDescriptorBase {
  kind: RuntimePackageV2DescriptorKind;
  name: string;
  mediaType: string;
  path: string;
  sha256: string;
  sizeBytes: number;
  schemaVersion: 1;
}

export interface RuntimeSliceDescriptor extends RuntimeDescriptorBase {
  kind: 'slice';
  mediaType: typeof RUNTIME_PACKAGE_V2_SLICE_MEDIA_TYPE;
  sourcePath: string;
  module: DemoScenarioModule;
  recordCount: number;
  materializationReason: RuntimePackageV2MaterializationReason;
  order?: number;
  shardIndex?: number;
  shardCount?: number;
}

export interface RuntimeArtifactDescriptor extends RuntimeDescriptorBase {
  kind: 'artifact';
  artifactType?: 'semantic-report' | 'quality-report' | 'blueprint' | 'other';
}

export interface RuntimeProvenanceDescriptor extends RuntimeDescriptorBase {
  kind: 'provenance';
  mediaType: typeof RUNTIME_PACKAGE_V2_PROVENANCE_MEDIA_TYPE;
}

export interface RuntimeFutureDescriptor extends RuntimeDescriptorBase {
  kind: 'blueprint' | 'scenario-graph' | 'recipe';
}

export type RuntimePackageDescriptor =
  | RuntimeSliceDescriptor
  | RuntimeArtifactDescriptor
  | RuntimeProvenanceDescriptor
  | RuntimeFutureDescriptor;

export interface RuntimePackageV2Manifest {
  formatVersion: 2;
  releaseId: string;
  scenarioId: string;
  scenarioName: string;
  scenarioVersion: string;
  schemaVersion: 1;
  contractFingerprint: string;
  generatorVersion: string;
  seed: string;
  generatedAt: string;
  scenarioFingerprint: string;
  domcRegistryFingerprint?: string;
  moduleContractFingerprints?: Record<string, string>;
  adapterVersions?: Record<string, string>;
  adapterCapabilitySummary?: Array<{
    moduleId: string;
    adapterId: string;
    adapterVersion: string;
    outputSourcePaths: readonly string[];
  }>;
  rootSha256: string;
  descriptors: RuntimePackageDescriptor[];
}

export interface RuntimePackageV2Provenance {
  formatVersion: 1;
  releaseId: string;
  scenarioId: string;
  topicKey: string;
  topicSummary: string;
  businessDescriptionSha256?: string;
  seed: string;
  contractFingerprint: string;
  generatorVersion: string;
  semanticGeneratorVersion?: string;
  semanticReportSha256?: string;
  generatedAt: string;
  validationSummary: RuntimeValidationSummary;
  domcRegistryFingerprint?: string;
  moduleContractFingerprints?: Record<string, string>;
  adapterVersions?: Record<string, string>;
  adapterCapabilitySummary?: Array<{
    moduleId: string;
    adapterId: string;
    adapterVersion: string;
    outputSourcePaths: readonly string[];
  }>;
  materials: Array<{
    kind:
      | 'demo-contract'
      | 'default-scenario'
      | 'semantic-report'
      | 'generator'
      | 'domc-registry'
      | 'domc-module-contract'
      | 'generator-adapter';
    name: string;
    sha256?: string;
  }>;
}

export interface RuntimePackageTimelineEvent {
  eventId: string;
  eventType: 'staged' | 'verified' | 'activated' | 'rolled_back' | 'gc_warning';
  releaseId: string;
  time: string;
  actor: 'mcp' | 'build' | 'manual';
  manifestSha256?: string;
  result: 'success' | 'warning' | 'error';
  summary: string;
}

export interface RuntimePackageSliceFile {
  descriptor: RuntimeSliceDescriptor;
  data: unknown[];
}

export interface RuntimePackageSliceMaterialization {
  sourcePath: string;
  module: DemoScenarioModule;
  name: string;
  path: string;
  data: unknown[];
  order: number;
  materializationReason: RuntimePackageV2MaterializationReason;
  shardIndex?: number;
  shardCount?: number;
}

export interface RuntimePackageV2ReleaseFiles {
  manifest: RuntimePackageV2Manifest;
  pointer: RuntimePackagePointer;
  provenance: RuntimePackageV2Provenance;
  slices: RuntimePackageSliceFile[];
}

export interface CreateRuntimePackageV2ReleaseOptions {
  releaseId: string;
  scenarioPackage: DemoScenarioPackage;
  contractFingerprint: string;
  generatorVersion?: string;
  generatedAt: string;
  activatedAt?: string;
  topicKey?: string;
  topicSummary?: string;
  seed?: string;
  validationSummary?: RuntimeValidationSummary;
  materializationReason?: RuntimePackageV2MaterializationReason;
  materializationReasonsBySourcePath?: Partial<
    Record<string, RuntimePackageV2MaterializationReason>
  >;
  tableMappings?: readonly DemoIndexedDbTableMapping[];
  domcRegistryFingerprint?: string;
  moduleContractFingerprints?: Record<string, string>;
  adapterVersions?: Record<string, string>;
  adapterCapabilitySummary?: Array<{
    moduleId: string;
    adapterId: string;
    adapterVersion: string;
    outputSourcePaths: readonly string[];
  }>;
}

const RELEASE_ID_PATTERN = /^[a-z0-9][a-z0-9._-]{1,79}$/;
const URL_OR_SCHEME_PATTERN = /^[a-z][a-z0-9+.-]*:/i;
const SHA256_HEX_PATTERN = /^[a-f0-9]{64}$/;
const RUNTIME_PACKAGE_DESCRIPTOR_KINDS = new Set<RuntimePackageV2DescriptorKind>([
  'slice',
  'artifact',
  'provenance',
  'blueprint',
  'scenario-graph',
  'recipe',
]);
const RUNTIME_PACKAGE_MATERIALIZATION_REASONS = new Set<RuntimePackageV2MaterializationReason>([
  'copied-default',
  'semantic-generated',
  'runtime-required',
  'reviewability',
  'recipe-not-yet-supported',
]);
const RUNTIME_PACKAGE_MODULES = new Set<DemoScenarioModule>([
  'auth',
  'system',
  'project',
  'simulation',
]);
const RUNTIME_PACKAGE_ARTIFACT_TYPES = new Set<NonNullable<RuntimeArtifactDescriptor['artifactType']>>([
  'semantic-report',
  'quality-report',
  'blueprint',
  'other',
]);
const RUNTIME_PACKAGE_PROVENANCE_MATERIAL_KINDS = new Set<
  RuntimePackageV2Provenance['materials'][number]['kind']
>([
  'demo-contract',
  'default-scenario',
  'semantic-report',
  'generator',
  'domc-registry',
  'domc-module-contract',
  'generator-adapter',
]);

function isPlainObject(value: unknown): value is Record<string, unknown> {
  return Object.prototype.toString.call(value) === '[object Object]';
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
    const existing = current[segment];
    if (!isPlainObject(existing)) {
      current[segment] = {};
    }
    current = current[segment] as Record<string, unknown>;
  });

  current[segments[segments.length - 1]] = value;
}

function normalizeRuntimePath(pathValue: string): string {
  return pathValue.replace(/\\/g, '/').replace(/^\.\/+/, '');
}

function assertSafeRelativeRuntimePath(pathValue: string, label: string): string {
  const normalized = normalizeRuntimePath(pathValue.trim());

  if (!normalized) {
    throw new Error(`${label} is required.`);
  }

  if (normalized.startsWith('/') || normalized.startsWith('//') || URL_OR_SCHEME_PATTERN.test(normalized)) {
    throw new Error(`${label} must be a relative local path.`);
  }

  if (normalized.split('/').some((segment) => !segment || segment === '.' || segment === '..')) {
    throw new Error(`${label} cannot contain empty, "." or ".." path segments.`);
  }

  return normalized;
}

function moduleFromSourcePath(sourcePath: string): DemoScenarioModule {
  const moduleName = sourcePath.split('.')[0];
  if (!RUNTIME_PACKAGE_MODULES.has(moduleName as DemoScenarioModule)) {
    throw new Error(`Unsupported release slice module "${moduleName}" for ${sourcePath}.`);
  }

  return moduleName as DemoScenarioModule;
}

function assertNonEmptyString(value: unknown, pathName: string): string {
  if (typeof value !== 'string' || !value.trim()) {
    throw new Error(`${pathName} is required.`);
  }

  return value;
}

function assertSafeInteger(value: unknown, pathName: string, min = 0): number {
  if (!Number.isSafeInteger(value) || Number(value) < min) {
    throw new Error(`${pathName} must be an integer >= ${min}.`);
  }

  return Number(value);
}

function assertOptionalSha256(value: unknown, pathName: string): string | undefined {
  if (value === undefined) return undefined;
  if (typeof value !== 'string') {
    throw new Error(`${pathName} must be a SHA-256 hex string when provided.`);
  }
  return assertSha256Hex(value, pathName);
}

function assertRuntimeValidationSummary(value: unknown, pathName: string): RuntimeValidationSummary {
  if (!isPlainObject(value)) {
    throw new Error(`${pathName} must be a JSON object.`);
  }

  const summary = value as Partial<RuntimeValidationSummary>;
  (['schemaValid', 'contractValid', 'invariantValid'] as const).forEach((field) => {
    if (typeof summary[field] !== 'boolean') {
      throw new Error(`${pathName}.${field} must be boolean.`);
    }
  });
  if (summary.dryRunValid !== undefined && typeof summary.dryRunValid !== 'boolean') {
    throw new Error(`${pathName}.dryRunValid must be boolean when provided.`);
  }
  assertSafeInteger(summary.issueCount, `${pathName}.issueCount`);

  return summary as RuntimeValidationSummary;
}

function emptyScenarioPackage(manifest: RuntimePackageV2Manifest): DemoScenarioPackage {
  return {
    schemaVersion: manifest.schemaVersion,
    scenario: {
      id: manifest.scenarioId,
      name: manifest.scenarioName,
      version: manifest.scenarioVersion,
      fingerprint: manifest.scenarioFingerprint,
      seed: manifest.seed,
    },
    auth: {
      accounts: [],
      roles: [],
      permissions: [],
    },
    system: {
      menus: [],
      dictTypes: [],
      dicts: [],
      departments: [],
      posts: [],
      users: [],
    },
    project: {
      projects: [],
      versions: [],
      topologies: [],
    },
    simulation: {
      sessions: [],
      messages: [],
      bandwidth: [],
      alarms: [],
      faults: [],
      events: [],
      streamFrames: [],
    },
  };
}

export function canonicalJsonSizeBytes(value: unknown): number {
  return new TextEncoder().encode(canonicalJson(value)).byteLength;
}

export function createManifestRootHashInput(
  manifest: RuntimePackageV2Manifest
): Omit<RuntimePackageV2Manifest, 'rootSha256'> {
  const { rootSha256: _rootSha256, ...hashInput } = manifest;
  return hashInput;
}

export async function computeManifestRootSha256(
  manifest: RuntimePackageV2Manifest
): Promise<string> {
  return sha256CanonicalJson(createManifestRootHashInput(manifest));
}

export async function createDescriptorForJson(input: {
  kind: 'slice';
  name: string;
  path: string;
  sourcePath: string;
  module: DemoScenarioModule;
  data: unknown[];
  materializationReason: RuntimePackageV2MaterializationReason;
  order: number;
  shardIndex?: number;
  shardCount?: number;
}): Promise<RuntimeSliceDescriptor>;
export async function createDescriptorForJson(input: {
  kind: 'provenance';
  name: string;
  path: string;
  data: unknown;
}): Promise<RuntimeProvenanceDescriptor>;
export async function createDescriptorForJson(input: {
  kind: 'artifact';
  name: string;
  path: string;
  mediaType: string;
  data: unknown;
  artifactType?: RuntimeArtifactDescriptor['artifactType'];
}): Promise<RuntimeArtifactDescriptor>;
export async function createDescriptorForJson(input: {
  kind: 'slice' | 'artifact' | 'provenance';
  name: string;
  path: string;
  data: unknown;
  mediaType?: string;
  sourcePath?: string;
  module?: DemoScenarioModule;
  materializationReason?: RuntimePackageV2MaterializationReason;
  order?: number;
  shardIndex?: number;
  shardCount?: number;
  artifactType?: RuntimeArtifactDescriptor['artifactType'];
}): Promise<RuntimeSliceDescriptor | RuntimeArtifactDescriptor | RuntimeProvenanceDescriptor> {
  const pathValue = assertRuntimePackageDescriptorPath(input.path);
  const base = {
    kind: input.kind,
    name: input.name,
    path: pathValue,
    sha256: await sha256CanonicalJson(input.data),
    sizeBytes: canonicalJsonSizeBytes(input.data),
    schemaVersion: 1 as const,
  };

  if (input.kind === 'slice') {
    const data = Array.isArray(input.data) ? input.data : [];
    if (!input.sourcePath || !input.module || !input.materializationReason || input.order === undefined) {
      throw new Error(`Slice descriptor ${input.name} is missing required metadata.`);
    }

    return {
      ...base,
      kind: 'slice',
      mediaType: RUNTIME_PACKAGE_V2_SLICE_MEDIA_TYPE,
      sourcePath: input.sourcePath,
      module: input.module,
      recordCount: data.length,
      materializationReason: input.materializationReason,
      order: input.order,
      ...(input.shardIndex !== undefined ? { shardIndex: input.shardIndex } : {}),
      ...(input.shardCount !== undefined ? { shardCount: input.shardCount } : {}),
    };
  }

  if (input.kind === 'provenance') {
    return {
      ...base,
      kind: 'provenance',
      mediaType: RUNTIME_PACKAGE_V2_PROVENANCE_MEDIA_TYPE,
    };
  }

  return {
    ...base,
    kind: 'artifact',
    mediaType: input.mediaType ?? 'application/json',
    artifactType: input.artifactType,
  };
}

export function assertRuntimePackageReleaseId(releaseId: string): string {
  const normalized = releaseId.trim();
  if (normalized !== RUNTIME_PACKAGE_V2_BUNDLE_DEFAULT_RELEASE_ID && !RELEASE_ID_PATTERN.test(normalized)) {
    throw new Error(
      `Invalid runtime package releaseId "${releaseId}". Use lowercase letters, digits, dots, underscores or hyphens.`
    );
  }

  return normalized;
}

export function manifestPathForReleaseId(releaseId: string): string {
  return `${RUNTIME_PACKAGE_V2_RELEASES_ROOT_PATH}/${assertRuntimePackageReleaseId(releaseId)}/manifest.json`;
}

export function assertRuntimePackageManifestPath(releaseId: string, manifestPath: string): string {
  const expected = manifestPathForReleaseId(releaseId);
  const normalized = assertSafeRelativeRuntimePath(manifestPath, 'manifestPath');

  if (normalized !== expected) {
    throw new Error(`manifestPath must be "${expected}".`);
  }

  return normalized;
}

export function assertRuntimePackageDescriptorPath(descriptorPath: string): string {
  const normalized = assertSafeRelativeRuntimePath(descriptorPath, 'descriptor.path');

  if (normalized.startsWith(`${DEMO_SCENARIOS_ROOT_PATH}/`)) {
    throw new Error('descriptor.path must be relative to the release directory.');
  }

  return normalized;
}

export function releaseAssetPath(releaseId: string, descriptorPath: string): string {
  return `${RUNTIME_PACKAGE_V2_RELEASES_ROOT_PATH}/${assertRuntimePackageReleaseId(
    releaseId
  )}/${assertRuntimePackageDescriptorPath(descriptorPath)}`;
}

export function assertSha256Hex(value: string, label: string): string {
  if (!SHA256_HEX_PATTERN.test(value)) {
    throw new Error(`${label} must be a lowercase SHA-256 hex string.`);
  }

  return value;
}

export function assertRuntimePackagePointer(value: unknown): RuntimePackagePointer {
  if (!isPlainObject(value)) {
    throw new Error('Runtime package pointer must be a JSON object.');
  }

  const pointer = value as Partial<RuntimePackagePointer>;

  if (pointer.formatVersion !== 2) {
    throw new Error(`Runtime package pointer formatVersion "${pointer.formatVersion}" is not supported.`);
  }

  if (typeof pointer.releaseId !== 'string') {
    throw new Error('Runtime package pointer releaseId is required.');
  }

  const releaseId = assertRuntimePackageReleaseId(pointer.releaseId);

  if (typeof pointer.manifestPath !== 'string') {
    throw new Error('Runtime package pointer manifestPath is required.');
  }

  assertRuntimePackageManifestPath(releaseId, pointer.manifestPath);

  (['manifestSha256', 'contractFingerprint', 'scenarioFingerprint'] as const).forEach((field) => {
    if (typeof pointer[field] !== 'string') {
      throw new Error(`Runtime package pointer ${field} is required.`);
    }
    assertSha256Hex(pointer[field] as string, `pointer.${field}`);
  });

  if (typeof pointer.activatedAt !== 'string' || !pointer.activatedAt.trim()) {
    throw new Error('Runtime package pointer activatedAt is required.');
  }

  return pointer as RuntimePackagePointer;
}

export async function assertRuntimePackageManifest(
  value: unknown,
  options: { releaseId?: string; contractFingerprint?: string } = {}
): Promise<RuntimePackageV2Manifest> {
  if (!isPlainObject(value)) {
    throw new Error('Runtime package manifest must be a JSON object.');
  }

  const manifest = value as Partial<RuntimePackageV2Manifest>;

  if (manifest.formatVersion !== 2) {
    throw new Error(`Runtime package manifest formatVersion "${manifest.formatVersion}" is not supported.`);
  }

  if (typeof manifest.releaseId !== 'string') {
    throw new Error('Runtime package manifest releaseId is required.');
  }

  const releaseId = assertRuntimePackageReleaseId(manifest.releaseId);
  if (options.releaseId && releaseId !== options.releaseId) {
    throw new Error(`Runtime package manifest releaseId "${releaseId}" does not match pointer releaseId "${options.releaseId}".`);
  }

  (
    [
      'scenarioId',
      'scenarioName',
      'scenarioVersion',
      'contractFingerprint',
      'generatorVersion',
      'seed',
      'generatedAt',
      'scenarioFingerprint',
      'rootSha256',
    ] as const
  ).forEach((field) => {
    if (typeof manifest[field] !== 'string' || !String(manifest[field]).trim()) {
      throw new Error(`Runtime package manifest ${field} is required.`);
    }
  });

  if (manifest.schemaVersion !== 1) {
    throw new Error(`Runtime package manifest schemaVersion "${manifest.schemaVersion}" is not supported.`);
  }

  if (options.contractFingerprint && manifest.contractFingerprint !== options.contractFingerprint) {
    throw new Error('Runtime package manifest contractFingerprint does not match the current demo-offline shell.');
  }

  if (!Array.isArray(manifest.descriptors)) {
    throw new Error('Runtime package manifest descriptors must be an array.');
  }

  manifest.descriptors.forEach((descriptor, index) => {
    assertRuntimePackageDescriptor(descriptor, `descriptors[${index}]`);
  });

  assertSha256Hex(manifest.rootSha256 as string, 'manifest.rootSha256');

  const actualRootSha256 = await computeManifestRootSha256(manifest as RuntimePackageV2Manifest);
  if (manifest.rootSha256 !== actualRootSha256) {
    throw new Error('Runtime package manifest rootSha256 does not match manifest content.');
  }

  return manifest as RuntimePackageV2Manifest;
}

export function assertRuntimePackageDescriptor(
  value: unknown,
  path = 'descriptor'
): RuntimePackageDescriptor {
  if (!isPlainObject(value)) {
    throw new Error(`${path} must be a JSON object.`);
  }

  const descriptor = value as Partial<RuntimePackageDescriptor>;
  if (typeof descriptor.kind !== 'string' || !descriptor.kind.trim()) {
    throw new Error(`${path}.kind is required.`);
  }
  if (!RUNTIME_PACKAGE_DESCRIPTOR_KINDS.has(descriptor.kind as RuntimePackageV2DescriptorKind)) {
    throw new Error(`${path}.kind "${descriptor.kind}" is not supported.`);
  }

  if (typeof descriptor.name !== 'string' || !descriptor.name.trim()) {
    throw new Error(`${path}.name is required.`);
  }

  if (typeof descriptor.mediaType !== 'string' || !descriptor.mediaType.trim()) {
    throw new Error(`${path}.mediaType is required.`);
  }

  if (typeof descriptor.path !== 'string') {
    throw new Error(`${path}.path is required.`);
  }
  assertRuntimePackageDescriptorPath(descriptor.path);

  if (typeof descriptor.sha256 !== 'string') {
    throw new Error(`${path}.sha256 is required.`);
  }
  assertSha256Hex(descriptor.sha256, `${path}.sha256`);

  if (!Number.isSafeInteger(descriptor.sizeBytes) || Number(descriptor.sizeBytes) < 0) {
    throw new Error(`${path}.sizeBytes must be a non-negative integer.`);
  }

  if (descriptor.schemaVersion !== 1) {
    throw new Error(`${path}.schemaVersion "${descriptor.schemaVersion}" is not supported.`);
  }

  if (descriptor.kind === 'slice') {
    const slice = descriptor as Partial<RuntimeSliceDescriptor>;
    if (slice.mediaType !== RUNTIME_PACKAGE_V2_SLICE_MEDIA_TYPE) {
      throw new Error(`${path}.mediaType is not a supported slice mediaType.`);
    }
    if (typeof slice.sourcePath !== 'string' || !slice.sourcePath.trim()) {
      throw new Error(`${path}.sourcePath is required.`);
    }
    const expectedModule = moduleFromSourcePath(slice.sourcePath);
    if (typeof slice.module !== 'string' || !RUNTIME_PACKAGE_MODULES.has(slice.module as DemoScenarioModule)) {
      throw new Error(`${path}.module is required.`);
    }
    if (slice.module !== expectedModule) {
      throw new Error(`${path}.module must match sourcePath module "${expectedModule}".`);
    }
    if (!Number.isSafeInteger(slice.recordCount) || Number(slice.recordCount) < 0) {
      throw new Error(`${path}.recordCount must be a non-negative integer.`);
    }
    if (
      typeof slice.materializationReason !== 'string' ||
      !RUNTIME_PACKAGE_MATERIALIZATION_REASONS.has(slice.materializationReason as RuntimePackageV2MaterializationReason)
    ) {
      throw new Error(`${path}.materializationReason is required.`);
    }
    assertSafeInteger(slice.order, `${path}.order`);
    const hasShardIndex = slice.shardIndex !== undefined;
    const hasShardCount = slice.shardCount !== undefined;
    if (hasShardIndex !== hasShardCount) {
      throw new Error(`${path}.shardIndex and ${path}.shardCount must be provided together.`);
    }
    if (hasShardIndex && hasShardCount) {
      const shardIndex = assertSafeInteger(slice.shardIndex, `${path}.shardIndex`);
      const shardCount = assertSafeInteger(slice.shardCount, `${path}.shardCount`, 1);
      if (shardIndex >= shardCount) {
        throw new Error(`${path}.shardIndex must be less than shardCount.`);
      }
    }
  } else if (descriptor.kind === 'provenance') {
    if (descriptor.mediaType !== RUNTIME_PACKAGE_V2_PROVENANCE_MEDIA_TYPE) {
      throw new Error(`${path}.mediaType is not a supported provenance mediaType.`);
    }
  } else if (descriptor.kind === 'artifact') {
    const artifact = descriptor as Partial<RuntimeArtifactDescriptor>;
    if (
      artifact.artifactType !== undefined &&
      !RUNTIME_PACKAGE_ARTIFACT_TYPES.has(artifact.artifactType)
    ) {
      throw new Error(`${path}.artifactType "${artifact.artifactType}" is not supported.`);
    }
  }

  return descriptor as RuntimePackageDescriptor;
}

export async function assertDescriptorJsonIntegrity(
  descriptor: RuntimePackageDescriptor,
  value: unknown
): Promise<void> {
  const actualSha256 = await sha256CanonicalJson(value);
  const actualSizeBytes = canonicalJsonSizeBytes(value);

  if (descriptor.sha256 !== actualSha256) {
    throw new Error(`Descriptor ${descriptor.name} sha256 does not match ${descriptor.path}.`);
  }

  if (descriptor.sizeBytes !== actualSizeBytes) {
    throw new Error(`Descriptor ${descriptor.name} sizeBytes does not match ${descriptor.path}.`);
  }

  if (descriptor.kind === 'slice') {
    if (!Array.isArray(value)) {
      throw new Error(`Descriptor ${descriptor.name} must point to a JSON array slice.`);
    }
    if (descriptor.recordCount !== value.length) {
      throw new Error(`Descriptor ${descriptor.name} recordCount does not match ${descriptor.path}.`);
    }
  }
}

export function splitScenarioPackageToSlices(
  scenarioPackage: DemoScenarioPackage,
  options: {
    materializationReason?: RuntimePackageV2MaterializationReason;
    materializationReasonsBySourcePath?: Partial<
      Record<string, RuntimePackageV2MaterializationReason>
    >;
    tableMappings?: readonly DemoIndexedDbTableMapping[];
  } = {}
): RuntimePackageSliceMaterialization[] {
  const validPackage = validateDemoScenarioPackage(scenarioPackage);
  const materializedSourcePaths = new Set<string>();
  const tableMappings = options.tableMappings ?? DEMO_INDEXED_DB_MAPPING.tables;

  return tableMappings.flatMap((mapping, index) => {
    if (materializedSourcePaths.has(mapping.sourcePath)) {
      throw new Error(`Duplicate release slice sourcePath "${mapping.sourcePath}".`);
    }
    materializedSourcePaths.add(mapping.sourcePath);

    const data = getPath(validPackage, mapping.sourcePath);
    if (!Array.isArray(data)) {
      throw new Error(`Release slice ${mapping.sourcePath} must resolve to an array.`);
    }

    const minItems = 'minItems' in mapping ? (mapping.minItems ?? 0) : 0;
    if (minItems > 0 && data.length < minItems) {
      throw new Error(`Release slice ${mapping.sourcePath} does not satisfy minItems ${minItems}.`);
    }

    const module = moduleFromSourcePath(mapping.sourcePath);
    const shards = splitDataIntoReviewableShards(data);
    const shardCount = shards.length;
    const baseOrder = (index + 1) * 100000;
    const materializationReason =
      options.materializationReasonsBySourcePath?.[mapping.sourcePath] ??
      options.materializationReason ??
      'runtime-required';

    return shards.map((shard, shardIndex) => ({
      sourcePath: mapping.sourcePath,
      module,
      name: shardCount === 1 ? mapping.sourcePath : `${mapping.sourcePath}#${shardIndex + 1}`,
      path:
        shardCount === 1
          ? `slices/${mapping.sourcePath}.json`
          : `slices/${mapping.sourcePath}.part-${String(shardIndex + 1).padStart(3, '0')}.json`,
      data: shard,
      order: baseOrder + shardIndex,
      materializationReason,
      ...(shardCount > 1 ? { shardIndex, shardCount } : {}),
    }));
  });
}

function splitDataIntoReviewableShards(data: unknown[]): unknown[][] {
  const shards: unknown[][] = [];
  let current: unknown[] = [];

  for (const record of data) {
    const candidate = [...current, record];
    const exceedsRecordLimit = candidate.length > RUNTIME_PACKAGE_V2_MAX_SLICE_RECORDS;
    const exceedsByteLimit =
      current.length > 0 && canonicalJsonSizeBytes(candidate) > RUNTIME_PACKAGE_V2_MAX_SLICE_BYTES;

    if (exceedsRecordLimit || exceedsByteLimit) {
      shards.push(current);
      current = [record];
    } else {
      current = candidate;
    }
  }

  if (current.length || data.length === 0) {
    shards.push(current);
  }

  return shards;
}

export async function createRuntimePackageV2Release(
  options: CreateRuntimePackageV2ReleaseOptions
): Promise<RuntimePackageV2ReleaseFiles> {
  const scenarioPackage = validateDemoScenarioPackage(options.scenarioPackage);
  const releaseId = assertRuntimePackageReleaseId(options.releaseId);
  const seed = options.seed ?? scenarioPackage.scenario.seed ?? 'ruoyi-demo-offline-default';
  const validationSummary = options.validationSummary ?? {
    schemaValid: true,
    contractValid: true,
    invariantValid: true,
    dryRunValid: true,
    issueCount: 0,
  };
  const slices = await Promise.all(
    splitScenarioPackageToSlices(scenarioPackage, options).map(async (slice) => {
      const descriptor = await createDescriptorForJson({
        kind: 'slice',
        name: slice.name,
        path: slice.path,
        sourcePath: slice.sourcePath,
        module: slice.module,
        data: slice.data,
        materializationReason: slice.materializationReason,
        order: slice.order,
        shardIndex: slice.shardIndex,
        shardCount: slice.shardCount,
      });

      return {
        descriptor,
        data: slice.data,
      };
    })
  );
  const scenarioFingerprint = await computeDemoScenarioFingerprint(scenarioPackage);
  const provenance: RuntimePackageV2Provenance = {
    formatVersion: 1,
    releaseId,
    scenarioId: scenarioPackage.scenario.id,
    topicKey: options.topicKey ?? scenarioPackage.scenario.id,
    topicSummary: options.topicSummary ?? scenarioPackage.scenario.name,
    seed,
    contractFingerprint: options.contractFingerprint,
    generatorVersion: options.generatorVersion ?? DEMO_OFFLINE_GENERATOR_ADAPTER_VERSION,
    generatedAt: options.generatedAt,
    validationSummary,
    domcRegistryFingerprint: options.domcRegistryFingerprint,
    moduleContractFingerprints: options.moduleContractFingerprints,
    adapterVersions: options.adapterVersions,
    adapterCapabilitySummary: options.adapterCapabilitySummary,
    materials: [
      {
        kind: 'demo-contract',
        name: 'demo-contract/contract.json',
        sha256: options.contractFingerprint,
      },
      ...(options.domcRegistryFingerprint
        ? [
            {
              kind: 'domc-registry' as const,
              name: 'demo-contract/domc.registry.json',
              sha256: options.domcRegistryFingerprint,
            },
          ]
        : []),
      ...Object.entries(options.moduleContractFingerprints ?? {}).map(([moduleId, sha256]) => ({
        kind: 'domc-module-contract' as const,
        name: `domc.modules.${moduleId}`,
        sha256,
      })),
      ...Object.entries(options.adapterVersions ?? {}).map(([adapterId, version]) => ({
        kind: 'generator-adapter' as const,
        name: `${adapterId}@${version}`,
      })),
      {
        kind: 'default-scenario',
        name: 'demo-contract/default-scenario.json',
      },
      {
        kind: 'generator',
        name: options.generatorVersion ?? DEMO_OFFLINE_GENERATOR_ADAPTER_VERSION,
      },
    ],
  };
  const provenanceDescriptor = await createDescriptorForJson({
    kind: 'provenance',
    name: 'provenance',
    path: 'provenance.json',
    data: provenance,
  });
  const manifestWithoutRoot: RuntimePackageV2Manifest = {
    formatVersion: 2,
    releaseId,
    scenarioId: scenarioPackage.scenario.id,
    scenarioName: scenarioPackage.scenario.name,
    scenarioVersion: scenarioPackage.scenario.version,
    schemaVersion: scenarioPackage.schemaVersion,
    contractFingerprint: options.contractFingerprint,
    generatorVersion: options.generatorVersion ?? DEMO_OFFLINE_GENERATOR_ADAPTER_VERSION,
    seed,
    generatedAt: options.generatedAt,
    scenarioFingerprint,
    domcRegistryFingerprint: options.domcRegistryFingerprint,
    moduleContractFingerprints: options.moduleContractFingerprints,
    adapterVersions: options.adapterVersions,
    adapterCapabilitySummary: options.adapterCapabilitySummary,
    rootSha256: '',
    descriptors: [...slices.map((slice) => slice.descriptor), provenanceDescriptor],
  };
  const manifest: RuntimePackageV2Manifest = {
    ...manifestWithoutRoot,
    rootSha256: await computeManifestRootSha256(manifestWithoutRoot),
  };
  const pointer: RuntimePackagePointer = {
    formatVersion: 2,
    releaseId,
    manifestPath: manifestPathForReleaseId(releaseId),
    manifestSha256: manifest.rootSha256,
    activatedAt: options.activatedAt ?? options.generatedAt,
    contractFingerprint: options.contractFingerprint,
    scenarioFingerprint,
  };

  return {
    manifest,
    pointer,
    provenance,
    slices,
  };
}

export async function assembleScenarioPackageFromRelease(input: {
  manifest: RuntimePackageV2Manifest;
  slices: Array<{ descriptor: RuntimeSliceDescriptor; data: unknown }>;
}): Promise<DemoScenarioPackage> {
  const packageDraft = emptyScenarioPackage(input.manifest) as unknown as Record<string, unknown>;
  const shardOrdersBySourcePath = new Map<string, Set<number>>();
  const descriptorsByPath = new Map(input.manifest.descriptors.map((descriptor) => [descriptor.path, descriptor]));

  input.slices
    .slice()
    .sort((left, right) => {
      if (left.descriptor.sourcePath === right.descriptor.sourcePath) {
        return (left.descriptor.order ?? 0) - (right.descriptor.order ?? 0);
      }
      return left.descriptor.sourcePath.localeCompare(right.descriptor.sourcePath);
    })
    .forEach(({ descriptor, data }) => {
      const manifestDescriptor = descriptorsByPath.get(descriptor.path);
      if (!manifestDescriptor || manifestDescriptor.kind !== 'slice') {
        throw new Error(`Slice descriptor ${descriptor.path} is not declared by manifest.`);
      }

      if (!Array.isArray(data)) {
        throw new Error(`Slice ${descriptor.path} must be a JSON array.`);
      }

      const order = descriptor.order ?? 0;
      const seenOrders = shardOrdersBySourcePath.get(descriptor.sourcePath) ?? new Set<number>();
      if (seenOrders.has(order)) {
        throw new Error(`Duplicate shard order ${order} for ${descriptor.sourcePath}.`);
      }
      seenOrders.add(order);
      shardOrdersBySourcePath.set(descriptor.sourcePath, seenOrders);

      const existing = getPath(packageDraft, descriptor.sourcePath);
      setPath(packageDraft, descriptor.sourcePath, Array.isArray(existing) ? [...existing, ...data] : data);
    });

  const assembled = validateDemoScenarioPackage(packageDraft as unknown as DemoScenarioPackage);
  const actualFingerprint = await computeDemoScenarioFingerprint(assembled);
  if (assembled.scenario.fingerprint !== actualFingerprint) {
    throw new Error('Assembled DemoScenarioPackage scenario fingerprint does not match package content.');
  }

  return assembled;
}

export function assertRuntimePackageProvenance(
  value: unknown,
  options: { manifest?: RuntimePackageV2Manifest } = {}
): RuntimePackageV2Provenance {
  if (!isPlainObject(value)) {
    throw new Error('Runtime package provenance must be a JSON object.');
  }

  const provenance = value as Partial<RuntimePackageV2Provenance>;
  if (provenance.formatVersion !== 1) {
    throw new Error(`Runtime package provenance formatVersion "${provenance.formatVersion}" is not supported.`);
  }
  (
    [
      'releaseId',
      'scenarioId',
      'topicKey',
      'topicSummary',
      'seed',
      'contractFingerprint',
      'generatorVersion',
      'generatedAt',
    ] as const
  ).forEach((field) => assertNonEmptyString(provenance[field], `provenance.${field}`));
  assertOptionalSha256(provenance.businessDescriptionSha256, 'provenance.businessDescriptionSha256');
  assertOptionalSha256(provenance.semanticReportSha256, 'provenance.semanticReportSha256');
  assertOptionalSha256(provenance.domcRegistryFingerprint, 'provenance.domcRegistryFingerprint');
  assertRuntimeValidationSummary(provenance.validationSummary, 'provenance.validationSummary');

  if (provenance.moduleContractFingerprints !== undefined) {
    if (!isPlainObject(provenance.moduleContractFingerprints)) {
      throw new Error('provenance.moduleContractFingerprints must be an object when provided.');
    }
    Object.entries(provenance.moduleContractFingerprints).forEach(([moduleId, sha256]) => {
      assertNonEmptyString(moduleId, 'provenance.moduleContractFingerprints key');
      assertOptionalSha256(sha256, `provenance.moduleContractFingerprints.${moduleId}`);
    });
  }
  if (provenance.adapterVersions !== undefined) {
    if (!isPlainObject(provenance.adapterVersions)) {
      throw new Error('provenance.adapterVersions must be an object when provided.');
    }
    Object.entries(provenance.adapterVersions).forEach(([adapterId, version]) => {
      assertNonEmptyString(adapterId, 'provenance.adapterVersions key');
      assertNonEmptyString(version, `provenance.adapterVersions.${adapterId}`);
    });
  }
  if (provenance.adapterCapabilitySummary !== undefined) {
    if (!Array.isArray(provenance.adapterCapabilitySummary)) {
      throw new Error('provenance.adapterCapabilitySummary must be an array when provided.');
    }
    provenance.adapterCapabilitySummary.forEach((item, index) => {
      if (!isPlainObject(item)) {
        throw new Error(`provenance.adapterCapabilitySummary[${index}] must be a JSON object.`);
      }
      assertNonEmptyString(item.moduleId, `provenance.adapterCapabilitySummary[${index}].moduleId`);
      assertNonEmptyString(item.adapterId, `provenance.adapterCapabilitySummary[${index}].adapterId`);
      assertNonEmptyString(item.adapterVersion, `provenance.adapterCapabilitySummary[${index}].adapterVersion`);
      if (!Array.isArray(item.outputSourcePaths) || !item.outputSourcePaths.length) {
        throw new Error(`provenance.adapterCapabilitySummary[${index}].outputSourcePaths must be a non-empty array.`);
      }
      item.outputSourcePaths.forEach((sourcePath, sourcePathIndex) =>
        assertNonEmptyString(sourcePath, `provenance.adapterCapabilitySummary[${index}].outputSourcePaths[${sourcePathIndex}]`)
      );
    });
  }

  if (!Array.isArray(provenance.materials) || provenance.materials.length === 0) {
    throw new Error('provenance.materials must be a non-empty array.');
  }
  provenance.materials.forEach((material, index) => {
    if (!isPlainObject(material)) {
      throw new Error(`provenance.materials[${index}] must be a JSON object.`);
    }
    if (!RUNTIME_PACKAGE_PROVENANCE_MATERIAL_KINDS.has(material.kind)) {
      throw new Error(`provenance.materials[${index}].kind "${material.kind}" is not supported.`);
    }
    assertNonEmptyString(material.name, `provenance.materials[${index}].name`);
    assertOptionalSha256(material.sha256, `provenance.materials[${index}].sha256`);
  });

  const manifest = options.manifest;
  if (manifest) {
    (
      [
        'releaseId',
        'scenarioId',
        'seed',
        'contractFingerprint',
        'generatorVersion',
        'generatedAt',
      ] as const
    ).forEach((field) => {
      if (provenance[field] !== manifest[field]) {
        throw new Error(`provenance.${field} must match manifest.${field}.`);
      }
    });
    if (provenance.domcRegistryFingerprint !== manifest.domcRegistryFingerprint) {
      throw new Error('provenance.domcRegistryFingerprint must match manifest.domcRegistryFingerprint.');
    }
    const semanticReportDescriptor = manifest.descriptors.find(
      (descriptor) =>
        descriptor.kind === 'artifact' &&
        ((descriptor as RuntimeArtifactDescriptor).artifactType === 'semantic-report' ||
          descriptor.path === 'semantic-report.json')
    );
    if (semanticReportDescriptor && provenance.semanticReportSha256 !== semanticReportDescriptor.sha256) {
      throw new Error('provenance.semanticReportSha256 must match semantic report artifact descriptor.');
    }
    if (!semanticReportDescriptor && provenance.semanticReportSha256) {
      throw new Error('provenance.semanticReportSha256 requires a semantic report artifact descriptor.');
    }
  }

  return provenance as RuntimePackageV2Provenance;
}
