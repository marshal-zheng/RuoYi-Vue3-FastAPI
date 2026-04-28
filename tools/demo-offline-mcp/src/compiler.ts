import fs from 'node:fs/promises';
import path from 'node:path';
import vm from 'node:vm';

import ts from 'typescript';

import { industryDataDraftSchema } from './draft-schema.js';
import type {
  CompileScenarioResult,
  CompiledDemoScenarioPackage,
  GenerationPlan,
  IndustryDataDraft,
  ToolEnvelope,
  ValidationIssue,
} from './types.js';
import { errorEnvelope, okEnvelope } from './types.js';
import type { ProjectPaths } from './project-paths.js';

export interface CompileScenarioInput {
  plan: GenerationPlan;
  draft: IndustryDataDraft;
  paths: ProjectPaths;
}

const BASE_TIME = Date.UTC(2026, 3, 28, 9, 0, 0);

function hashText(value: string): string {
  let hash = 2166136261;

  for (const char of value) {
    hash ^= char.charCodeAt(0);
    hash = Math.imul(hash, 16777619);
  }

  return (hash >>> 0).toString(36);
}

function safeId(value: string): string {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 48);
}

function isoAt(minutes: number): string {
  return new Date(BASE_TIME + minutes * 60_000).toISOString();
}

function assertArray(value: unknown, pathName: string, issues: ValidationIssue[]): void {
  if (!Array.isArray(value)) {
    issues.push({
      path: pathName,
      code: 'compiled_package_array_missing',
      severity: 'error',
      actual: typeof value,
      expected: 'array',
      fixHint: `Compiler must output ${pathName} as an array.`,
      autoRepairable: false,
    });
  }
}

function validateCompiledScenarioPackage(packageValue: CompiledDemoScenarioPackage): ValidationIssue[] {
  const issues: ValidationIssue[] = [];

  if (packageValue.schemaVersion !== 1) {
    issues.push({
      path: 'schemaVersion',
      code: 'compiled_schema_version_invalid',
      severity: 'error',
      actual: packageValue.schemaVersion,
      expected: '1',
      fixHint: 'Compiler must emit DemoScenarioPackage schemaVersion 1.',
      autoRepairable: false,
    });
  }

  for (const pathName of [
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
  ]) {
    const value = pathName.split('.').reduce<unknown>((current, key) => {
      if (!current || typeof current !== 'object') return undefined;
      return (current as Record<string, unknown>)[key];
    }, packageValue);

    assertArray(value, pathName, issues);
  }

  return issues;
}

async function loadDefaultDemoScenario(paths: ProjectPaths): Promise<CompiledDemoScenarioPackage> {
  const defaultPath = path.join(paths.demoRoot, 'scenarios', 'default.ts');
  const source = await fs.readFile(defaultPath, 'utf8');
  const compiled = ts.transpileModule(source, {
    compilerOptions: {
      module: ts.ModuleKind.CommonJS,
      target: ts.ScriptTarget.ES2022,
      esModuleInterop: true,
    },
  }).outputText;
  const exportsObject: Record<string, unknown> = {};
  const moduleObject = { exports: exportsObject };
  const sandbox = {
    exports: exportsObject,
    module: moduleObject,
    require: (request: string) => {
      if (request === './schema') {
        return { DEMO_SCENARIO_SCHEMA_VERSION: 1 };
      }

      throw new Error(`Unexpected default scenario import: ${request}`);
    },
  };

  vm.runInNewContext(compiled, sandbox, {
    filename: defaultPath,
    timeout: 1000,
  });

  const loaded = (moduleObject.exports as Record<string, unknown>).defaultDemoScenario;

  if (!loaded || typeof loaded !== 'object') {
    throw new Error('defaultDemoScenario was not exported from frontend default scenario.');
  }

  return JSON.parse(JSON.stringify(loaded)) as CompiledDemoScenarioPackage;
}

