import type { z } from 'zod';

import { industryDataDraftSchema } from './draft-schema.js';
import type {
  DemoOfflineContext,
  DraftValidationResult,
  GenerationPlan,
  IndustryDataDraft,
  ToolEnvelope,
  ValidationIssue,
} from './types.js';
import { okEnvelope } from './types.js';

export interface ValidateDraftInput {
  plan: GenerationPlan;
  draft: unknown;
  context: DemoOfflineContext;
  autoRepair?: boolean;
}

const PLACEHOLDER_PATTERNS = [/测试项目/, /示例数据/, /张三/, /李四/, /TODO/i, /\bxxx\b/i, /占位/];

function issue(params: ValidationIssue): ValidationIssue {
  return params;
}

function pathFromZodIssue(zodIssue: z.ZodIssue): string {
  return zodIssue.path.length ? zodIssue.path.join('.') : '$';
}

function zodIssuesToValidationIssues(issues: z.ZodIssue[]): ValidationIssue[] {
  return issues.map((zodIssue) =>
    issue({
      path: pathFromZodIssue(zodIssue),
      code: 'invalid_draft_structure',
      severity: 'error',
      actual: zodIssue.message,
      expected: zodIssue.code,
      fixHint: 'Return an IndustryDataDraft that matches the documented draft schema.',
      autoRepairable: false,
    })
  );
}

function cloneDraft(draft: IndustryDataDraft): IndustryDataDraft {
  return JSON.parse(JSON.stringify(draft)) as IndustryDataDraft;
}

function trimStrings(value: unknown): unknown {
  if (typeof value === 'string') {
    return value.trim().replace(/\s+/g, ' ');
  }

  if (Array.isArray(value)) {
    return value.map(trimStrings);
  }

  if (value && typeof value === 'object') {
    return Object.fromEntries(
      Object.entries(value).map(([key, nestedValue]) => [key, trimStrings(nestedValue)])
    );
  }

  return value;
}

function collectText(value: unknown): string {
  if (typeof value === 'string') return value;
  if (Array.isArray(value)) return value.map(collectText).join('\n');
  if (value && typeof value === 'object') return Object.values(value).map(collectText).join('\n');
  return '';
}

function countDuplicates(values: string[]): Set<string> {
  const seen = new Set<string>();
  const duplicated = new Set<string>();

  for (const value of values) {
    if (seen.has(value)) duplicated.add(value);
    seen.add(value);
  }

  return duplicated;
}

function appendAutoRepairIssues(
  originalDraft: IndustryDataDraft,
  repairedDraft: IndustryDataDraft,
  issues: ValidationIssue[],
  repairSummary: string[]
): void {
  const trimmedDraft = trimStrings(repairedDraft) as IndustryDataDraft;

  if (JSON.stringify(trimmedDraft) !== JSON.stringify(repairedDraft)) {
    Object.assign(repairedDraft, trimmedDraft);
    issues.push(
      issue({
        path: '$',
        code: 'trimmed_whitespace',
        severity: 'warning',
        actual: 'Draft contained leading, trailing, or repeated whitespace.',
        expected: 'Normalized text fields',
        fixHint: 'Use the repaired draft with normalized whitespace.',
        autoRepairable: true,
      })
    );
    repairSummary.push('Normalized whitespace in draft text fields.');
  }

  if (!originalDraft.scenario.version?.trim()) {
    repairedDraft.scenario.version = '1.0.0';
    issues.push(
      issue({
        path: 'scenario.version',
        code: 'default_version_applied',
        severity: 'warning',
        actual: originalDraft.scenario.version,
        expected: 'Semantic version string',
        fixHint: 'Use the repaired draft with scenario.version set to 1.0.0.',
        autoRepairable: true,
      })
    );
    repairSummary.push('Defaulted scenario.version to 1.0.0.');
  }

  repairedDraft.projects.forEach((project, index) => {
    if (!project.ownerName?.trim()) {
      project.ownerName = `${project.ownerRole}负责人${index + 1}`;
      issues.push(
        issue({
          path: `projects.${index}.ownerName`,
          code: 'owner_name_defaulted',
          severity: 'warning',
          actual: originalDraft.projects[index]?.ownerName,
          expected: 'Industry-specific owner name',
          fixHint: 'Use the repaired draft or replace ownerName with a specific role owner.',
          autoRepairable: true,
        })
      );
      repairSummary.push(`Defaulted ownerName for project ${project.key}.`);
    }
  });
}

function validateScope(plan: GenerationPlan, context: DemoOfflineContext, issues: ValidationIssue[]): void {
  const unsupported = plan.scope.filter((slice) => !context.safeSlices.includes(slice));

  if (unsupported.length) {
    issues.push(
      issue({
        path: 'plan.scope',
        code: 'scope_not_supported_by_scan',
        severity: 'error',
        actual: unsupported,
        expected: `Safe slices: ${context.safeSlices.join(', ')}`,
        fixHint: 'Regenerate the plan using only slices returned by demo_offline_scan_context.',
        autoRepairable: false,
      })
    );
  }
}

