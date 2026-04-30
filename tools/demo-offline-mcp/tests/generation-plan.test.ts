import path from 'node:path';

import { describe, expect, it } from 'vitest';

import { scanDemoOfflineContext } from '../src/demo-scan.js';
import { createGenerationPlan } from '../src/generation-plan.js';
import { ProjectPaths } from '../src/project-paths.js';

const repoRoot = path.resolve(import.meta.dirname, '../../..');

async function scanContext() {
  const paths = await ProjectPaths.create({ repoRoot });
  const context = await scanDemoOfflineContext(paths);
  return context.data!;
}

describe('createGenerationPlan', () => {
  it('defaults to project + simulation and copies auth/system from default scenario', async () => {
    const plan = createGenerationPlan(
      {
        brief: '房地产客户演示，强调项目进度与仿真态势。',
      },
      await scanContext()
    );

    expect(plan.data).toMatchObject({
      scenarioId: 'real-estate-project-simulation-demo',
      industry: '房地产',
      scope: ['project', 'simulation'],
      copiedSlices: ['auth', 'system'],
      targetCounts: {
        projects: 6,
        versionsPerProject: 1,
        sessionsPerProject: 1,
      },
    });
    expect(plan.data?.trace).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ slice: 'project', status: 'generate' }),
        expect.objectContaining({ slice: 'simulation', status: 'generate' }),
        expect.objectContaining({ slice: 'auth', status: 'copy' }),
        expect.objectContaining({ slice: 'system', status: 'copy' }),
      ])
    );
  });

  it('keeps local scope dependencies intact when simulation is requested', async () => {
    const plan = createGenerationPlan(
      {
        brief: '只需要仿真态势演示。',
        industry: '制造',
        scope: ['simulation'],
      },
      await scanContext()
    );

    expect(plan.data?.scope).toEqual(['project', 'simulation']);
  });

  it('marks all-module requests outside P0 as unsupported instead of promising coverage', async () => {
    const plan = createGenerationPlan(
      {
        brief: '希望系统全亮，全部菜单都能演示。',
        industry: '教育',
        targetCounts: {
          projects: 2,
        },
      },
      await scanContext()
    );

    expect(plan.data?.targetCounts.projects).toBe(2);
    expect(plan.data?.trace).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          slice: 'unregistered-business-modules',
          status: 'blocked',
          blocker: expect.objectContaining({
            code: 'domc_all_modules_request_blocked',
          }),
        }),
      ])
    );
  });

  it('accepts explicit scenario metadata and normalized counts', async () => {
    const plan = createGenerationPlan(
      {
        brief: '房地产项目专项演示。',
        industry: '房地产',
        scenarioId: 'customer-a-demo',
        scenarioName: '客户 A 演示场景',
        scope: ['project'],
        targetCounts: {
          projects: 3,
          versionsPerProject: 2,
          sessionsPerProject: 0,
        },
      },
      await scanContext()
    );

    expect(plan.data).toMatchObject({
      scenarioId: 'customer-a-demo',
      scenarioName: '客户 A 演示场景',
      scope: ['project'],
      targetCounts: {
        projects: 3,
        versionsPerProject: 2,
        sessionsPerProject: 1,
      },
    });
  });
});
