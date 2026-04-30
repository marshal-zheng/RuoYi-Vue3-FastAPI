import type { SemanticQualityReport, SemanticQualitySummary } from './semantic/types.js';

export interface ValidationIssue {
  path: string;
  code: string;
  severity: 'error' | 'warning';
  actual?: unknown;
  expected?: string;
  fixHint: string;
  autoRepairable: boolean;
}

export type DemoDomcQualityGate =
  | 'domc-schema'
  | 'domc-registry-integrity'
  | 'domc-fingerprint'
  | 'adapter-registry'
  | 'adapter-capability'
  | 'module-blocker'
  | 'ui-journey-coverage'
  | 'handler-mapping-coverage'
  | 'contract-drift'
  | 'domc-provenance'
  | 'adapter-regression';

export interface DemoOfflineBlockerIssue extends ValidationIssue {
  gate: DemoDomcQualityGate;
  missingArtifacts: string[];
  nextActions: string[];
}

export interface DemoOfflineArtifact {
  kind: 'file' | 'command' | 'scenario' | 'report';
  label: string;
  path?: string;
  metadata?: Record<string, unknown>;
}

export interface ToolEnvelope<T> extends Record<string, unknown> {
  ok: boolean;
  summary: string;
  data?: T;
  errors?: ValidationIssue[];
  artifacts?: DemoOfflineArtifact[];
  nextActions?: string[];
}

export type DemoGeneratableSlice = string;
export type DemoCopiedSlice = string;
export type DemoDomcCapability = 'generatable' | 'copyOnly' | 'unsupported';
export type DemoTargetKind = 'source-generated' | 'offline-static';

export interface DemoOfflineContextDomcModule {
  moduleId: string;
  capability: DemoDomcCapability;
  lifecycle: 'active' | 'deprecated' | 'experimental';
  sourcePaths: string[];
  adapterId?: string;
  evidence: string[];
}

export interface DemoOfflineContext {
  repoRoot: string;
  frontendRoot: string;
  generatedRoot: string;
  schemaVersion: 1;
  safeSlices: DemoGeneratableSlice[];
  copiedSlices: DemoCopiedSlice[];
  domcModules: DemoOfflineContextDomcModule[];
  handlers: Array<{ name: string; source: string; covered: boolean }>;
  scenarios: Array<{
    id: string;
    name: string;
    kind: 'default' | 'generated' | 'candidate';
    path: string;
  }>;
  scripts: {
    devMock: string;
    buildDemoOffline: string;
    previewDemoOffline: string;
    typeCheck: string;
    testRun: string;
  };
  risks: Array<{ code: string; message: string; source?: string }>;
}

export interface GenerationPlan {
  scenarioId: string;
  scenarioName: string;
  industry: string;
  brief: string;
  scope: DemoGeneratableSlice[];
  copiedSlices: DemoCopiedSlice[];
  targetCounts: {
    projects: number;
    versionsPerProject: number;
    sessionsPerProject: number;
  };
  trace: Array<{
    slice: string;
    status: 'generate' | 'copy' | 'blocked' | 'unsupported';
    evidence: string[];
    blocker?: DemoOfflineBlockerIssue;
  }>;
  moduleTrace?: Array<{
    moduleId: string;
    capability: DemoDomcCapability;
    status: 'generate' | 'copy' | 'blocked' | 'unsupported';
    sourcePaths: string[];
    adapterId?: string;
    adapterVersion?: string;
    evidence: string[];
    blocker?: DemoOfflineBlockerIssue;
  }>;
}

export interface IndustryDataDraft {
  industry: {
    id: string;
    name: string;
    keywords?: string[];
  };
  scenario: {
    id: string;
    name: string;
    version?: string;
    seed?: string;
    description?: string;
  };
  projects: Array<{
    key: string;
    name: string;
    region?: string;
    stage: string;
    departmentName?: string;
    ownerRole: string;
    ownerName?: string;
    riskLevel: 'low' | 'medium' | 'high';
    risk: string;
    remark: string;
    keyMetrics?: Array<{ name: string; value: string; trend?: string }>;
    versions?: Array<{
      name: string;
      locked?: boolean;
      summary?: string;
    }>;
    topology?: {
      nodes?: Array<{ name: string; type: string; status?: string }>;
      links?: Array<{ source: string; target: string; label?: string }>;
    };
    simulation?: {
      status?: 'idle' | 'running' | 'paused' | 'completed' | 'failed';
      messages?: string[];
      alarms?: Array<{ severity: 'low' | 'medium' | 'high'; message: string }>;
      events?: string[];
    };
  }>;
}

export interface DraftValidationResult {
  valid: boolean;
  repairedDraft?: IndustryDataDraft;
  issues: ValidationIssue[];
  repairSummary: string[];
}

