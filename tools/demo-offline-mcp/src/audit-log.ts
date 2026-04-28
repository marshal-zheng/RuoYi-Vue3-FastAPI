import fs from 'node:fs/promises';
import path from 'node:path';

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

type ObjectLike = Record<string, unknown>;

function isAuditDisabled(): boolean {
  return ['off', 'false', '0'].includes((process.env.DEMO_OFFLINE_MCP_AUDIT ?? '').toLowerCase());
}

function isObjectLike(value: unknown): value is ObjectLike {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function truncateText(value: string, maxLength = 160): string {
  return value.length > maxLength ? `${value.slice(0, maxLength)}...` : value;
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
  const record = {
    timestamp: new Date().toISOString(),
    tool: event.tool,
    phase: event.phase,
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
      `[${event.tool}] ${event.phase} repo=${paths.repoRoot} audit=${path.relative(paths.repoRoot, logPath)}`
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
