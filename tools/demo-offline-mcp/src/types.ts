export interface ValidationIssue {
  path: string;
  code: string;
  severity: 'error' | 'warning';
  actual?: unknown;
  expected?: string;
  fixHint: string;
  autoRepairable: boolean;
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

export type DemoGeneratableSlice = 'project' | 'simulation';
export type DemoCopiedSlice = 'auth' | 'system';

export interface DemoOfflineContext {
  repoRoot: string;
  frontendRoot: string;
  generatedRoot: string;
  schemaVersion: 1;
  safeSlices: DemoGeneratableSlice[];
  copiedSlices: DemoCopiedSlice[];
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
    status: 'generate' | 'copy' | 'unsupported';
    evidence: string[];
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
