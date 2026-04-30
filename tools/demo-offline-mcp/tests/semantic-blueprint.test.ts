import { describe, expect, it } from 'vitest';

import { compileScenarioPackage } from '../src/compiler.js';
import { createOfflineStaticPlan, GENERATOR_VERSION } from '../src/offline-static/generate.js';
import { createStableSeed, normalizeTopicKey } from '../src/offline-static/topic.js';
import {
  compileBlueprintToIndustryDraft,
  generateDeterministicBusinessBlueprint,
  validateBusinessBlueprint,
  validateDiversity,
  validateSemanticCoverage,
} from '../src/semantic/index.js';
import type { BusinessBlueprint } from '../src/semantic/types.js';
import type { CompiledDemoScenarioPackage } from '../src/types.js';

function createBlueprint(input: { topic: string; businessDescription: string; projectCount?: number }): BusinessBlueprint {
  const topicKey = normalizeTopicKey(input.topic, input.businessDescription);
  const seed = createStableSeed({
    topicKey,
    businessDescription: input.businessDescription,
    contractFingerprint: 'semantic-unit-contract',
    generatorVersion: GENERATOR_VERSION,
  });

  return generateDeterministicBusinessBlueprint({
    topic: input.topic,
    businessDescription: input.businessDescription,
    topicKey,
    seed,
    contractFingerprint: 'semantic-unit-contract',
    generatorVersion: GENERATOR_VERSION,
    projectCount: input.projectCount ?? 4,
  });
}

function createDefaultScenarioPackage(): CompiledDemoScenarioPackage {
  return {
    schemaVersion: 1,
    scenario: {
      id: 'default',
      name: 'Default',
      version: '1.0.0',
      fingerprint: 'default',
      seed: 'default',
    },
    auth: { accounts: [], roles: [], permissions: [] },
    system: { menus: [], dictTypes: [], dicts: [], departments: [], posts: [], users: [] },
    project: { projects: [], versions: [], topologies: [] },
    simulation: {
      sessions: [],
      messages: [],
      bandwidth: [],
      alarms: [],
      faults: [],
      events: [],
      streamFrames: [],
    },
  };
}

async function compileSemanticPackage(blueprint: BusinessBlueprint) {
  const plan = createOfflineStaticPlan({
    topic: blueprint.topic,
    businessDescription: blueprint.businessDescription,
    topicKey: blueprint.topicKey,
    scenarioId: `${blueprint.topicKey}-semantic-unit`,
    scenarioName: `${blueprint.topic} semantic unit`,
    projectCount: blueprint.storyBeats.length,
  });
  const compiledDraft = compileBlueprintToIndustryDraft({
    blueprint,
    scenarioId: plan.scenarioId,
    scenarioName: plan.scenarioName,
    projectCount: plan.targetCounts.projects,
  });
  const compiledPackage = await compileScenarioPackage({
    plan,
    draft: compiledDraft.draft,
    defaultScenarioPackage: createDefaultScenarioPackage(),
  });

  expect(compiledPackage.ok).toBe(true);

  return {
    plan,
    ...compiledDraft,
    scenarioPackage: compiledPackage.data!.scenarioPackage,
  };
}

