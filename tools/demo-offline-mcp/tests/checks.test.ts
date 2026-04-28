import fs from 'node:fs/promises';
import path from 'node:path';

import { describe, expect, it } from 'vitest';

import type { CommandExecutor, CommandSpec } from '../src/checks.js';
import { runChecks } from '../src/checks.js';
import { createTempRepoFixture } from '../src/project-paths.js';

async function writeCandidateFixture(paths: Awaited<ReturnType<typeof createTempRepoFixture>>, candidateId: string) {
  await fs.mkdir(paths.candidateRoot, { recursive: true });
  await fs.writeFile(
    path.join(paths.candidateRoot, `${candidateId}.candidate.ts`),
    `export const ${candidateId.replace(/[^a-zA-Z0-9_$]/g, '')} = { scenario: { id: '${candidateId}' } };\n`,
    'utf8'
  );
}

describe('CheckRunner', () => {
  it('rejects allowlist profile violations with structured guidance', async () => {
    const paths = await createTempRepoFixture();

    await expect(
      runChecks(paths, {
        profiles: ['rm -rf'],
      })
    ).rejects.toMatchObject({
      issue: expect.objectContaining({
        code: 'check_profile_not_allowed',
        expected: expect.stringContaining('candidate-focused-tests'),
      }),
    });
  });

  it('builds fixed command specs with env variables and shell-free executor contract', async () => {
    const paths = await createTempRepoFixture();
    await writeCandidateFixture(paths, 'candidate-a');
    const specs: CommandSpec[] = [];
    const executor: CommandExecutor = async (spec) => {
      specs.push(spec);
      return {
        exitCode: 0,
        stdout: 'ok\n',
        stderr: '',
        durationMs: 12,
      };
    };
    const result = await runChecks(
      paths,
      {
        candidateId: 'candidate-a',
        profiles: ['candidate-focused-tests', 'candidate-demo-offline-build'],
      },
      executor
    );

    expect(result.data).toMatchObject({
      passed: true,
      candidateId: 'candidate-a',
      runMode: 'candidate',
      recommendedPreviewCommand:
        'VITE_APP_RUNTIME_MODE=demo-offline VITE_DEMO_ALLOW_CANDIDATE_SCENARIOS=true VITE_DEMO_SCENARIO_ID=candidate-a yarn preview:demo-offline',
      results: [
        expect.objectContaining({ profile: 'candidate-focused-tests', passed: true }),
        expect.objectContaining({ profile: 'candidate-demo-offline-build', passed: true }),
      ],
    });
    expect(specs[0].command.slice(0, 2)).toEqual(['yarn', 'test:run']);
    expect(specs[0].command).toContain('src/demo/scenarios/index.test.ts');
    expect(specs[0]).toMatchObject({
      env: {
        VITE_APP_RUNTIME_MODE: 'demo-offline',
        VITE_DEMO_ALLOW_CANDIDATE_SCENARIOS: 'true',
        VITE_DEMO_SCENARIO_ID: 'candidate-a',
      },
    });
    expect(specs[1]).toMatchObject({
      command: ['yarn', 'build:demo-offline'],
      env: {
        VITE_DEMO_SCENARIO_ID: 'candidate-a',
      },
    });
    await expect(
      fs.readFile(path.join(paths.candidateRoot, 'candidate-a.checks', `${result.data!.runId}.json`), 'utf8')
    ).resolves.toContain('"candidateSourceHash"');
  });

  it('returns failure summaries with command evidence and next actions', async () => {
    const paths = await createTempRepoFixture();
    const executor: CommandExecutor = async () => ({
      exitCode: 2,
      stdout: 'line 1\nline 2\n',
      stderr: 'Type error\nat src/demo/scenarios/generated/foo.ts\n',
      durationMs: 42,
    });
    const result = await runChecks(
      paths,
      {
        profiles: ['frontend-type-check'],
        maxLogLines: 1,
      },
      executor
    );

    expect(result.data).toMatchObject({
      passed: false,
      results: [
        expect.objectContaining({
          profile: 'frontend-type-check',
          exitCode: 2,
          stdoutTail: ['line 2'],
          stderrTail: ['at src/demo/scenarios/generated/foo.ts'],
          nextActions: ['Fix the reported errors and rerun the same check profile.'],
        }),
      ],
    });
  });

  it('requires candidate/scenario ids for profiles that need them', async () => {
    const paths = await createTempRepoFixture();

    await expect(
      runChecks(paths, {
        profiles: ['candidate-demo-offline-build'],
      })
    ).rejects.toMatchObject({
      issue: expect.objectContaining({ code: 'candidate_id_required' }),
    });

    await expect(
      runChecks(paths, {
        profiles: ['promoted-demo-offline-build'],
      })
    ).rejects.toMatchObject({
      issue: expect.objectContaining({ code: 'scenario_id_required' }),
    });
  });

  it('rejects candidate checks when explicit scenario id does not match the candidate id', async () => {
    const paths = await createTempRepoFixture();
    await writeCandidateFixture(paths, 'candidate-a');

    await expect(
      runChecks(paths, {
        candidateId: 'candidate-a',
        scenarioId: 'other-scenario',
        profiles: ['candidate-focused-tests'],
      })
    ).rejects.toMatchObject({
      issue: expect.objectContaining({ code: 'candidate_scenario_id_mismatch' }),
    });
  });
});
