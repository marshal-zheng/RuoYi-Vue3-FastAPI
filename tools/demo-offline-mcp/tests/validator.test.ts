import path from 'node:path';

import { describe, expect, it } from 'vitest';

import { scanDemoOfflineContext } from '../src/demo-scan.js';
import { createGenerationPlan } from '../src/generation-plan.js';
import { ProjectPaths } from '../src/project-paths.js';
import type { GenerationPlan, IndustryDataDraft } from '../src/types.js';
import { validateIndustryDataDraft } from '../src/validator.js';

const repoRoot = path.resolve(import.meta.dirname, '../../..');

async function createPlan(): Promise<{ plan: GenerationPlan; draft: IndustryDataDraft }> {
  const paths = await ProjectPaths.create({ repoRoot });
  const context = (await scanDemoOfflineContext(paths)).data!;
  const plan = createGenerationPlan(
    {
      brief: '房地产客户演示，生成两个项目。',
      industry: '房地产',
      targetCounts: {
        projects: 2,
      },
    },
    context
  ).data!;
  const draft: IndustryDataDraft = {
    industry: {
      id: 'real-estate',
      name: '房地产',
      keywords: ['交付', '预售', '拿地'],
    },
    scenario: {
      id: plan.scenarioId,
      name: plan.scenarioName,
    },
    projects: [
      {
        key: 'delivery-001',
        name: '滨江云著交付整改专项',
        region: '杭州滨江',
        stage: '交付整改',
        ownerRole: '交付负责人',
        riskLevel: 'high',
        risk: '公区石材整改和户内渗漏复验影响集中交付。',
        remark: '房地产交付团队按楼栋批次推进整改闭环。',
        topology: {
          nodes: [
            { name: '整改派单', type: 'workflow' },
            { name: '复验确认', type: 'checkpoint' },
          ],
          links: [{ source: '整改派单', target: '复验确认' }],
        },
        simulation: {
          status: 'running',
          messages: ['交付整改任务进入业主开放日前冲刺。'],
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
        risk: '价格备案和样板间开放节点需同步管控。',
        remark: '房地产营销团队关注认筹转化与开盘节奏。',
        simulation: {
          status: 'paused',
          alarms: [{ severity: 'medium', message: '样板间软装较计划延后 3 天。' }],
        },
      },
    ],
  };

  return { plan, draft };
}

describe('validateIndustryDataDraft', () => {
  it('validates a reusable real-estate semantic draft and repairs low-risk fields', async () => {
    const paths = await ProjectPaths.create({ repoRoot });
    const context = (await scanDemoOfflineContext(paths)).data!;
    const { plan, draft } = await createPlan();
    draft.projects[0].name = '  滨江云著交付整改专项  ';

    const result = validateIndustryDataDraft({
      plan,
      draft,
      context,
      autoRepair: true,
    });

    expect(result.data?.valid).toBe(true);
    expect(result.data?.repairedDraft?.scenario.version).toBe('1.0.0');
    expect(result.data?.repairedDraft?.projects[0]).toMatchObject({
      ownerName: '交付负责人负责人1',
    });
    expect(result.data?.issues).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ code: 'trimmed_whitespace', autoRepairable: true }),
        expect.objectContaining({ code: 'default_version_applied', autoRepairable: true }),
        expect.objectContaining({ code: 'owner_name_defaulted', autoRepairable: true }),
      ])
    );
  });

  it('returns structural errors with paths and fix hints', async () => {
    const paths = await ProjectPaths.create({ repoRoot });
    const context = (await scanDemoOfflineContext(paths)).data!;
    const { plan, draft } = await createPlan();

    const result = validateIndustryDataDraft({
      plan,
      draft: {
        ...draft,
        projects: [{ ...draft.projects[0], riskLevel: 'critical' }],
      },
      context,
    });

    expect(result.data?.valid).toBe(false);
    expect(result.data?.issues[0]).toMatchObject({
      path: 'projects.0.riskLevel',
      code: 'invalid_draft_structure',
      autoRepairable: false,
    });
  });

  it('detects placeholders, duplicate keys, insufficient count, and relationship gaps', async () => {
    const paths = await ProjectPaths.create({ repoRoot });
    const context = (await scanDemoOfflineContext(paths)).data!;
    const { plan, draft } = await createPlan();
    plan.targetCounts.projects = 3;
    draft.projects = [
      {
        ...draft.projects[0],
        key: 'same',
        name: '测试项目',
        topology: {
          nodes: [{ name: '节点A', type: 'device' }],
          links: [{ source: '节点A', target: '不存在节点' }],
        },
      },
      {
        ...draft.projects[1],
        key: 'same',
        name: '测试项目',
      },
    ];

    const result = validateIndustryDataDraft({ plan, draft, context });

    expect(result.data?.valid).toBe(false);
    expect(result.data?.issues).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ code: 'placeholder_text' }),
        expect.objectContaining({ code: 'duplicate_project_key' }),
        expect.objectContaining({ code: 'repeated_project_name' }),
        expect.objectContaining({ code: 'insufficient_project_count' }),
        expect.objectContaining({ code: 'topology_link_node_missing' }),
      ])
    );
  });

  it('reports scan context mismatches for unsupported plan scopes', async () => {
    const paths = await ProjectPaths.create({ repoRoot });
    const context = (await scanDemoOfflineContext(paths)).data!;
    const { plan, draft } = await createPlan();
    context.safeSlices = ['project'];

    const result = validateIndustryDataDraft({ plan, draft, context });

    expect(result.data?.valid).toBe(false);
    expect(result.data?.issues).toEqual(
      expect.arrayContaining([expect.objectContaining({ code: 'scope_not_supported_by_scan' })])
    );
  });
});
