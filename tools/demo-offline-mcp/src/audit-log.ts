import crypto from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { issueFromUnknown } from './errors.js';
import { ProjectPaths } from './project-paths.js';
import type {
  CompiledDemoScenarioPackage,
  DemoOfflineContext,
  GenerationPlan,
  IndustryDataDraft,
  ToolEnvelope,
  ValidationIssue,
} from './types.js';

export type AuditPhase = 'started' | 'succeeded' | 'failed';

export interface ToolAuditEvent {
  tool: string;
  phase: AuditPhase;
  input?: Record<string, unknown>;
  output?: Record<string, unknown>;
  error?: Record<string, unknown>;
}

export const AUDIT_LOG_RELATIVE_PATH = '.audit/demo-offline-mcp.jsonl';
const AUDIT_SCHEMA_VERSION = 2;
const PROCESS_STARTED_AT = new Date().toISOString();
const RUNTIME_MODULE_PATH = fileURLToPath(import.meta.url);

type ObjectLike = Record<string, unknown>;
type RuntimeFileFingerprint = {
  path: string;
  repoPath?: string;
  mtimeMs: number;
  size: number;
  sha256: string;
};

type RuntimeFingerprint = {
  auditSchemaVersion: number;
  pid: number;
  ppid: number;
  processStartedAt: string;
  nodeVersion: string;
  execPath: string;
  argv: string[];
  cwd: string;
  entrypoint?: string;
  entrypointMtimeMs?: number;
  packageVersion?: string;
  gitHead?: string;
  loadedFiles: RuntimeFileFingerprint[];
};

let runtimeFingerprintByRepo = new Map<string, Promise<RuntimeFingerprint>>();

function isAuditDisabled(): boolean {
  return ['off', 'false', '0'].includes((process.env.DEMO_OFFLINE_MCP_AUDIT ?? '').toLowerCase());
}

