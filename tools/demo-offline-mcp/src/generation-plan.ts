import type {
  DemoCopiedSlice,
  DemoGeneratableSlice,
  DemoOfflineContext,
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

const DEFAULT_SCOPE: DemoGeneratableSlice[] = ['project', 'simulation'];
const COPIED_SLICES: DemoCopiedSlice[] = ['auth', 'system'];
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

function normalizeScope(scope: DemoGeneratableSlice[] | undefined): DemoGeneratableSlice[] {
  const requested = scope?.length ? [...new Set(scope)] : DEFAULT_SCOPE;
  const normalized = requested.includes('simulation')
    ? (['project', ...requested] as DemoGeneratableSlice[])
    : requested;

  return [...new Set(normalized)].filter((slice): slice is DemoGeneratableSlice =>
    DEFAULT_SCOPE.includes(slice as DemoGeneratableSlice)
  );
}

function normalizeCount(value: number | undefined, fallback: number): number {
  if (typeof value !== 'number' || !Number.isFinite(value)) return fallback;
  return Math.max(1, Math.floor(value));
}

function wantsAllModules(brief: string): boolean {
  return /全亮|全量|全部|所有|全模块|整站/.test(brief);
}

function evidenceForSlice(context: DemoOfflineContext, slice: string): string[] {
  const handler = context.handlers.find((item) => item.name === slice);
  const schemaEvidence = 'ruoyi-fastapi-frontend/src/demo/scenarios/schema.ts';
  return [schemaEvidence, ...(handler ? [handler.source] : [])];
}

export function createGenerationPlan(
  input: CreateGenerationPlanInput,
  context: DemoOfflineContext
): ToolEnvelope<GenerationPlan> {
  const brief = input.brief.trim();
  const industry = inferIndustry({ ...input, brief });
  const industryId = industryToId(industry);
  const scope = normalizeScope(input.scope);
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
    ...COPIED_SLICES.map((slice) => ({
      slice,
      status: 'copy' as const,
      evidence: [
        'ruoyi-fastapi-frontend/src/demo/scenarios/default.ts',
        'docs/specs/demo-offline-data-mcp/requirements.md',
      ],
    })),
  ];

  if (wantsAllModules(brief)) {
    trace.push({
      slice: 'p0-unsupported-business-modules',
      status: 'unsupported',
      evidence: [
        'P0 scan scope excludes src/views/**, src/api/**, and backend business code.',
        'Only project + simulation have safe generated evidence in src/demo/**.',
      ],
    });
  }

  const plan: GenerationPlan = {
    scenarioId,
    scenarioName,
    industry,
    brief,
    scope,
    copiedSlices: [...COPIED_SLICES],
    targetCounts,
    trace,
  };

  return okEnvelope('Created a reviewable demo-offline generation plan.', plan, {
    nextActions: [
      'Ask the external Chat Agent to draft IndustryDataDraft using only generate trace slices.',
      'Keep auth/system copied from the default scenario unless a later spec explicitly expands scope.',
    ],
  });
}
