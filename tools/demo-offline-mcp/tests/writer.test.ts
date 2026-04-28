import fs from 'node:fs/promises';
import path from 'node:path';

import { describe, expect, it } from 'vitest';

import type { CompiledDemoScenarioPackage, GenerationPlan } from '../src/types.js';
import { REQUIRED_CANDIDATE_PROMOTE_PROFILES } from '../src/check-profiles.js';
import {
  computeCandidateSourceHash,
  promoteCandidateScenario,
  writeCandidateScenario,
  writeCheckRunRecord,
} from '../src/writer.js';
import { createTempRepoFixture } from '../src/project-paths.js';

function createScenarioPackage(): CompiledDemoScenarioPackage {
  return {
    schemaVersion: 1,
    scenario: {
      id: 'writer-demo',
      name: 'Writer Demo',
      version: '1.0.0',
      fingerprint: 'writer-demo-v1',
      seed: 'writer-demo',
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

function createPlan(): GenerationPlan {
  return {
    scenarioId: 'writer-demo',
    scenarioName: 'Writer Demo',
    industry: '房地产',
    brief: 'writer test',
    scope: ['project', 'simulation'],
    copiedSlices: ['auth', 'system'],
    targetCounts: {
      projects: 1,
      versionsPerProject: 1,
      sessionsPerProject: 1,
    },
    trace: [],
  };
}

async function writePassedCandidateCheckRun(paths: Awaited<ReturnType<typeof createTempRepoFixture>>, runId = 'run-1') {
  const candidateSourceHash = await computeCandidateSourceHash(paths, 'writer-demo');

  await writeCheckRunRecord(paths, 'writer-demo', {
    runId,
    candidateId: 'writer-demo',
    scenarioId: 'writer-demo',
    candidateSourceHash,
    passed: true,
    profiles: [...REQUIRED_CANDIDATE_PROMOTE_PROFILES],
    results: REQUIRED_CANDIDATE_PROMOTE_PROFILES.map((profile) => ({
      profile,
      command: ['yarn', profile],
      exitCode: 0,
      passed: true,
    })),
    createdAt: '2026-04-28T00:00:00.000Z',
  });
}

describe('ScenarioWriter', () => {
  it('writes candidates only under generated/candidates and updates candidate registry', async () => {
    const paths = await createTempRepoFixture();
    const result = await writeCandidateScenario(paths, {
      scenarioPackage: createScenarioPackage(),
      plan: createPlan(),
    });

    expect(result.data).toMatchObject({
      candidateId: 'writer-demo',
      metadataPath: expect.stringContaining('generated/candidates/writer-demo.candidate.json'),
    });
    await expect(
      fs.readFile(path.join(paths.candidateRoot, 'writer-demo.candidate.ts'), 'utf8')
    ).resolves.toContain('export const writerDemoCandidateScenario');
    await expect(fs.readFile(path.join(paths.candidateRoot, 'index.ts'), 'utf8')).resolves.toContain(
      'candidateScenarioRegistry'
    );
    await expect(fs.access(path.join(paths.generatedRoot, 'writer-demo.ts'))).rejects.toThrow();
  });

  it('rejects candidate conflicts unless overwriteCandidate is explicit', async () => {
    const paths = await createTempRepoFixture();
    await writeCandidateScenario(paths, {
      scenarioPackage: createScenarioPackage(),
      plan: createPlan(),
    });

    await expect(
      writeCandidateScenario(paths, {
        scenarioPackage: createScenarioPackage(),
        plan: createPlan(),
      })
    ).rejects.toMatchObject({
      issue: expect.objectContaining({ code: 'candidate_conflict' }),
    });

    await expect(
      writeCandidateScenario(paths, {
        scenarioPackage: createScenarioPackage(),
        plan: createPlan(),
        overwriteCandidate: true,
      })
    ).resolves.toMatchObject({ ok: true });
  });

  it('requires a passed checks run before promoting candidates', async () => {
    const paths = await createTempRepoFixture();
    await writeCandidateScenario(paths, {
      scenarioPackage: createScenarioPackage(),
      plan: createPlan(),
    });

    await expect(
      promoteCandidateScenario(paths, {
        candidateId: 'writer-demo',
        scenarioId: 'writer-demo',
        checksRunId: 'missing',
        confirm: true,
      })
    ).rejects.toMatchObject({
      issue: expect.objectContaining({ code: 'checks_run_not_found' }),
    });

    await writeCheckRunRecord(paths, 'writer-demo', {
      runId: 'incomplete-run',
      candidateId: 'writer-demo',
      scenarioId: 'writer-demo',
      candidateSourceHash: await computeCandidateSourceHash(paths, 'writer-demo'),
      passed: true,
      profiles: ['candidate-focused-tests'],
      createdAt: '2026-04-28T00:00:00.000Z',
    });

    await expect(
      promoteCandidateScenario(paths, {
        candidateId: 'writer-demo',
        scenarioId: 'writer-demo',
        checksRunId: 'incomplete-run',
        confirm: true,
      })
    ).rejects.toMatchObject({
      issue: expect.objectContaining({ code: 'checks_profiles_incomplete' }),
    });

    await writePassedCandidateCheckRun(paths);
    const result = await promoteCandidateScenario(paths, {
      candidateId: 'writer-demo',
      scenarioId: 'writer-demo',
      checksRunId: 'run-1',
      confirm: true,
    });

    expect(result.data).toMatchObject({
      scenarioId: 'writer-demo',
      registryUpdated: true,
      activated: true,
      activePath: expect.stringContaining('generated/active.ts'),
    });
    await expect(fs.readFile(path.join(paths.generatedRoot, 'writer-demo.ts'), 'utf8')).resolves.toContain(
      'export const writerDemoScenario'
    );
    await expect(fs.readFile(path.join(paths.generatedRoot, 'index.ts'), 'utf8')).resolves.toContain(
      'generatedScenarioRegistry'
    );
    await expect(fs.readFile(path.join(paths.generatedRoot, 'active.ts'), 'utf8')).resolves.toContain(
      "activeGeneratedScenarioId = 'writer-demo'"
    );
    await expect(fs.readFile(path.join(paths.generatedRoot, 'index.ts'), 'utf8')).resolves.toContain(
      'activeGeneratedScenarioId'
    );
  });

  it('rejects stale checks when the candidate changed after validation', async () => {
    const paths = await createTempRepoFixture();
    await writeCandidateScenario(paths, {
      scenarioPackage: createScenarioPackage(),
      plan: createPlan(),
    });
    await writePassedCandidateCheckRun(paths);
    await writeCandidateScenario(paths, {
      scenarioPackage: {
        ...createScenarioPackage(),
        scenario: {
          ...createScenarioPackage().scenario,
          fingerprint: 'writer-demo-v2',
        },
      },
      plan: createPlan(),
      overwriteCandidate: true,
    });

    await expect(
      promoteCandidateScenario(paths, {
        candidateId: 'writer-demo',
        scenarioId: 'writer-demo',
        checksRunId: 'run-1',
        confirm: true,
      })
    ).rejects.toMatchObject({
      issue: expect.objectContaining({ code: 'candidate_changed_since_checks' }),
    });
  });

  it('refuses to replace an official scenario unless replaceExisting is explicit', async () => {
    const paths = await createTempRepoFixture();
    await writeCandidateScenario(paths, {
      scenarioPackage: createScenarioPackage(),
      plan: createPlan(),
    });
    await writePassedCandidateCheckRun(paths);
    await promoteCandidateScenario(paths, {
      candidateId: 'writer-demo',
      scenarioId: 'writer-demo',
      checksRunId: 'run-1',
      confirm: true,
    });

    await expect(
      promoteCandidateScenario(paths, {
        candidateId: 'writer-demo',
        scenarioId: 'writer-demo',
        checksRunId: 'run-1',
        confirm: true,
      })
    ).rejects.toMatchObject({
      issue: expect.objectContaining({ code: 'official_scenario_conflict' }),
    });

    await expect(
      promoteCandidateScenario(paths, {
        candidateId: 'writer-demo',
        scenarioId: 'writer-demo',
        checksRunId: 'run-1',
        confirm: true,
        replaceExisting: true,
        cleanupCandidate: true,
      })
    ).resolves.toMatchObject({ ok: true });
  });

  it('allows promoting without changing the active generated scenario', async () => {
    const paths = await createTempRepoFixture();
    await writeCandidateScenario(paths, {
      scenarioPackage: createScenarioPackage(),
      plan: createPlan(),
    });
    await writePassedCandidateCheckRun(paths);

    const result = await promoteCandidateScenario(paths, {
      candidateId: 'writer-demo',
      scenarioId: 'writer-demo',
      checksRunId: 'run-1',
      confirm: true,
      activate: false,
    });

    expect(result.data).toMatchObject({
      scenarioId: 'writer-demo',
      activated: false,
    });
    await expect(fs.access(path.join(paths.generatedRoot, 'active.ts'))).rejects.toThrow();
  });
});
