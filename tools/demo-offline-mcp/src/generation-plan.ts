import type {
  DemoCopiedSlice,
  DemoGeneratableSlice,
  DemoOfflineContext,
  DemoOfflineBlockerIssue,
  GenerationPlan,
  ToolEnvelope,
} from './types.js';
import { okEnvelope } from './types.js';

export interface CreateGenerationPlanInput {
  brief: string;
  industry?: string;
  scenarioId?: string;
  scenarioName?: string;
  scope?: DemoGeneratableSlice[];
  targetCounts?: Partial<GenerationPlan['targetCounts']>;
}

const DEFAULT_TARGET_COUNTS = {
  projects: 6,
  versionsPerProject: 1,
  sessionsPerProject: 1,
} satisfies GenerationPlan['targetCounts'];

const INDUSTRY_ID_MAP: Record<string, string> = {
  房地产: 'real-estate',
  地产: 'real-estate',
  制造: 'manufacturing',
  教育: 'education',
  外卖: 'food-delivery',
};

function hashText(value: string): string {
  let hash = 5381;

  for (const char of value) {
    hash = (hash * 33) ^ char.charCodeAt(0);
  }

  return (hash >>> 0).toString(36).slice(0, 6);
}

function slugify(value: string): string {
  const normalized = value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');

  return normalized || `industry-${hashText(value)}`;
}

function inferIndustry(input: CreateGenerationPlanInput): string {
  if (input.industry?.trim()) {
    return input.industry.trim();
  }

  const matchedIndustry = Object.keys(INDUSTRY_ID_MAP).find((industry) => input.brief.includes(industry));
  return matchedIndustry ?? '通用行业';
}

function industryToId(industry: string): string {
  return INDUSTRY_ID_MAP[industry] ?? slugify(industry);
}

function activeGeneratableModules(context: DemoOfflineContext): DemoGeneratableSlice[] {
  const fromDomc = context.domcModules
    .filter((moduleContract) => moduleContract.capability === 'generatable' && moduleContract.lifecycle === 'active')
    .map((moduleContract) => moduleContract.moduleId);
  return fromDomc.length ? fromDomc : context.safeSlices;
}

function activeCopyOnlyModules(context: DemoOfflineContext): DemoCopiedSlice[] {
  const fromDomc = context.domcModules
    .filter((moduleContract) => moduleContract.capability === 'copyOnly' && moduleContract.lifecycle === 'active')
    .map((moduleContract) => moduleContract.moduleId);
  return fromDomc.length ? fromDomc : context.copiedSlices;
}

function normalizeScope(
  scope: DemoGeneratableSlice[] | undefined,
  context: DemoOfflineContext
): DemoGeneratableSlice[] {
  const available = activeGeneratableModules(context);
  const requested = scope?.length ? [...new Set(scope)] : available;
  const withDependencies =
    requested.includes('simulation') && available.includes('project')
      ? ['project', ...requested]
      : requested;

  return [...new Set(withDependencies)].filter((slice) => available.includes(slice));
}

function normalizeCount(value: number | undefined, fallback: number): number {
  if (typeof value !== 'number' || !Number.isFinite(value)) return fallback;
  return Math.max(1, Math.floor(value));
}

function wantsAllModules(brief: string): boolean {
  return /全亮|全量|全部|所有|全模块|整站/.test(brief);
}

function evidenceForSlice(context: DemoOfflineContext, slice: string): string[] {
  const domcModule = context.domcModules.find((moduleContract) => moduleContract.moduleId === slice);
  const handler = context.handlers.find((item) => item.name === slice);
  const schemaEvidence = 'ruoyi-fastapi-frontend/src/demo/scenarios/schema.ts';
  return [
    ...(domcModule?.evidence ?? []),
    schemaEvidence,
    ...(handler ? [handler.source] : []),
  ];
}

function createPlanBlocker(input: {
  moduleId: string;
  code: string;
  actual?: unknown;
  expected: string;
  fixHint: string;
  missingArtifacts: string[];
  nextActions: string[];
}): DemoOfflineBlockerIssue {
  return {
    path: `domc.modules[${input.moduleId}]`,
    code: input.code,
    severity: 'error',
    actual: input.actual,
    expected: input.expected,
    fixHint: input.fixHint,
    autoRepairable: false,
    gate: 'module-blocker',
    missingArtifacts: input.missingArtifacts,
    nextActions: input.nextActions,
  };
}

