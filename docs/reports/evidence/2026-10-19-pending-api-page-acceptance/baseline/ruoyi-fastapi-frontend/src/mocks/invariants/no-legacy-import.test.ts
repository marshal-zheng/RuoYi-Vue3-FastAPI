import { existsSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';

import fg from 'fast-glob';
import { describe, expect, it } from 'vitest';

const LEGACY_PATTERNS = [
  '@/demo/',
  'src/demo/',
  'VITE_ENABLE_MOCK',
  'VITE_DEMO_SCENARIO_ID',
  'VITE_DEMO_ALLOW_CANDIDATE_SCENARIOS',
  'demo-offline-contract',
  'demo-contract',
  'demo-scenarios',
  'release-store',
  '@/demo/scenarios',
  'DemoScenarioPackage',
  'ScenarioRepository',
  'generatedScenarioRegistry',
  'candidateScenarioRegistry',
  'tools/demo-offline-mcp',
];

describe('mock mainline static boundaries', () => {
  it('removes the legacy src/demo runtime tree', () => {
    expect(existsSync(resolve(__dirname, '..', '..', 'demo'))).toBe(false);
  });

  it('does not import legacy scenario runtime from current frontend source', () => {
    const root = resolve(__dirname, '..', '..');
    const files = fg.sync('**/*.{ts,tsx}', {
      cwd: root,
      absolute: true,
      ignore: ['**/*.test.ts', 'demo/**'],
    });

    const offenders = files.flatMap((file) => {
      const content = readFileSync(file, 'utf-8');
      return LEGACY_PATTERNS.filter((pattern) => content.includes(pattern)).map(
        (pattern) => `${file}: ${pattern}`
      );
    });

    expect(offenders).toEqual([]);
  });
});