function isObjectLike(value: unknown): value is ObjectLike {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function truncateText(value: string, maxLength = 160): string {
  return value.length > maxLength ? `${value.slice(0, maxLength)}...` : value;
}

function normalizeSlashes(value: string): string {
  return value.split(path.sep).join('/');
}

async function readJsonFile<T>(filePath: string): Promise<T | undefined> {
  const source = await fs.readFile(filePath, 'utf8').catch(() => undefined);
  if (!source) return undefined;

  try {
    return JSON.parse(source) as T;
  } catch {
    return undefined;
  }
}

async function readGitHead(repoRoot: string): Promise<string | undefined> {
  const headPath = path.join(repoRoot, '.git', 'HEAD');
  const head = (await fs.readFile(headPath, 'utf8').catch(() => undefined))?.trim();
  if (!head) return undefined;

  const refMatch = head.match(/^ref:\s+(.+)$/);
  if (!refMatch) return head;

  const refPath = path.join(repoRoot, '.git', refMatch[1]);
  const refHead = (await fs.readFile(refPath, 'utf8').catch(() => undefined))?.trim();
  return refHead ? `${refMatch[1]}@${refHead}` : refMatch[1];
}

async function fingerprintFile(repoRoot: string, filePath: string): Promise<RuntimeFileFingerprint | undefined> {
  const [stat, source] = await Promise.all([
    fs.stat(filePath).catch(() => undefined),
    fs.readFile(filePath).catch(() => undefined),
  ]);

  if (!stat || !source) return undefined;

  return {
    path: filePath,
    repoPath: normalizeSlashes(path.relative(repoRoot, filePath)),
    mtimeMs: stat.mtimeMs,
    size: stat.size,
    sha256: crypto.createHash('sha256').update(source).digest('hex').slice(0, 16),
  };
}

async function resolveRuntimeFingerprint(paths: ProjectPaths): Promise<RuntimeFingerprint> {
  const cached = runtimeFingerprintByRepo.get(paths.repoRoot);
  if (cached) return cached;

  const fingerprintPromise = (async () => {
    const moduleExtension = path.extname(RUNTIME_MODULE_PATH) || '.js';
    const moduleDir = path.dirname(RUNTIME_MODULE_PATH);
    const loadedFilePaths = [
      RUNTIME_MODULE_PATH,
      path.join(moduleDir, `writer${moduleExtension}`),
      path.join(moduleDir, 'tools', `promote-candidate${moduleExtension}`),
    ];
    const packageJson = await readJsonFile<{ version?: string }>(
      path.join(paths.repoRoot, 'tools', 'demo-offline-mcp', 'package.json')
    );
    const entrypoint = process.argv[1] ? path.resolve(process.argv[1]) : undefined;
    const entrypointStat = entrypoint ? await fs.stat(entrypoint).catch(() => undefined) : undefined;
    const loadedFiles = (
      await Promise.all(loadedFilePaths.map((filePath) => fingerprintFile(paths.repoRoot, filePath)))
    ).filter((file): file is RuntimeFileFingerprint => Boolean(file));

    return {
      auditSchemaVersion: AUDIT_SCHEMA_VERSION,
      pid: process.pid,
      ppid: process.ppid,
      processStartedAt: PROCESS_STARTED_AT,
      nodeVersion: process.version,
      execPath: process.execPath,
      argv: process.argv.slice(0, 8),
      cwd: process.cwd(),
      entrypoint,
      entrypointMtimeMs: entrypointStat?.mtimeMs,
      packageVersion: packageJson?.version,
      gitHead: await readGitHead(paths.repoRoot),
      loadedFiles,
    };
  })();

  runtimeFingerprintByRepo.set(paths.repoRoot, fingerprintPromise);
  return fingerprintPromise;
}

function compactIssues(issues: ValidationIssue[] | undefined): Array<Record<string, unknown>> | undefined {
  if (!issues?.length) return undefined;

  return issues.slice(0, 10).map((issue) => ({
    path: issue.path,
    code: issue.code,
    severity: issue.severity,
  }));
}

function summarizeScenarioPackage(value: unknown): Record<string, unknown> | undefined {
  if (!isObjectLike(value)) return undefined;

  const scenarioPackage = value as Partial<CompiledDemoScenarioPackage>;
  return {
    scenarioId: scenarioPackage.scenario?.id,
    scenarioName: scenarioPackage.scenario?.name,
    version: scenarioPackage.scenario?.version,
    fingerprint: scenarioPackage.scenario?.fingerprint,
    projectCount: scenarioPackage.project?.projects?.length ?? 0,
    versionCount: scenarioPackage.project?.versions?.length ?? 0,
    topologyCount: scenarioPackage.project?.topologies?.length ?? 0,
    sessionCount: scenarioPackage.simulation?.sessions?.length ?? 0,
    messageCount: scenarioPackage.simulation?.messages?.length ?? 0,
    alarmCount: scenarioPackage.simulation?.alarms?.length ?? 0,
  };
}

export function summarizePlan(value: unknown): Record<string, unknown> | undefined {
  if (!isObjectLike(value)) return undefined;

  const plan = value as Partial<GenerationPlan>;
  return {
    scenarioId: plan.scenarioId,
    scenarioName: plan.scenarioName,
    industry: plan.industry,
    brief: typeof plan.brief === 'string' ? truncateText(plan.brief) : undefined,
    scope: plan.scope,
    copiedSlices: plan.copiedSlices,
    targetCounts: plan.targetCounts,
  };
}

export function summarizeDraft(value: unknown): Record<string, unknown> | undefined {
  if (!isObjectLike(value)) return undefined;

  const draft = value as Partial<IndustryDataDraft>;
  return {
    industryId: draft.industry?.id,
    industryName: draft.industry?.name,
    keywords: draft.industry?.keywords?.slice(0, 8),
    scenarioId: draft.scenario?.id,
    scenarioName: draft.scenario?.name,
    projectCount: draft.projects?.length ?? 0,
    projectKeys: draft.projects?.slice(0, 10).map((project) => project.key),
  };
}

export function summarizeScenarioInput(value: unknown): Record<string, unknown> | undefined {
  return summarizeScenarioPackage(value);
}

function summarizeContext(value: DemoOfflineContext): Record<string, unknown> {
  return {
    repoRoot: value.repoRoot,
    frontendRoot: value.frontendRoot,
    generatedRoot: value.generatedRoot,
    safeSlices: value.safeSlices,
    copiedSlices: value.copiedSlices,
    scenarioCount: value.scenarios.length,
    candidateCount: value.scenarios.filter((scenario) => scenario.kind === 'candidate').length,
    handlerCount: value.handlers.length,
    uncoveredHandlers: value.handlers.filter((handler) => !handler.covered).map((handler) => handler.name),
    risks: value.risks.map((risk) => risk.code),
  };
}

function summarizeData(value: unknown): Record<string, unknown> | undefined {
  if (!isObjectLike(value)) return undefined;

  if ('repoRoot' in value && 'safeSlices' in value && 'scenarios' in value) {
    return summarizeContext(value as unknown as DemoOfflineContext);
  }

  if ('scenarioPackage' in value) {
    return {
      scenarioPackage: summarizeScenarioPackage(value.scenarioPackage),
      summary: value.summary,
    };
  }

  if ('valid' in value && 'issues' in value) {
    const issues = Array.isArray(value.issues) ? (value.issues as ValidationIssue[]) : [];
    return {
      valid: value.valid,
      issueCount: issues.length,
      issues: compactIssues(issues),
      hasRepairedDraft: Boolean(value.repairedDraft),
      repairSummary: value.repairSummary,
    };
  }

  if ('runId' in value && 'results' in value) {
    const results = Array.isArray(value.results) ? value.results : [];
    return {
      runId: value.runId,
      candidateId: value.candidateId,
      scenarioId: value.scenarioId,
      runMode: value.runMode,
      passed: value.passed,
      recommendedPreviewCommand: value.recommendedPreviewCommand,
      profiles: results.map((result) =>
        isObjectLike(result)
          ? {
              profile: result.profile,
              exitCode: result.exitCode,
              passed: result.passed,
            }
          : result
      ),
    };
  }

  const knownKeys = [
    'candidateId',
    'scenarioId',
    'scenarioName',
    'industry',
    'scope',
    'copiedSlices',
    'targetCounts',
    'paths',
    'metadataPath',
    'registryUpdated',
    'activated',
    'activePath',
    'summary',
  ];
  const summary: Record<string, unknown> = {};

  for (const key of knownKeys) {
    if (key in value) {
      summary[key] = value[key];
    }
  }

  if (Object.keys(summary).length) return summary;

  const scenarioSummary = summarizeScenarioPackage(value);
  return scenarioSummary ? { scenarioPackage: scenarioSummary } : undefined;
}

function summarizeEnvelope(envelope: ToolEnvelope<unknown>): Record<string, unknown> {
  return {
    ok: envelope.ok,
    summary: envelope.summary,
    data: summarizeData(envelope.data),
    artifactPaths: envelope.artifacts?.map((artifact) => artifact.path).filter(Boolean),
    nextActions: envelope.nextActions,
    errors: compactIssues(envelope.errors),
  };
}

function summarizeUnknownError(error: unknown): Record<string, unknown> {
  const issue = issueFromUnknown(error);
  return {
    path: issue.path,
    code: issue.code,
    severity: issue.severity,
    expected: issue.expected,
    fixHint: issue.fixHint,
  };
}

export async function resolveAuditLogPath(paths: ProjectPaths): Promise<string> {
  return paths.resolveCandidateWritePath(AUDIT_LOG_RELATIVE_PATH);
}

export async function appendAuditEvent(paths: ProjectPaths, event: ToolAuditEvent): Promise<string> {
  const logPath = await resolveAuditLogPath(paths);
  const runtime = await resolveRuntimeFingerprint(paths);
  const record = {
    timestamp: new Date().toISOString(),
    tool: event.tool,
    phase: event.phase,
    runtime,
    repoRoot: paths.repoRoot,
    frontendRoot: paths.frontendRoot,
    generatedRoot: paths.generatedRoot,
    candidateRoot: paths.candidateRoot,
    input: event.input,
    output: event.output,
    error: event.error,
  };

  await fs.mkdir(path.dirname(logPath), { recursive: true });
  await fs.appendFile(logPath, `${JSON.stringify(record)}\n`, 'utf8');

  return logPath;
}

export async function appendAuditEventSafely(
  paths: ProjectPaths,
  event: ToolAuditEvent
): Promise<void> {
  if (isAuditDisabled()) return;

  try {
    const logPath = await appendAuditEvent(paths, event);
    console.error(
      `[${event.tool}] ${event.phase} pid=${process.pid} started=${PROCESS_STARTED_AT} repo=${
        paths.repoRoot
      } audit=${path.relative(paths.repoRoot, logPath)}`
    );
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    console.error(`[${event.tool}] audit_log_failed: ${message}`);
  }
}

export async function withToolAudit<T>(
  tool: string,
  options: { repoRoot?: string; input?: Record<string, unknown> },
  run: (paths: ProjectPaths) => Promise<ToolEnvelope<T>>
): Promise<ToolEnvelope<T>> {
  let paths: ProjectPaths | undefined;

  try {
    paths = await ProjectPaths.create({ repoRoot: options.repoRoot });
    await appendAuditEventSafely(paths, {
      tool,
      phase: 'started',
      input: options.input,
    });

    const envelope = await run(paths);
    await appendAuditEventSafely(paths, {
      tool,
      phase: envelope.ok ? 'succeeded' : 'failed',
      input: options.input,
      output: summarizeEnvelope(envelope),
    });

    return envelope;
  } catch (error) {
    if (paths) {
      await appendAuditEventSafely(paths, {
        tool,
        phase: 'failed',
        input: options.input,
        error: summarizeUnknownError(error),
      });
    } else {
      const issue = summarizeUnknownError(error);
      console.error(`[${tool}] failed before repo paths resolved: ${JSON.stringify(issue)}`);
    }

    throw error;
  }
}
