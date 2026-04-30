import path from 'node:path';

import { describe, expect, it } from 'vitest';

import { scanDemoOfflineContext, formatDemoOfflineContext } from '../src/demo-scan.js';
import { ProjectPaths } from '../src/project-paths.js';

const repoRoot = path.resolve(import.meta.dirname, '../../..');

describe('scanDemoOfflineContext', () => {
  it('summarizes demo-offline schema, handlers, scripts, and scenarios', async () => {
    const paths = await ProjectPaths.create({ repoRoot });
    const result = await scanDemoOfflineContext(paths);

    expect(result.ok).toBe(true);
    expect(result.data).toMatchObject({
      schemaVersion: 1,
      safeSlices: ['project', 'simulation'],
      copiedSlices: ['auth', 'system'],
      domcModules: expect.arrayContaining([
        expect.objectContaining({
          moduleId: 'project',
          capability: 'generatable',
          adapterId: 'project-simulation',
        }),
        expect.objectContaining({
          moduleId: 'auth',
          capability: 'copyOnly',
        }),
      ]),
      scripts: {
        devMock: expect.stringContaining('demo-offline'),
        buildDemoOffline: 'vite build --mode demo-offline',
        typeCheck: 'vue-tsc --noEmit',
        testRun: 'vitest run',
      },
    });
    expect(result.data?.handlers).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ name: 'project', covered: true }),
        expect.objectContaining({ name: 'simulation', covered: true }),
      ])
    );
    expect(result.data?.scenarios).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ id: 'default', kind: 'default' }),
        expect.objectContaining({ id: 'real-estate-project-demo', kind: 'generated' }),
      ])
    );
    expect(result.data?.risks).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ code: 'demo_api_not_implemented_catch_all' }),
      ])
    );
  });

  it('can omit generated and candidate scenarios from scan output', async () => {
    const paths = await ProjectPaths.create({ repoRoot });
    const result = await scanDemoOfflineContext(paths, {
      includeGenerated: false,
      includeCandidates: false,
    });

    expect(result.data?.scenarios).toEqual([expect.objectContaining({ id: 'default' })]);
  });

  it('formats a compact markdown summary for agent context', async () => {
    const paths = await ProjectPaths.create({ repoRoot });
    const result = await scanDemoOfflineContext(paths);

    expect(formatDemoOfflineContext(result.data!)).toContain('Safe slices: project, simulation');
  });
});
