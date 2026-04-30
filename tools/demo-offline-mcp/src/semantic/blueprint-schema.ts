import type { z } from 'zod';
import { z as zod } from 'zod';

import { createIssue } from '../errors.js';
import type {
  BusinessBlueprint,
  SemanticAnchorBinding,
  SemanticAnchorType,
  SemanticBlueprintSummary,
  SemanticGate,
  SemanticQualityIssue,
} from './types.js';

export const blueprintMinimums = {
  domainObjects: 5,
  personas: 3,
  departments: 2,
  processStages: 5,
  riskTypes: 4,
  metricDefinitions: 4,
} as const;

const idSchema = zod.string().min(1);
const labelSchema = zod.string().min(1);

const domainObjectSchema = zod.object({
  id: idSchema,
  label: labelSchema,
  description: zod.string().min(1),
  attributes: zod.array(zod.string().min(1)).optional(),
});

const departmentSchema = zod.object({
  id: idSchema,
  label: labelSchema,
  responsibility: zod.string().min(1),
});

const personaSchema = zod.object({
  id: idSchema,
  name: zod.string().min(1),
  role: zod.string().min(1),
  departmentId: idSchema,
  actions: zod.array(zod.string().min(1)).min(1),
});

const processStageSchema = zod.object({
  id: idSchema,
  label: labelSchema,
  sequence: zod.number().int().min(1),
  description: zod.string().min(1),
  action: zod.string().min(1),
});

const riskTypeSchema = zod.object({
  id: idSchema,
  label: labelSchema,
  severity: zod.enum(['low', 'medium', 'high']),
  description: zod.string().min(1),
  riskSignals: zod.array(zod.string().min(1)).min(1),
});

const metricDefinitionSchema = zod.object({
  id: idSchema,
  name: zod.string().min(1),
  description: zod.string().min(1),
  unit: zod.string().min(1),
  valueSamples: zod.array(zod.string().min(1)).min(1),
  trend: zod.enum(['up', 'down', 'flat']).optional(),
});

const storyBeatSchema = zod.object({
  id: idSchema,
  title: zod.string().min(1),
  summary: zod.string().min(1),
  domainObjectId: idSchema,
  departmentId: idSchema,
  personaId: idSchema,
  processStageId: idSchema,
  riskTypeId: idSchema,
  metricDefinitionIds: zod.array(idSchema).min(1),
  outcome: zod.string().min(1),
});

export const businessBlueprintSchema = zod.object({
  schemaVersion: zod.literal(1),
  topic: zod.string().min(1),
  businessDescription: zod.string().optional(),
  topicKey: zod.string().min(1),
  seed: zod.string().min(1),
  contractFingerprint: zod.string().min(1),
  generatorVersion: zod.string().min(1),
  industry: zod.object({
    name: zod.string().min(1),
    keywords: zod.array(zod.string().min(1)).min(1),
  }),
  domainObjects: zod.array(domainObjectSchema),
  departments: zod.array(departmentSchema),
  personas: zod.array(personaSchema),
  processStages: zod.array(processStageSchema),
  riskTypes: zod.array(riskTypeSchema),
  metricDefinitions: zod.array(metricDefinitionSchema),
  storyBeats: zod.array(storyBeatSchema),
});

export type BusinessBlueprintSchema = z.infer<typeof businessBlueprintSchema>;

function pathFromZodIssue(issue: z.ZodIssue): string {
  return issue.path.length ? issue.path.join('.') : '$';
}

export function createSemanticIssue(params: {
  gate: SemanticGate;
  path: string;
  code: string;
  severity?: 'error' | 'warning';
  actual?: unknown;
  expected: string;
  fixHint: string;
  autoRepairable?: boolean;
}): SemanticQualityIssue {
  return {
    ...createIssue({
      path: params.path,
      code: params.code,
      severity: params.severity ?? 'error',
      actual: params.actual,
      expected: params.expected,
      fixHint: params.fixHint,
      autoRepairable: params.autoRepairable ?? false,
    }),
    gate: params.gate,
  };
}

function zodIssueToSemanticIssue(issue: z.ZodIssue): SemanticQualityIssue {
  const path = pathFromZodIssue(issue);
  return createSemanticIssue({
    gate: 'blueprint-schema',
    path,
    code: 'blueprint_schema_invalid',
    actual: issue.message,
    expected: issue.code,
    fixHint: `Repair BusinessBlueprint.${path} before compiling semantic demo data.`,
  });
}