export interface CompiledDemoScenarioPackage {
  schemaVersion: 1;
  scenario: {
    id: string;
    name: string;
    version: string;
    fingerprint: string;
    seed?: string;
  };
  auth: {
    accounts: unknown[];
    roles: unknown[];
    permissions: unknown[];
  };
  system: {
    menus: unknown[];
    dictTypes: unknown[];
    dicts: unknown[];
    departments: unknown[];
    posts: unknown[];
    users: unknown[];
  };
  project: {
    projects: Array<Record<string, unknown>>;
    versions: Array<Record<string, unknown>>;
    topologies: Array<Record<string, unknown>>;
  };
  simulation: {
    sessions: Array<Record<string, unknown>>;
    messages: Array<Record<string, unknown>>;
    bandwidth: Array<Record<string, unknown>>;
    alarms: Array<Record<string, unknown>>;
    faults: Array<Record<string, unknown>>;
    events: Array<Record<string, unknown>>;
    streamFrames: Array<Record<string, unknown>>;
  };
}

export interface CompileSummary {
  scenarioId: string;
  fingerprint: string;
  projectCount: number;
  versionCount: number;
  sessionCount: number;
  copiedSlices: DemoCopiedSlice[];
  generatedSlices: DemoGeneratableSlice[];
}

export interface CompileScenarioResult {
  scenarioPackage: CompiledDemoScenarioPackage;
  summary: CompileSummary;
}

export interface RuntimeValidationSummary {
  schemaValid: boolean;
  contractValid: boolean;
  invariantValid: boolean;
  dryRunValid?: boolean;
  issueCount: number;
}

export interface RuntimeScenarioMeta {
  scenarioId: string;
  topicKey: string;
  schemaVersion: 1;
  contractFingerprint: string;
  generatorVersion: string;
  seed: string;
  generatedAt: string;
  validationSummary: RuntimeValidationSummary;
  sourceTarget: 'offline-static';
  scenarioFingerprint: string;
  packageSha256: string;
  releaseId?: string;
  manifestPath?: string;
  manifestSha256?: string;
  provenancePath?: string;
  domcRegistryFingerprint?: string;
  moduleContractFingerprints?: Record<string, string>;
  adapterVersions?: Record<string, string>;
  adapterCapabilitySummary?: Array<{
    moduleId: string;
    adapterId: string;
    adapterVersion: string;
    outputSourcePaths: string[];
  }>;
}

export interface DemoOfflineContractManifest {
  contractVersion: 1;
  schemaVersion: 1;
  generatedAt: string;
  runtimeAdapterVersion: string;
  generatorAdapterVersion: string;
  contractFingerprint: string;
  supportedModules: string[];
  generatedModules: string[];
  copiedModules: string[];
  domcRegistryFingerprint: string;
  domcRegistryPath: 'demo-contract/domc.registry.json';
  moduleContractFingerprints: Record<string, string>;
  adapterReferences: Array<{
    moduleId: string;
    adapterId: string;
    adapterVersionRange: string;
    capability: DemoDomcCapability;
    outputSourcePaths: string[];
  }>;
  indexedDbMapping: {
    dbName: string;
    dbVersion: number;
    tables: Array<{
      table: string;
      sourcePath: string;
      primaryKey: string;
      indexes: string[];
      minItems?: number;
    }>;
  };
  handlerCoverage: Array<Record<string, unknown>>;
  moduleContracts?: Array<Record<string, unknown>>;
  invariants: Array<Record<string, unknown>>;
}

export interface DemoDomcFieldContract {
  name: string;
  required: boolean;
  nullable: boolean;
  semanticKind: string;
  enumValues?: string[];
  defaultRepair?: 'derive' | 'copy-default' | 'block';
}

export interface DemoDomcReferenceContract {
  field: string;
  targetEntity: string;
  targetField: string;
  relation: string;
  required: boolean;
}

export type DemoDomcSemanticAnchorType =
  | 'storyBeat'
  | 'domainObject'
  | 'persona'
  | 'role'
  | 'processStage'
  | 'riskType'
  | 'metricDefinition';

export interface DemoDomcDiversityRule {
  ruleId: string;
  primarySourcePath: string;
  fields: string[];
  dimensions: string[];
  duplicateThreshold: number;
  templateSimilarityThreshold: number;
  severity: 'error' | 'warning';
  explainableExceptions: string[];
}

export interface DemoDomcSemanticAnchorRule {
  ruleId: string;
  sourcePath: string;
  minAnchorTypes: number;
  requiredAnchorTypes: DemoDomcSemanticAnchorType[];
  supportCategories: string[];
}

