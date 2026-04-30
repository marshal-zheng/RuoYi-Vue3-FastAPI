import type { CompiledDemoScenarioPackage, IndustryDataDraft } from '../types.js';
import { createSemanticIssue } from './blueprint-schema.js';
import type { BusinessBlueprint, SemanticQualityIssue, SemanticValidationResult } from './types.js';

export interface DiversityValidationInput {
  blueprint: BusinessBlueprint;
  draft: IndustryDataDraft;
  scenarioPackage?: CompiledDemoScenarioPackage;
}

interface DimensionSummary {
  duplicateRatio: number;
  uniqueCount: number;
  totalCount: number;
  templateSimilarity: number;
  severity: 'ok' | 'warning' | 'error';
}

export interface DiversitySummary {
  dimensions: Record<string, DimensionSummary>;
}

const CRITICAL_DIMENSIONS = new Set([
  'nameTitle',
  'remark',
  'descriptionRemark',
  'risk',
  'stage',
  'owner',
  'departmentPersona',
  'keyMetrics',
  'timelineCue',
  'packageCreateByDepartment',
]);

function normalizeText(value: string): string {
  return value
    .toLowerCase()
    .replace(/\d+/g, '#')
    .replace(/[^\p{Letter}\p{Number}#]+/gu, '')
    .trim();
}

function duplicateRatio(values: string[]): number {
  if (values.length <= 1) return 0;
  const normalized = values.map(normalizeText).filter(Boolean);
  if (!normalized.length) return 0;
  return (normalized.length - new Set(normalized).size) / normalized.length;
}

function bigrams(value: string): Set<string> {
  const normalized = normalizeText(value);
  if (normalized.length <= 1) return new Set(normalized ? [normalized] : []);
  const result = new Set<string>();
  for (let index = 0; index < normalized.length - 1; index += 1) {
    result.add(normalized.slice(index, index + 2));
  }
  return result;
}

function jaccard(left: Set<string>, right: Set<string>): number {
  if (!left.size && !right.size) return 0;
  const intersection = [...left].filter((item) => right.has(item)).length;
  return intersection / new Set([...left, ...right]).size;
}

function maxPairwiseSimilarity(values: string[]): number {
  const uniqueValues = [...new Set(values.map(normalizeText).filter(Boolean))];
  let max = 0;
  for (let left = 0; left < uniqueValues.length; left += 1) {
    for (let right = left + 1; right < uniqueValues.length; right += 1) {
      max = Math.max(max, jaccard(bigrams(uniqueValues[left]), bigrams(uniqueValues[right])));
    }
  }
  return max;
}

function severityForDimension(
  dimension: string,
  ratio: number,
  similarity: number
): DimensionSummary['severity'] {
  if ((ratio >= 0.75 || similarity >= 0.85) && CRITICAL_DIMENSIONS.has(dimension)) return 'error';
  if (ratio >= 0.5 || similarity >= 0.85) return 'warning';
  return 'ok';
}

function issueForDimension(input: {
  dimension: string;
  severity: 'warning' | 'error';
  duplicateRatio: number;
  templateSimilarity: number;
  values: string[];
}): SemanticQualityIssue {
  return createSemanticIssue({
    gate: 'diversity',
    path: `draft.projects.${input.dimension}`,
    code: input.severity === 'error' ? 'semantic_diversity_threshold_error' : 'semantic_diversity_threshold_warning',
    severity: input.severity,
    actual: {
      duplicateRatio: Number(input.duplicateRatio.toFixed(3)),
      templateSimilarity: Number(input.templateSimilarity.toFixed(3)),
      samples: input.values.slice(0, 4),
    },
    expected:
      'Critical dimensions normalized duplicate ratio < 0.75 and template similarity < 0.85; warning below error threshold should be reviewed.',
    fixHint:
      'Return to the Business Blueprint and diversify story beats, domain objects, personas, process stages, risk types, or metric definitions before regenerating the v2 release.',
  });
}

function collectPackageTexts(scenarioPackage?: CompiledDemoScenarioPackage): Record<string, string[]> {
  if (!scenarioPackage) return {};

  return {
    packageProjectNames: scenarioPackage.project.projects.map((project) => String(project.projectName ?? '')),
    packageCreateByDepartment: scenarioPackage.project.projects.map((project) =>
      [project.department, project.createBy].map((value) => String(value ?? '')).join('-')
    ),
    packageEvents: scenarioPackage.simulation.events.map((event) => String(event.message ?? event.eventType ?? '')),
    packageMessages: scenarioPackage.simulation.messages.map((message) => String(message.content ?? '')),
  };
}

function summarizeDimension(dimension: string, values: string[]): DimensionSummary {
  const ratio = duplicateRatio(values);
  const similarity = maxPairwiseSimilarity(values);

  return {
    duplicateRatio: Number(ratio.toFixed(3)),
    uniqueCount: new Set(values.map(normalizeText).filter(Boolean)).size,
    totalCount: values.filter(Boolean).length,
    templateSimilarity: Number(similarity.toFixed(3)),
    severity: severityForDimension(dimension, ratio, similarity),
  };
}

export function validateDiversity(
  input: DiversityValidationInput
): SemanticValidationResult<DiversitySummary> {
  const dimensionValues: Record<string, string[]> = {
    nameTitle: input.draft.projects.map((project) => project.name),
    remark: input.draft.projects.map((project) => project.remark),
    descriptionRemark: input.draft.projects.map((project) =>
      [project.remark, project.risk, project.simulation?.messages?.join('\n') ?? ''].join('\n')
    ),
    owner: input.draft.projects.map((project) => `${project.ownerRole}-${project.ownerName ?? ''}`),
    departmentPersona: input.draft.projects.map((project) =>
      [project.departmentName ?? '', project.ownerRole, project.ownerName ?? ''].join('-')
    ),
    stage: input.draft.projects.map((project) => project.stage),
    risk: input.draft.projects.map((project) => project.risk),
    keyMetrics: input.draft.projects.map((project) => (project.keyMetrics ?? []).map((metric) => metric.name).join('|')),
    timelineCue: input.draft.projects.map((project) =>
      [
        project.stage,
        project.versions?.map((version) => version.summary ?? version.name).join('|') ?? '',
        project.simulation?.events?.join('|') ?? '',
      ].join('|')
    ),
    ...collectPackageTexts(input.scenarioPackage),
  };
  const summary: DiversitySummary = {
    dimensions: Object.fromEntries(
      Object.entries(dimensionValues).map(([dimension, values]) => [dimension, summarizeDimension(dimension, values)])
    ),
  };
  const issues = Object.entries(summary.dimensions)
    .filter(([, dimensionSummary]) => dimensionSummary.severity !== 'ok')
    .map(([dimension, dimensionSummary]) =>
      issueForDimension({
        dimension,
        severity: dimensionSummary.severity as 'warning' | 'error',
        duplicateRatio: dimensionSummary.duplicateRatio,
        templateSimilarity: dimensionSummary.templateSimilarity,
        values: dimensionValues[dimension],
      })
    );

  const lowRiskBlueprintExplanation =
    input.blueprint.riskTypes.length >= 4 &&
    input.blueprint.processStages.length >= 5 &&
    input.blueprint.personas.length >= 3;

  const adjustedIssues = issues.map((issue) => {
    if (issue.severity === 'error' || !lowRiskBlueprintExplanation) return issue;
    return {
      ...issue,
      fixHint: `${issue.fixHint} The current Blueprint has enough semantic sources, so this warning can be resolved by improving the Blueprint-to-draft mapping if it is customer-visible.`,
    };
  });

  return {
    valid: !adjustedIssues.some((issue) => issue.severity === 'error'),
    summary,
    issues: adjustedIssues,
  };
}