function addMinimumIssue(
  issues: SemanticQualityIssue[],
  blueprint: BusinessBlueprint,
  field: keyof Pick<
    BusinessBlueprint,
    'domainObjects' | 'personas' | 'departments' | 'processStages' | 'riskTypes' | 'metricDefinitions' | 'storyBeats'
  >,
  minimum: number
): void {
  const actual = blueprint[field].length;
  if (actual >= minimum) return;

  issues.push(
    createSemanticIssue({
      gate: 'blueprint-semantic-minimum',
      path: field,
      code: 'blueprint_semantic_minimum_not_met',
      actual,
      expected: `At least ${minimum} item(s)`,
      fixHint: `Add more ${field} in the Business Blueprint, then regenerate the v2 release from Blueprint rather than editing runtime JSON by hand.`,
    })
  );
}

function addDuplicateIdIssues(
  issues: SemanticQualityIssue[],
  values: Array<{ id: string }>,
  path: string
): void {
  const seen = new Set<string>();
  values.forEach((value, index) => {
    if (!seen.has(value.id)) {
      seen.add(value.id);
      return;
    }

    issues.push(
      createSemanticIssue({
        gate: 'blueprint-schema',
        path: `${path}[${index}].id`,
        code: 'blueprint_duplicate_id',
        actual: value.id,
        expected: 'Unique semantic entity id',
        fixHint: `Make ${path}[${index}].id unique in the Blueprint before compiling draft data.`,
      })
    );
  });
}

function addReferenceIssue(
  issues: SemanticQualityIssue[],
  path: string,
  actual: unknown,
  expected: string
): void {
  issues.push(
    createSemanticIssue({
      gate: 'blueprint-schema',
      path,
      code: 'blueprint_reference_missing',
      actual,
      expected,
      fixHint: `Repair ${path} so story beats and personas reference existing Blueprint entities.`,
    })
  );
}

function validateBlueprintReferences(blueprint: BusinessBlueprint): SemanticQualityIssue[] {
  const issues: SemanticQualityIssue[] = [];
  const domainObjectIds = new Set(blueprint.domainObjects.map((item) => item.id));
  const departmentIds = new Set(blueprint.departments.map((item) => item.id));
  const personaIds = new Set(blueprint.personas.map((item) => item.id));
  const processStageIds = new Set(blueprint.processStages.map((item) => item.id));
  const riskTypeIds = new Set(blueprint.riskTypes.map((item) => item.id));
  const metricDefinitionIds = new Set(blueprint.metricDefinitions.map((item) => item.id));

  addDuplicateIdIssues(issues, blueprint.domainObjects, 'domainObjects');
  addDuplicateIdIssues(issues, blueprint.departments, 'departments');
  addDuplicateIdIssues(issues, blueprint.personas, 'personas');
  addDuplicateIdIssues(issues, blueprint.processStages, 'processStages');
  addDuplicateIdIssues(issues, blueprint.riskTypes, 'riskTypes');
  addDuplicateIdIssues(issues, blueprint.metricDefinitions, 'metricDefinitions');
  addDuplicateIdIssues(issues, blueprint.storyBeats, 'storyBeats');

  blueprint.personas.forEach((persona, index) => {
    if (!departmentIds.has(persona.departmentId)) {
      addReferenceIssue(
        issues,
        `personas[${index}].departmentId`,
        persona.departmentId,
        'Existing departments[].id'
      );
    }
  });

  blueprint.storyBeats.forEach((storyBeat, index) => {
    if (!domainObjectIds.has(storyBeat.domainObjectId)) {
      addReferenceIssue(
        issues,
        `storyBeats[${index}].domainObjectId`,
        storyBeat.domainObjectId,
        'Existing domainObjects[].id'
      );
    }
    if (!departmentIds.has(storyBeat.departmentId)) {
      addReferenceIssue(
        issues,
        `storyBeats[${index}].departmentId`,
        storyBeat.departmentId,
        'Existing departments[].id'
      );
    }
    if (!personaIds.has(storyBeat.personaId)) {
      addReferenceIssue(issues, `storyBeats[${index}].personaId`, storyBeat.personaId, 'Existing personas[].id');
    }
    if (!processStageIds.has(storyBeat.processStageId)) {
      addReferenceIssue(
        issues,
        `storyBeats[${index}].processStageId`,
        storyBeat.processStageId,
        'Existing processStages[].id'
      );
    }
    if (!riskTypeIds.has(storyBeat.riskTypeId)) {
      addReferenceIssue(issues, `storyBeats[${index}].riskTypeId`, storyBeat.riskTypeId, 'Existing riskTypes[].id');
    }

    storyBeat.metricDefinitionIds.forEach((metricId, metricIndex) => {
      if (!metricDefinitionIds.has(metricId)) {
        addReferenceIssue(
          issues,
          `storyBeats[${index}].metricDefinitionIds[${metricIndex}]`,
          metricId,
          'Existing metricDefinitions[].id'
        );
      }
    });
  });

  return issues;
}