function createProjectRecords(plan: GenerationPlan, draft: IndustryDataDraft) {
  const projects: Array<Record<string, unknown>> = [];
  const versions: Array<Record<string, unknown>> = [];
  const topologies: Array<Record<string, unknown>> = [];

  draft.projects.forEach((project, projectIndex) => {
    const projectId = 7001 + projectIndex;
    const versionDrafts = project.versions?.length
      ? project.versions
      : Array.from({ length: plan.targetCounts.versionsPerProject }, (_, versionIndex) => ({
          name: `${project.stage}方案 V${versionIndex + 1}`,
          locked: versionIndex === 0,
          summary: `${project.name} ${project.stage}演示版本`,
        }));
    const primaryVersionId = 8001 + projectIndex * 10;
    const updatedAt = isoAt(projectIndex * 13);

    projects.push({
      projectId,
      projectName: project.name,
      projectCode: project.key.toUpperCase().replace(/[^A-Z0-9]+/g, '-'),
      projectDesc: project.remark,
      description: project.risk,
      status: project.riskLevel === 'low' ? '1' : '0',
      createTime: isoAt(projectIndex * 13 - 240),
      updateTime: updatedAt,
      owner: `${project.ownerRole}-${project.ownerName ?? `${project.ownerRole}负责人${projectIndex + 1}`}`,
      createBy: `${plan.industry}演示团队`,
      updateBy: project.ownerRole,
      remark: project.remark,
      industry: draft.industry.id,
      industryName: draft.industry.name,
      region: project.region,
      businessStage: project.stage,
      keyMetrics: project.keyMetrics ?? [],
      riskLevel: project.riskLevel,
    });

    versionDrafts.slice(0, plan.targetCounts.versionsPerProject).forEach((versionDraft, versionIndex) => {
      const versionId = primaryVersionId + versionIndex;
      versions.push({
        versionId,
        projectId,
        versionNumber: `${safeId(project.key).toUpperCase()}-V${versionIndex + 1}.0`,
        versionName: versionDraft.name,
        description: versionDraft.summary ?? `${project.name} ${project.stage}演示版本`,
        locked: versionDraft.locked ?? versionIndex === 0,
        isLocked: versionDraft.locked ?? versionIndex === 0 ? '1' : '0',
        status: '0',
        createTime: isoAt(projectIndex * 13 - 180 + versionIndex),
        updateTime: updatedAt,
        createBy: `${plan.industry}演示团队`,
        updateBy: project.ownerRole,
        remark: versionDraft.summary ?? project.remark,
      });
    });

    const nodes =
      project.topology?.nodes?.length
        ? project.topology.nodes
        : [
            { name: `${project.stage}看板`, type: 'dashboard', status: 'active' },
            { name: `${project.ownerRole}节点`, type: 'workflow', status: 'active' },
          ];
    const links =
      project.topology?.links?.length
        ? project.topology.links
        : [{ source: nodes[0].name, target: nodes[1].name, label: project.stage }];

    topologies.push({
      id: `${safeId(plan.scenarioId)}-topology-${projectId}`,
      projectId,
      versionId: primaryVersionId,
      graph: {
        nodes: nodes.map((node, nodeIndex) => ({
          id: `${project.key}-node-${nodeIndex + 1}`,
          label: node.name,
          type: node.type,
          status: node.status ?? 'active',
        })),
        edges: links.map((link, linkIndex) => ({
          id: `${project.key}-edge-${linkIndex + 1}`,
          source: link.source,
          target: link.target,
          label: link.label ?? project.stage,
        })),
      },
      updateTime: updatedAt,
    });
  });

  return { projects, versions, topologies };
}