describe('semantic Business Blueprint layer', () => {
  it('returns structured schema and semantic-minimum issues for invalid blueprints', () => {
    const schemaResult = validateBusinessBlueprint({ schemaVersion: 1 }, { projectCount: 4 });

    expect(schemaResult.valid).toBe(false);
    expect(schemaResult.issues).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          gate: 'blueprint-schema',
          code: 'blueprint_schema_invalid',
          path: 'topic',
        }),
      ])
    );

    const blueprint = createBlueprint({
      topic: '无人机巡检任务管理',
      businessDescription: '突出航线排程、热成像缺陷复核和空域审批。',
    });
    blueprint.domainObjects = blueprint.domainObjects.slice(0, 2);
    blueprint.storyBeats[0].domainObjectId = 'missing-domain-object';
    const minimumResult = validateBusinessBlueprint(blueprint, { projectCount: 4 });

    expect(minimumResult.valid).toBe(false);
    expect(minimumResult.issues).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          gate: 'blueprint-semantic-minimum',
          code: 'blueprint_semantic_minimum_not_met',
          path: 'domainObjects',
        }),
        expect.objectContaining({
          gate: 'blueprint-schema',
          code: 'blueprint_reference_missing',
          path: 'storyBeats[0].domainObjectId',
        }),
      ])
    );
  });

  it('generates deterministic blueprints and reacts to businessDescription changes', () => {
    const first = createBlueprint({
      topic: '无人机巡检任务管理',
      businessDescription: '突出航线排程、热成像缺陷复核和空域审批。',
    });
    const second = createBlueprint({
      topic: '无人机巡检任务管理',
      businessDescription: '突出航线排程、热成像缺陷复核和空域审批。',
    });
    const changed = createBlueprint({
      topic: '无人机巡检任务管理',
      businessDescription: '突出电池健康、返航余量和恶劣天气插队。',
    });

    expect(second).toEqual(first);
    expect(changed.domainObjects.map((item) => item.label)).not.toEqual(first.domainObjects.map((item) => item.label));
    expect(changed.storyBeats.map((item) => item.summary).join('\n')).not.toEqual(
      first.storyBeats.map((item) => item.summary).join('\n')
    );
  });

  it('compiles Blueprint into project/simulation draft and generic anchor bindings', async () => {
    const blueprint = createBlueprint({
      topic: '二手电脑回收管理',
      businessDescription: '突出回收评估、检测、报价、数据清除证明和环保流转。',
    });
    const validation = validateBusinessBlueprint(blueprint, { projectCount: 4 });

    expect(validation.valid).toBe(true);

    const { draft, bindings, scenarioPackage } = await compileSemanticPackage(blueprint);

    expect(draft.projects[0].keyMetrics?.map((metric) => metric.name)).not.toEqual(['处理量', '闭环率']);
    expect(draft.projects[0].departmentName).toBeTruthy();
    expect(draft.projects[0].simulation?.messages?.join('\n')).toContain('数据');
    expect(bindings.find((binding) => binding.recordKind === 'primary')?.anchors.length).toBeGreaterThanOrEqual(3);
    expect(new Set(scenarioPackage.project.projects.map((project) => project.createBy)).size).toBeGreaterThan(1);
    expect(scenarioPackage.project.projects[0]).toHaveProperty('department');

    const diversity = validateDiversity({ blueprint, draft, scenarioPackage });
    const coverage = validateSemanticCoverage({ blueprint, bindings, scenarioPackage });

    expect(diversity.issues.filter((issue) => issue.severity === 'error')).toEqual([]);
    expect(coverage.valid).toBe(true);
    expect(coverage.summary.records[0]).toMatchObject({
      recordPath: 'project.projects[0]',
      anchorTypes: expect.arrayContaining(['storyBeat', 'domainObject', 'persona', 'processStage']),
    });
  });

  it('detects diversity errors, warnings, and coverage gaps with structured fix hints', async () => {
    const blueprint = createBlueprint({
      topic: '无人机巡检任务管理',
      businessDescription: '突出航线排程、热成像缺陷复核和空域审批。',
    });
    const { draft, bindings, scenarioPackage } = await compileSemanticPackage(blueprint);
    const repetitiveDraft = {
      ...draft,
      projects: draft.projects.map((project) => ({
        ...project,
        stage: '同一阶段',
        ownerRole: '同一负责人',
        ownerName: '同一人员',
        risk: '同一风险描述。',
        remark: '同一备注描述。',
      })),
    };
    const warningDraft = {
      ...draft,
      projects: draft.projects.map((project, index) => ({
        ...project,
        stage: index < 2 ? '阶段A' : '阶段B',
      })),
    };
    const repeatedRemarkDraft = {
      ...draft,
      projects: draft.projects.map((project) => ({
        ...project,
        remark: '同一备注描述。',
      })),
    };
    const badBindings = JSON.parse(JSON.stringify(bindings)) as typeof bindings;
    badBindings[0].anchors = badBindings[0].anchors.slice(0, 2);
    badBindings[0].supports = ['simulation.messages[999]'];
    badBindings[0].anchors[0].id = 'missing-anchor';
    const missingAlarmBindings = JSON.parse(JSON.stringify(bindings)) as typeof bindings;
    missingAlarmBindings.forEach((binding) => {
      if (binding.recordKind === 'primary') {
        binding.supports = binding.supports?.filter((supportPath) => !supportPath.startsWith('simulation.alarms'));
      }
    });
    const missingFaultBindings = (JSON.parse(JSON.stringify(bindings)) as typeof bindings)
      .filter((binding) => !binding.recordPath.startsWith('simulation.faults'))
      .map((binding) => ({
        ...binding,
        supports:
          binding.recordKind === 'primary'
            ? binding.supports?.filter((supportPath) => !supportPath.startsWith('simulation.faults'))
            : binding.supports,
      }));

    expect(validateDiversity({ blueprint, draft: repetitiveDraft, scenarioPackage }).issues).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          gate: 'diversity',
          severity: 'error',
          fixHint: expect.stringContaining('Business Blueprint'),
        }),
      ])
    );
    expect(validateDiversity({ blueprint, draft: warningDraft, scenarioPackage }).issues).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          gate: 'diversity',
          severity: 'warning',
        }),
      ])
    );
    expect(validateDiversity({ blueprint, draft: repeatedRemarkDraft, scenarioPackage }).issues).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          gate: 'diversity',
          severity: 'error',
          path: 'draft.projects.remark',
        }),
      ])
    );
    expect(validateSemanticCoverage({ blueprint, bindings: badBindings, scenarioPackage }).issues).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ code: 'semantic_anchor_id_missing' }),
        expect.objectContaining({ code: 'semantic_anchor_type_minimum_not_met' }),
        expect.objectContaining({ code: 'semantic_support_package_path_missing' }),
      ])
    );
    expect(validateSemanticCoverage({ blueprint, bindings: missingAlarmBindings, scenarioPackage }).issues).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          code: 'semantic_support_category_missing',
          expected: 'alarm support record',
        }),
      ])
    );
    expect(validateSemanticCoverage({ blueprint, bindings: missingFaultBindings, scenarioPackage }).issues).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          code: 'semantic_support_category_missing',
          expected: 'fault support record',
        }),
      ])
    );
  });
});