export function summarizeBusinessBlueprint(blueprint: BusinessBlueprint): SemanticBlueprintSummary {
  return {
    domainObjectCount: blueprint.domainObjects.length,
    personaCount: blueprint.personas.length,
    departmentCount: blueprint.departments.length,
    processStageCount: blueprint.processStages.length,
    riskTypeCount: blueprint.riskTypes.length,
    metricDefinitionCount: blueprint.metricDefinitions.length,
    storyBeatCount: blueprint.storyBeats.length,
  };
}

export function validateBusinessBlueprint(
  value: unknown,
  options: { projectCount: number }
): { valid: boolean; blueprint?: BusinessBlueprint; issues: SemanticQualityIssue[]; summary?: SemanticBlueprintSummary } {
  const parsed = businessBlueprintSchema.safeParse(value);

  if (!parsed.success) {
    return {
      valid: false,
      issues: parsed.error.issues.map(zodIssueToSemanticIssue),
    };
  }

  const blueprint = parsed.data as BusinessBlueprint;
  const issues: SemanticQualityIssue[] = [];

  addMinimumIssue(issues, blueprint, 'domainObjects', blueprintMinimums.domainObjects);
  addMinimumIssue(issues, blueprint, 'personas', blueprintMinimums.personas);
  addMinimumIssue(issues, blueprint, 'departments', blueprintMinimums.departments);
  addMinimumIssue(issues, blueprint, 'processStages', blueprintMinimums.processStages);
  addMinimumIssue(issues, blueprint, 'riskTypes', blueprintMinimums.riskTypes);
  addMinimumIssue(issues, blueprint, 'metricDefinitions', blueprintMinimums.metricDefinitions);
  addMinimumIssue(issues, blueprint, 'storyBeats', Math.max(1, Math.floor(options.projectCount)));
  issues.push(...validateBlueprintReferences(blueprint));

  return {
    valid: !issues.some((issue) => issue.severity === 'error'),
    blueprint,
    issues,
    summary: summarizeBusinessBlueprint(blueprint),
  };
}

export function createSemanticEntityId(kind: string, label: string, index: number): string {
  return `${kind}-${index + 1}-${Array.from(label)
    .map((char) => char.charCodeAt(0).toString(36))
    .join('')
    .slice(0, 8)}`;
}

export function anchorTypeToBlueprintIds(
  blueprint: BusinessBlueprint,
  type: SemanticAnchorType
): Set<string> {
  switch (type) {
    case 'storyBeat':
      return new Set(blueprint.storyBeats.map((item) => item.id));
    case 'domainObject':
      return new Set(blueprint.domainObjects.map((item) => item.id));
    case 'persona':
      return new Set(blueprint.personas.map((item) => item.id));
    case 'role':
      return new Set(blueprint.personas.map((item) => item.role));
    case 'processStage':
      return new Set(blueprint.processStages.map((item) => item.id));
    case 'riskType':
      return new Set(blueprint.riskTypes.map((item) => item.id));
    case 'metricDefinition':
      return new Set(blueprint.metricDefinitions.map((item) => item.id));
  }
}

export function validateAnchorIds(
  blueprint: BusinessBlueprint,
  bindings: SemanticAnchorBinding[]
): SemanticQualityIssue[] {
  const issues: SemanticQualityIssue[] = [];

  bindings.forEach((binding, bindingIndex) => {
    binding.anchors.forEach((anchor, anchorIndex) => {
      const validIds = anchorTypeToBlueprintIds(blueprint, anchor.type);
      if (validIds.has(anchor.id)) return;

      issues.push(
        createSemanticIssue({
          gate: 'semantic-coverage',
          path: `bindings[${bindingIndex}].anchors[${anchorIndex}].id`,
          code: 'semantic_anchor_id_missing',
          actual: `${anchor.type}:${anchor.id}`,
          expected: `Existing ${anchor.type} anchor id from Business Blueprint`,
          fixHint:
            'Regenerate semantic anchor bindings from the Blueprint or repair the Blueprint entity id before writing a runtime package.',
        })
      );
    });
  });

  return issues;
}