export interface DemoDomcEntityContract {
  entity: string;
  sourcePath: string;
  indexedDbTable: string;
  primaryKey: string;
  minItems: number;
  fields: DemoDomcFieldContract[];
  references: DemoDomcReferenceContract[];
  ownership: {
    recordOwner: 'adapter' | 'default-scenario' | 'runtime-required';
    mergePolicy: 'replace-sourcePath' | 'append-shards' | 'copy-only';
  };
}

export interface DemoDomcModuleContract {
  moduleId: string;
  moduleVersion: string;
  lifecycle: 'active' | 'deprecated' | 'experimental';
  capability: DemoDomcCapability;
  owner: string;
  sourcePaths: string[];
  indexedDbTables: DemoIndexedDbTableMapping[];
  handlerCoverage: Array<{
    module: string;
    source: string;
    apiPrefix: string;
    coveredRoutes: string[];
    unsupportedBehavior: string;
  }>;
  uiJourneys: Array<{
    journeyId: string;
    entry: string;
    primarySourcePath: string;
    requiredSupportSourcePaths: string[];
    listFields: string[];
    detailFields: string[];
    keyActions: Array<{ action: string; demoBehavior: string }>;
    emptyState: string;
    errorState: string;
    minimumDemoChain: string[];
  }>;
  entities: DemoDomcEntityContract[];
  stateMachines: Array<Record<string, unknown>>;
  invariants: Array<Record<string, unknown>>;
  diversityRules: DemoDomcDiversityRule[];
  semanticAnchors?: DemoDomcSemanticAnchorRule[];
  materializationPolicy: Array<{
    sourcePath: string;
    order: number;
    materializationReason: 'semantic-generated' | 'copied-default' | 'runtime-required';
    minItems: number;
  }>;
  adapterRef?: {
    adapterId: string;
    adapterVersionRange: string;
    capabilities: string[];
    outputSourcePaths: string[];
    priority?: number;
  };
  copyOnly?: {
    source: 'demo-contract/default-scenario.json' | 'bundle-default-v2';
    sourcePaths: string[];
    reason: string;
    minItems: Record<string, number>;
  };
  unsupportedReason?: string;
  migrationSources: string[];
}

export interface DemoDomcRegistry {
  schemaVersion: 1;
  registryVersion: string;
  generatedAt: string;
  domcFingerprint: string;
  contractVersion: 1;
  platformLayer: 'DOMC';
  modules: DemoDomcModuleContract[];
  qualityGates: Array<Record<string, unknown>>;
  migrationSources: string[];
}

export interface DemoIndexedDbTableMapping {
  table: string;
  sourcePath: string;
  primaryKey: string;
  indexes: string[];
  minItems?: number;
}

export interface ImportDryRunSummary {
  dbName: string;
  inserted: Record<string, number>;
  activeScenario: {
    scenarioId: string;
    fingerprint: string;
  };
  durationMs: number;
}

export interface OfflineStaticActivationResult {
  phase:
    | 'staged'
    | 'validation_failed'
    | 'dry_run_failed'
    | 'published'
    | 'activated'
    | 'candidate_written';
  targetKind: 'offline-static';
  packageFormat?: 'v2';
  targetRoot: string;
  releaseId?: string;
  scenarioId: string;
  topicKey: string;
  seed: string;
  contractFingerprint: string;
  scenarioFingerprint: string;
  activePointerPath?: string;
  previousPointerPath?: string;
  manifestPath?: string;
  provenancePath?: string;
  validationSummary?: RuntimeValidationSummary;
  dryRunSummary?: ImportDryRunSummary;
  semanticQualitySummary?: SemanticQualitySummary;
  semanticReportPath?: string;
  semanticQualityReport?: SemanticQualityReport;
  domcRegistryFingerprint?: string;
  moduleContractFingerprints?: Record<string, string>;
  adapterVersions?: Record<string, string>;
  moduleTrace?: GenerationPlan['moduleTrace'];
  paths: string[];
}

export type CheckProfile =
  | 'candidate-focused-tests'
  | 'frontend-type-check'
  | 'candidate-demo-offline-build'
  | 'promoted-demo-offline-build';

export interface RunChecksResult {
  runId: string;
  passed: boolean;
  scenarioId?: string;
  candidateId?: string;
  runMode: 'candidate' | 'promoted' | 'general';
  recommendedPreviewCommand?: string;
  results: import('./errors.js').CheckResult[];
}

export function okEnvelope<T>(
  summary: string,
  data: T,
  extras: Omit<ToolEnvelope<T>, 'ok' | 'summary' | 'data'> = {}
): ToolEnvelope<T> {
  return {
    ok: true,
    summary,
    data,
    ...extras,
  };
}

export function errorEnvelope<T>(
  summary: string,
  errors: ValidationIssue[],
  extras: Omit<ToolEnvelope<T>, 'ok' | 'summary' | 'errors'> = {}
): ToolEnvelope<T> {
  return {
    ok: false,
    summary,
    errors,
    ...extras,
  };
}
