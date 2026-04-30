import type { CompiledDemoScenarioPackage } from '../types.js';
import { createSemanticIssue, validateAnchorIds } from './blueprint-schema.js';
import type {
  BusinessBlueprint,
  SemanticAnchorBinding,
  SemanticAnchorRef,
  SemanticCoverageSummaryItem,
  SemanticQualityIssue,
  SemanticValidationResult,
} from './types.js';

export interface SemanticCoverageValidationInput {
  blueprint: BusinessBlueprint;
  bindings: SemanticAnchorBinding[];
  scenarioPackage: CompiledDemoScenarioPackage;
}

export interface SemanticCoverageSummary {
  records: SemanticCoverageSummaryItem[];
  primaryRecordCount: number;
  supportingRecordCount: number;
}

function getPathValue(value: unknown, pathName: string): unknown {
  return pathName.split('.').reduce<unknown>((current, segment) => {
    if (current === undefined || current === null) return undefined;
    const arrayMatch = /^([^\[]+)\[(\d+)]$/.exec(segment);
    if (arrayMatch) {
      const parent = typeof current === 'object' ? (current as Record<string, unknown>)[arrayMatch[1]] : undefined;
      return Array.isArray(parent) ? parent[Number(arrayMatch[2])] : undefined;
    }
    if (typeof current !== 'object') return undefined;
    return (current as Record<string, unknown>)[segment];
  }, value);
}

function uniqueAnchorTypes(anchors: SemanticAnchorRef[]): Set<SemanticAnchorRef['type']> {
  return new Set(anchors.map((anchor) => anchor.type));
}

function summarizeBinding(binding: SemanticAnchorBinding): SemanticCoverageSummaryItem {
  return {
    recordPath: binding.recordPath,
    recordKey: binding.recordKey,
    anchorTypes: [...uniqueAnchorTypes(binding.anchors)],
    anchorIds: binding.anchors.map((anchor) => anchor.id),
    anchorLabels: binding.anchors.map((anchor) => anchor.label),
  };
}

function missingPrimaryAnchorIssues(binding: SemanticAnchorBinding, bindingIndex: number): SemanticQualityIssue[] {
  const issues: SemanticQualityIssue[] = [];
  const anchorTypes = uniqueAnchorTypes(binding.anchors);

  if (anchorTypes.size < 3) {
    issues.push(
      createSemanticIssue({
        gate: 'semantic-coverage',
        path: `bindings[${bindingIndex}].anchors`,
        code: 'semantic_anchor_type_minimum_not_met',
        actual: [...anchorTypes],
        expected: 'At least 3 semantic anchor types',
        fixHint:
          'Regenerate anchor bindings from the Blueprint so every primary record includes story/domain, persona, process, risk, and metric anchors.',
      })
    );
  }

  if (!anchorTypes.has('storyBeat') && !anchorTypes.has('domainObject')) {
    issues.push(
      createSemanticIssue({
        gate: 'semantic-coverage',
        path: `bindings[${bindingIndex}].anchors`,
        code: 'semantic_anchor_story_or_domain_missing',
        actual: [...anchorTypes],
        expected: 'storyBeat or domainObject anchor',
        fixHint:
          'Bind each primary record to a Blueprint storyBeat or domainObject before compiling project/simulation data.',
      })
    );
  }

  return issues;
}

function supportSharesAnchor(primary: SemanticAnchorBinding, support: SemanticAnchorBinding): boolean {
  const primaryIds = new Set(primary.anchors.map((anchor) => `${anchor.type}:${anchor.id}`));
  return support.anchors.some((anchor) => primaryIds.has(`${anchor.type}:${anchor.id}`));
}

function supportCategory(pathName: string): 'version' | 'topology' | 'session' | 'message' | 'alarm' | 'fault' | 'event' | 'other' {
  if (pathName.startsWith('project.versions')) return 'version';
  if (pathName.startsWith('project.topologies')) return 'topology';
  if (pathName.startsWith('simulation.sessions')) return 'session';
  if (pathName.startsWith('simulation.messages')) return 'message';
  if (pathName.startsWith('simulation.alarms')) return 'alarm';
  if (pathName.startsWith('simulation.faults')) return 'fault';
  if (pathName.startsWith('simulation.events')) return 'event';
  return 'other';
}

function requiredSupportCategories(
  primary: SemanticAnchorBinding,
  scenarioPackage: CompiledDemoScenarioPackage
): Set<string> {
  const categories = new Set(['version', 'topology', 'session', 'message', 'alarm', 'event']);
  const primaryRecord = getPathValue(scenarioPackage, primary.recordPath);
  const riskLevel =
    primaryRecord && typeof primaryRecord === 'object'
      ? (primaryRecord as Record<string, unknown>).riskLevel
      : undefined;

  if (riskLevel === 'high') {
    categories.add('alarm');
    categories.add('fault');
  }
  return categories;
}

function validatePrimarySupport(input: {
  primary: SemanticAnchorBinding;
  primaryIndex: number;
  byPath: Map<string, SemanticAnchorBinding>;
  scenarioPackage: CompiledDemoScenarioPackage;
}): SemanticQualityIssue[] {
  const issues: SemanticQualityIssue[] = [];
  const supports = input.primary.supports ?? [];
  const categories = new Set<string>();

  for (const supportPath of supports) {
    const support = input.byPath.get(supportPath);
    const packageValue = getPathValue(input.scenarioPackage, supportPath);
    if (packageValue === undefined) {
      issues.push(
        createSemanticIssue({
          gate: 'semantic-coverage',
          path: supportPath,
          code: 'semantic_support_package_path_missing',
          actual: supportPath,
          expected: 'Existing supporting record in compiled DemoScenarioPackage v1',
          fixHint:
            'Repair the Blueprint-to-draft mapping so support paths point at generated versions, topologies, simulation messages, alarms, faults, or events.',
        })
      );
      continue;
    }

    if (!support) {
      issues.push(
        createSemanticIssue({
          gate: 'semantic-coverage',
          path: `bindings[${input.primaryIndex}].supports`,
          code: 'semantic_support_binding_missing',
          actual: supportPath,
          expected: 'Supporting SemanticAnchorBinding for every support path',
          fixHint:
            'Regenerate semantic anchor bindings and include supporting bindings for project versions, topology, and simulation records.',
        })
      );
      continue;
    }

    if (!supportSharesAnchor(input.primary, support)) {
      issues.push(
        createSemanticIssue({
          gate: 'semantic-coverage',
          path: supportPath,
          code: 'semantic_support_anchor_mismatch',
          actual: support.anchors.map((anchor) => `${anchor.type}:${anchor.id}`),
          expected: 'At least one shared semantic anchor with the primary record summary',
          fixHint:
            'Regenerate support records from the same Blueprint story beat, domain object, persona, stage, risk, or metric anchors.',
        })
      );
    }

    categories.add(supportCategory(supportPath));
  }

  for (const category of requiredSupportCategories(input.primary, input.scenarioPackage)) {
    if (categories.has(category)) continue;
    issues.push(
      createSemanticIssue({
        gate: 'semantic-coverage',
        path: `bindings[${input.primaryIndex}].supports`,
        code: 'semantic_support_category_missing',
        actual: [...categories],
        expected: `${category} support record`,
        fixHint:
          'Add Blueprint-derived support records so project summaries are explained by versions, topology, simulation messages, alarms, faults, and events.',
      })
    );
  }

  return issues;
}

export function validateSemanticCoverage(
  input: SemanticCoverageValidationInput
): SemanticValidationResult<SemanticCoverageSummary> {
  const issues: SemanticQualityIssue[] = [...validateAnchorIds(input.blueprint, input.bindings)];
  const byPath = new Map(input.bindings.map((binding) => [binding.recordPath, binding]));
  const primaryBindings = input.bindings.filter((binding) => binding.recordKind === 'primary');

  input.bindings.forEach((binding, bindingIndex) => {
    if (getPathValue(input.scenarioPackage, binding.recordPath) !== undefined) return;
    issues.push(
      createSemanticIssue({
        gate: 'semantic-coverage',
        path: binding.recordPath,
        code: 'semantic_binding_package_path_missing',
        actual: binding.recordPath,
        expected: 'Existing record path in compiled DemoScenarioPackage v1',
        fixHint:
          'Repair compileBlueprintToIndustryDraft() binding paths so semantic report points at generated package records.',
      })
    );

    if (binding.recordKind === 'primary') {
      issues.push(...missingPrimaryAnchorIssues(binding, bindingIndex));
    }
  });

  primaryBindings.forEach((binding) => {
    const bindingIndex = input.bindings.indexOf(binding);
    issues.push(...missingPrimaryAnchorIssues(binding, bindingIndex));
    issues.push(
      ...validatePrimarySupport({
        primary: binding,
        primaryIndex: bindingIndex,
        byPath,
        scenarioPackage: input.scenarioPackage,
      })
    );
  });

  const summary: SemanticCoverageSummary = {
    records: primaryBindings.map(summarizeBinding),
    primaryRecordCount: primaryBindings.length,
    supportingRecordCount: input.bindings.length - primaryBindings.length,
  };

  return {
    valid: !issues.some((issue) => issue.severity === 'error'),
    summary,
    issues,
  };
}
