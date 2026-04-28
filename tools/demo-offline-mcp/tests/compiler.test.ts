import path from 'node:path';

import { describe, expect, it } from 'vitest';

import { compileScenarioPackage } from '../src/compiler.js';
import { scanDemoOfflineContext } from '../src/demo-scan.js';
import { createGenerationPlan } from '../src/generation-plan.js';
import { ProjectPaths } from '../src/project-paths.js';
import type { GenerationPlan, IndustryDataDraft } from '../src/types.js';

const repoRoot = path.resolve(import.meta.dirname, '../../..');

async function createCompileFixture(): Promise<{
  paths: ProjectPaths;
  plan: GenerationPlan;
  draft: IndustryDataDraft;
}> {
  const paths = await ProjectPaths.create({ repoRoot });
  const context = (await scanDemoOfflineContext(paths)).data!;
  const plan = createGenerationPlan(
    {
      brief: '房地产行业 project + simulation 验收样例。',
      industry: '房地产',
      scenarioId: 'real-estate-compiled-demo',
      scenarioName: '房地产编译演示',
      targetCounts: {
        projects: 2,
        versionsPerProject: 2,
        sessionsPerProject: 1,
      },
    },
    context
  ).data!;
  const draft: IndustryDataDraft = {
    industry: {
      id: 'real-estate',
      name: '房地产',
      keywords: ['交付', '预售'],
    },
    scenario: {
      id: plan.scenarioId,
      name: plan.scenarioName,
      version: '1.0.0',
      seed: 'compiler-test',
    },
    projects: [
      {
        key: 'delivery-001',
        name: '滨江云著交付整改专项',
        region: '杭州滨江',
        stage: '交付整改',
        ownerRole: '交付负责人',
        ownerName: '顾清远',
        riskLevel: 'high',
        risk: '公区石材整改影响交付开放日。',
        remark: '房地产交付团队按楼栋批次推进整改闭环。',
        versions: [{ name: '交付整改作战版', locked: true }],
        simulation: {
          status: 'running',
          messages: ['整改复验进入集中冲刺。'],
          alarms: [{ severity: 'high', message: '公区石材修补进度偏慢。' }],
        },
      },
      {
        key: 'presale-002',
        name: '南湖悦府预售筹备计划',
        region: '嘉兴南湖',
        stage: '预售筹备',
        ownerRole: '营销项目经理',
        ownerName: '叶南乔',
        riskLevel: 'medium',
        risk: '样板间开放节奏影响认筹转化。',
        remark: '房地产营销团队关注预售证和开盘节奏。',
        simulation: {
          status: 'paused',
          events: ['价格备案材料已提交。'],
        },
      },
    ],
  };

  return { paths, plan, draft };
}

describe('compileScenarioPackage', () => {
  it('deterministically compiles project and simulation slices while copying auth/system', async () => {
    const fixture = await createCompileFixture();
    const first = await compileScenarioPackage(fixture);
    const second = await compileScenarioPackage(fixture);

    expect(first.ok).toBe(true);
    expect(first.data).toStrictEqual(second.data);
    expect(first.data?.summary).toMatchObject({
      scenarioId: 'real-estate-compiled-demo',
      projectCount: 2,
      versionCount: 3,
      sessionCount: 2,
      copiedSlices: ['auth', 'system'],
      generatedSlices: ['project', 'simulation'],
    });
    expect(first.data?.scenarioPackage.auth.accounts.length).toBeGreaterThan(0);
    expect(first.data?.scenarioPackage.system.menus.length).toBeGreaterThan(0);
  });

  it('emits DemoScenarioPackage array structures and linked deterministic IDs', async () => {
    const fixture = await createCompileFixture();
    const result = await compileScenarioPackage(fixture);
    const scenarioPackage = result.data!.scenarioPackage;

    expect(Array.isArray(scenarioPackage.project.projects)).toBe(true);
    expect(Array.isArray(scenarioPackage.project.versions)).toBe(true);
    expect(Array.isArray(scenarioPackage.project.topologies)).toBe(true);
    expect(Array.isArray(scenarioPackage.simulation.sessions)).toBe(true);
    expect(Array.isArray(scenarioPackage.simulation.messages)).toBe(true);
    expect(Array.isArray(scenarioPackage.simulation.bandwidth)).toBe(true);
    expect(Array.isArray(scenarioPackage.simulation.alarms)).toBe(true);
    expect(Array.isArray(scenarioPackage.simulation.faults)).toBe(true);
    expect(Array.isArray(scenarioPackage.simulation.events)).toBe(true);
    expect(Array.isArray(scenarioPackage.simulation.streamFrames)).toBe(true);
    expect(scenarioPackage.project.projects[0]).toMatchObject({
      projectId: 7001,
      projectName: '滨江云著交付整改专项',
      riskLevel: 'high',
    });
    expect(scenarioPackage.simulation.sessions[0]).toMatchObject({
      sessionId: 'real-estate-compiled-demo-session-1-1',
      projectId: 7001,
      versionId: 8001,
    });
  });

  it('rejects invalid drafts before compiling', async () => {
    const fixture = await createCompileFixture();
    const result = await compileScenarioPackage({
      ...fixture,
      draft: {
        ...fixture.draft,
        projects: [],
      },
    });

    expect(result.ok).toBe(false);
    expect(result.errors).toEqual(
      expect.arrayContaining([expect.objectContaining({ code: 'invalid_draft_structure' })])
    );
  });
});