function validateSemantics(
  plan: GenerationPlan,
  draft: IndustryDataDraft,
  issues: ValidationIssue[]
): void {
  const draftText = collectText(draft);

  for (const pattern of PLACEHOLDER_PATTERNS) {
    if (pattern.test(draftText)) {
      issues.push(
        issue({
          path: '$',
          code: 'placeholder_text',
          severity: 'error',
          actual: pattern.source,
          expected: 'Industry-specific project, stage, risk, and remark text',
          fixHint:
            'Replace placeholders such as 测试项目, 示例数据, 张三, 李四, TODO, and xxx with domain-specific content.',
          autoRepairable: false,
        })
      );
    }
  }

  const projectKeys = draft.projects.map((project) => project.key);
  for (const duplicatedKey of countDuplicates(projectKeys)) {
    issues.push(
      issue({
        path: 'projects.key',
        code: 'duplicate_project_key',
        severity: 'error',
        actual: duplicatedKey,
        expected: 'Unique project key values',
        fixHint: 'Make every project.key stable and unique.',
        autoRepairable: false,
      })
    );
  }

  const projectNames = draft.projects.map((project) => project.name);
  for (const duplicatedName of countDuplicates(projectNames)) {
    issues.push(
      issue({
        path: 'projects.name',
        code: 'repeated_project_name',
        severity: 'error',
        actual: duplicatedName,
        expected: 'Distinct project names',
        fixHint: 'Use differentiated project names, regions, stages, or customer contexts.',
        autoRepairable: false,
      })
    );
  }

  if (draft.projects.length < plan.targetCounts.projects) {
    issues.push(
      issue({
        path: 'projects',
        code: 'insufficient_project_count',
        severity: 'error',
        actual: draft.projects.length,
        expected: String(plan.targetCounts.projects),
        fixHint: `Add ${plan.targetCounts.projects - draft.projects.length} more industry-specific projects.`,
        autoRepairable: false,
      })
    );
  }

  const industryHints = [draft.industry.name, plan.industry, ...(draft.industry.keywords ?? [])].filter(Boolean);
  const hasIndustryContext = industryHints.some((hint) => draftText.includes(hint));

  if (!hasIndustryContext) {
    issues.push(
      issue({
        path: 'industry',
        code: 'industry_context_mismatch',
        severity: 'error',
        actual: draft.industry.name,
        expected: `Text should reflect ${plan.industry} via project names, stages, risks, remarks, or keywords.`,
        fixHint: 'Rewrite projects with industry-specific stage names, roles, risks, and operational language.',
        autoRepairable: false,
      })
    );
  }
}

function validateRelationships(draft: IndustryDataDraft, issues: ValidationIssue[]): void {
  draft.projects.forEach((project, projectIndex) => {
    const nodeNames = new Set(project.topology?.nodes?.map((node) => node.name) ?? []);

    project.topology?.links?.forEach((link, linkIndex) => {
      if (!nodeNames.has(link.source) || !nodeNames.has(link.target)) {
        issues.push(
          issue({
            path: `projects.${projectIndex}.topology.links.${linkIndex}`,
            code: 'topology_link_node_missing',
            severity: 'error',
            actual: `${link.source} -> ${link.target}`,
            expected: 'Topology links must reference existing node names.',
            fixHint: 'Update topology.links so source and target match topology.nodes names.',
            autoRepairable: false,
          })
        );
      }
    });
  });
}

export function validateIndustryDataDraft(input: ValidateDraftInput): ToolEnvelope<DraftValidationResult> {
  const parsed = industryDataDraftSchema.safeParse(input.draft);

  if (!parsed.success) {
    const result: DraftValidationResult = {
      valid: false,
      issues: zodIssuesToValidationIssues(parsed.error.issues),
      repairSummary: [],
    };

    return okEnvelope('IndustryDataDraft failed structural validation.', result);
  }

  const originalDraft = parsed.data as IndustryDataDraft;
  const repairedDraft = cloneDraft(originalDraft);
  const issues: ValidationIssue[] = [];
  const repairSummary: string[] = [];

  if (input.autoRepair) {
    appendAutoRepairIssues(originalDraft, repairedDraft, issues, repairSummary);
  }

  const draftToValidate = input.autoRepair ? repairedDraft : originalDraft;

  validateScope(input.plan, input.context, issues);
  validateSemantics(input.plan, draftToValidate, issues);
  validateRelationships(draftToValidate, issues);

  const blockingIssues = issues.filter((item) => item.severity === 'error');
  const result: DraftValidationResult = {
    valid: blockingIssues.length === 0,
    issues,
    repairSummary,
    ...(input.autoRepair && repairSummary.length ? { repairedDraft } : {}),
  };

  return okEnvelope(
    result.valid
      ? 'IndustryDataDraft passed validation.'
      : 'IndustryDataDraft failed validation with structured repair guidance.',
    result,
    {
      nextActions: result.valid
        ? ['Compile the repaired draft or original draft into a candidate scenario.']
        : ['Ask the external Chat Agent to fix the draft using the returned path/code/fixHint issues.'],
    }
  );
}
