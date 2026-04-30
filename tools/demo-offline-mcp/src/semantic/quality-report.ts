import type {
  BusinessBlueprint,
  SemanticAnchorBinding,
  SemanticAnchorBindingSummaryItem,
  SemanticCoverageSummaryItem,
  SemanticQualityIssue,
  SemanticQualityReport,
  SemanticQualitySummary,
} from './types.js';
import { summarizeBusinessBlueprint } from './blueprint-schema.js';

export interface CreateSemanticQualityReportInput {
  scenarioId: string;
  topicKey: string;
  seed: string;
  generatorVersion: string;
  blueprint: BusinessBlueprint;
  diversitySummary: Record<string, unknown>;
  semanticCoverageSummary: SemanticCoverageSummaryItem[];
  bindings: SemanticAnchorBinding[];
  issues: SemanticQualityIssue[];
}

function summarizeQuality(issues: SemanticQualityIssue[]): SemanticQualitySummary {
  const errorCount = issues.filter((issue) => issue.severity === 'error').length;
  const warningCount = issues.filter((issue) => issue.severity === 'warning').length;

  return {
    blueprintValid: !issues.some(
      (issue) =>
        issue.severity === 'error' &&
        (issue.gate === 'blueprint-schema' || issue.gate === 'blueprint-semantic-minimum')
    ),
    diversityValid: !issues.some((issue) => issue.severity === 'error' && issue.gate === 'diversity'),
    semanticCoverageValid: !issues.some((issue) => issue.severity === 'error' && issue.gate === 'semantic-coverage'),
    issueCount: issues.length,
    warningCount,
    errorCount,
  };
}

function summarizeBinding(binding: SemanticAnchorBinding): SemanticAnchorBindingSummaryItem {
  const anchorTypes = [...new Set(binding.anchors.map((anchor) => anchor.type))];

  return {
    recordKind: binding.recordKind,
    module: binding.module,
    recordPath: binding.recordPath,
    recordKey: binding.recordKey,
    anchorTypes,
    anchorIds: binding.anchors.map((anchor) => anchor.id),
    anchorLabels: binding.anchors.map((anchor) => anchor.label),
    supports: binding.supports ?? [],
  };
}

export function createSemanticQualityReport(input: CreateSemanticQualityReportInput): SemanticQualityReport {
  return {
    schemaVersion: 1,
    scenarioId: input.scenarioId,
    topicKey: input.topicKey,
    seed: input.seed,
    generatorVersion: input.generatorVersion,
    summary: summarizeQuality(input.issues),
    blueprintSummary: summarizeBusinessBlueprint(input.blueprint),
    diversitySummary: input.diversitySummary,
    semanticCoverageSummary: input.semanticCoverageSummary,
    anchorBindingSummary: input.bindings.map(summarizeBinding),
    issues: input.issues,
  };
}