export function createGenerationPlan(
  input: CreateGenerationPlanInput,
  context: DemoOfflineContext
): ToolEnvelope<GenerationPlan> {
  const brief = input.brief.trim();
  const industry = inferIndustry({ ...input, brief });
  const industryId = industryToId(industry);
  const scope = normalizeScope(input.scope, context);
  const copiedSlices = activeCopyOnlyModules(context);
  const availableGeneratable = activeGeneratableModules(context);
  const requestedUnsupported = (input.scope ?? []).filter((slice) => !availableGeneratable.includes(slice));
  const targetCounts = {
    projects: normalizeCount(input.targetCounts?.projects, DEFAULT_TARGET_COUNTS.projects),
    versionsPerProject: normalizeCount(
      input.targetCounts?.versionsPerProject,
      DEFAULT_TARGET_COUNTS.versionsPerProject
    ),
    sessionsPerProject: normalizeCount(
      input.targetCounts?.sessionsPerProject,
      DEFAULT_TARGET_COUNTS.sessionsPerProject
    ),
  };
  const scenarioId = input.scenarioId?.trim() || `${industryId}-project-simulation-demo`;
  const scenarioName = input.scenarioName?.trim() || `${industry} project + simulation demo`;
  const trace: GenerationPlan['trace'] = [
    ...scope.map((slice) => ({
      slice,
      status: 'generate' as const,
      evidence: evidenceForSlice(context, slice),
    })),
    ...copiedSlices.map((slice) => ({
      slice,
      status: 'copy' as const,
      evidence: [
        ...evidenceForSlice(context, slice),
        'ruoyi-fastapi-frontend/src/demo/scenarios/default.ts',
      ],
    })),
  ];
  const moduleTrace: NonNullable<GenerationPlan['moduleTrace']> = [
    ...scope.map((moduleId) => ({
      moduleId,
      capability: 'generatable' as const,
      status: 'generate' as const,
      sourcePaths: context.domcModules.find((moduleContract) => moduleContract.moduleId === moduleId)?.sourcePaths ?? [],
      adapterId: context.domcModules.find((moduleContract) => moduleContract.moduleId === moduleId)?.adapterId,
      evidence: evidenceForSlice(context, moduleId),
    })),
    ...copiedSlices.map((moduleId) => ({
      moduleId,
      capability: 'copyOnly' as const,
      status: 'copy' as const,
      sourcePaths: context.domcModules.find((moduleContract) => moduleContract.moduleId === moduleId)?.sourcePaths ?? [],
      evidence: evidenceForSlice(context, moduleId),
    })),
  ];

  requestedUnsupported.forEach((moduleId) => {
    const domcModule = context.domcModules.find((moduleContract) => moduleContract.moduleId === moduleId);
    const blocker = createPlanBlocker({
      moduleId,
      code: domcModule ? 'domc_module_not_generatable' : 'domc_module_missing',
      actual: domcModule ?? moduleId,
      expected: 'Active DOMC generatable module with compatible adapter evidence',
      fixHint: 'Complete module DOMC and adapter DoD before adding it to generation scope.',
      missingArtifacts: [
        `ruoyi-fastapi-frontend/src/demo/domc/modules/${moduleId}.domc.ts`,
        `tools/demo-offline-mcp/src/adapters/${moduleId}/adapter.ts`,
      ],
      nextActions: ['Add DOMC registry coverage.', 'Implement and register a compatible MCP adapter.'],
    });
    trace.push({
      slice: moduleId,
      status: 'blocked',
      evidence: domcModule?.evidence ?? ['ruoyi-fastapi-frontend/src/demo/domc/**'],
      blocker,
    });
    moduleTrace.push({
      moduleId,
      capability: domcModule?.capability ?? 'unsupported',
      status: 'blocked',
      sourcePaths: domcModule?.sourcePaths ?? [],
      adapterId: domcModule?.adapterId,
      evidence: domcModule?.evidence ?? ['ruoyi-fastapi-frontend/src/demo/domc/**'],
      blocker,
    });
  });

  if (wantsAllModules(brief)) {
    const blocker = createPlanBlocker({
      moduleId: 'unregistered-business-modules',
      code: 'domc_all_modules_request_blocked',
      actual: 'all modules requested',
      expected: 'Only active DOMC generatable modules and copyOnly modules may be planned',
      fixHint: 'Add DOMC, IndexedDB mapping, handler coverage, UI journey, invariants, and adapter for every additional business module.',
      missingArtifacts: [
        'DOMC for unregistered business modules',
        'IndexedDB mapping',
        'MSW handler coverage',
        'UI journey',
        'generator adapter',
      ],
      nextActions: ['Implement the module Definition of Done before full-site generation.'],
    });
    trace.push({
      slice: 'unregistered-business-modules',
      status: 'blocked',
      evidence: [
        'docs/specs/demo-offline-domc-registry-and-generator-adapters/requirements.md',
        'ruoyi-fastapi-frontend/src/demo/domc/**',
      ],
      blocker,
    });
    moduleTrace.push({
      moduleId: 'unregistered-business-modules',
      capability: 'unsupported',
      status: 'blocked',
      sourcePaths: [],
      evidence: ['docs/specs/demo-offline-domc-registry-and-generator-adapters/requirements.md'],
      blocker,
    });
  }

  const plan: GenerationPlan = {
    scenarioId,
    scenarioName,
    industry,
    brief,
    scope,
    copiedSlices,
    targetCounts,
    trace,
    moduleTrace,
  };

  return okEnvelope('Created a reviewable demo-offline generation plan.', plan, {
    nextActions: [
      'Ask the external Chat Agent to draft IndustryDataDraft using only generate trace slices.',
      'Keep auth/system copied from the default scenario unless a later spec explicitly expands scope.',
    ],
  });
}