function createSimulationRecords(plan: GenerationPlan, draft: IndustryDataDraft) {
  const sessions: Array<Record<string, unknown>> = [];
  const messages: Array<Record<string, unknown>> = [];
  const bandwidth: Array<Record<string, unknown>> = [];
  const alarms: Array<Record<string, unknown>> = [];
  const faults: Array<Record<string, unknown>> = [];
  const events: Array<Record<string, unknown>> = [];
  const streamFrames: Array<Record<string, unknown>> = [];

  draft.projects.forEach((project, projectIndex) => {
    const projectId = 7001 + projectIndex;
    const versionId = 8001 + projectIndex * 10;

    for (let sessionIndex = 0; sessionIndex < plan.targetCounts.sessionsPerProject; sessionIndex += 1) {
      const sessionId = `${safeId(plan.scenarioId)}-session-${projectIndex + 1}-${sessionIndex + 1}`;
      const timestamp = isoAt(projectIndex * 17 + sessionIndex * 5);
      const sessionStatus = project.simulation?.status ?? (project.riskLevel === 'high' ? 'running' : 'completed');

      sessions.push({
        sessionId,
        projectId,
        versionId,
        status: sessionStatus,
        createTime: timestamp,
        updateTime: isoAt(projectIndex * 17 + sessionIndex * 5 + 3),
        scenarioStage: project.stage,
        riskLevel: project.riskLevel,
      });

      const messageDrafts = project.simulation?.messages?.length
        ? project.simulation.messages
        : [`${project.name}进入${project.stage}演示流程。`, project.risk];
      messageDrafts.forEach((message, messageIndex) => {
        messages.push({
          id: `${sessionId}-message-${messageIndex + 1}`,
          sessionId,
          timestamp: isoAt(projectIndex * 17 + messageIndex),
          role: messageIndex % 2 === 0 ? 'system' : 'operator',
          content: message,
          severity: project.riskLevel,
        });
      });

      bandwidth.push({
        id: `${sessionId}-bandwidth-1`,
        sessionId,
        portId: `${project.key}-port-1`,
        timestamp,
        inboundMbps: 40 + projectIndex * 7,
        outboundMbps: 24 + projectIndex * 5,
        utilization: project.riskLevel === 'high' ? 0.86 : 0.58,
      });

      (project.simulation?.alarms ?? [{ severity: project.riskLevel, message: project.risk }]).forEach(
        (alarm, alarmIndex) => {
          alarms.push({
            alarmId: `${sessionId}-alarm-${alarmIndex + 1}`,
            sessionId,
            timestamp: isoAt(projectIndex * 17 + alarmIndex + 1),
            severity: alarm.severity,
            message: alarm.message,
            status: alarm.severity === 'low' ? 'closed' : 'open',
          });
        }
      );

      if (project.riskLevel === 'high') {
        faults.push({
          faultId: `${sessionId}-fault-1`,
          sessionId,
          timestamp: isoAt(projectIndex * 17 + 2),
          faultType: project.stage,
          description: project.risk,
          status: 'processing',
        });
      }

      (project.simulation?.events ?? [`${project.stage}节点更新`, `${project.ownerRole}完成风险复核`]).forEach(
        (event, eventIndex) => {
          events.push({
            eventId: `${sessionId}-event-${eventIndex + 1}`,
            sessionId,
            triggerTime: isoAt(projectIndex * 17 + eventIndex + 3),
            eventType: project.stage,
            message: event,
          });
        }
      );

      streamFrames.push({
        frameId: `${sessionId}-frame-1`,
        sessionId,
        order: 1,
        type: 'summary',
        delayMs: 200,
        payload: {
          projectName: project.name,
          stage: project.stage,
          riskLevel: project.riskLevel,
        },
      });
    }
  });

  return { sessions, messages, bandwidth, alarms, faults, events, streamFrames };
}

export async function compileScenarioPackage(
  input: CompileScenarioInput
): Promise<ToolEnvelope<CompileScenarioResult>> {
  const parsed = industryDataDraftSchema.safeParse(input.draft);

  if (!parsed.success) {
    return errorEnvelope(
      'Cannot compile invalid IndustryDataDraft.',
      parsed.error.issues.map((zodIssue) => ({
        path: zodIssue.path.join('.') || '$',
        code: 'invalid_draft_structure',
        severity: 'error',
        actual: zodIssue.message,
        expected: zodIssue.code,
        fixHint: 'Run demo_offline_validate_draft and fix structural errors before compiling.',
        autoRepairable: false,
      }))
    );
  }

  const draft = parsed.data as IndustryDataDraft;
  const defaultScenario = await loadDefaultDemoScenario(input.paths);
  const fingerprint = `${safeId(input.plan.scenarioId)}-${hashText(
    JSON.stringify({ plan: input.plan, draft })
  )}`;
  const project = createProjectRecords(input.plan, draft);
  const simulation = createSimulationRecords(input.plan, draft);
  const scenarioPackage: CompiledDemoScenarioPackage = {
    schemaVersion: 1,
    scenario: {
      id: input.plan.scenarioId,
      name: input.plan.scenarioName,
      version: draft.scenario.version ?? '1.0.0',
      fingerprint,
      seed: draft.scenario.seed ?? input.plan.scenarioId,
    },
    auth: defaultScenario.auth,
    system: defaultScenario.system,
    project,
    simulation,
  };
  const packageIssues = validateCompiledScenarioPackage(scenarioPackage);

  if (packageIssues.length) {
    return errorEnvelope('Compiled scenario package failed structural validation.', packageIssues);
  }

  return okEnvelope(
    `Compiled scenario package ${input.plan.scenarioId}.`,
    {
      scenarioPackage,
      summary: {
        scenarioId: scenarioPackage.scenario.id,
        fingerprint: scenarioPackage.scenario.fingerprint,
        projectCount: scenarioPackage.project.projects.length,
        versionCount: scenarioPackage.project.versions.length,
        sessionCount: scenarioPackage.simulation.sessions.length,
        copiedSlices: input.plan.copiedSlices,
        generatedSlices: input.plan.scope,
      },
    },
    {
      nextActions: ['Write the compiled package as a generated candidate before running checks.'],
    }
  );
}
