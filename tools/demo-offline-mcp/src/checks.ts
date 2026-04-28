import { spawn } from 'node:child_process';
import type { ChildProcessWithoutNullStreams } from 'node:child_process';

import { ALLOWED_CHECK_PROFILES, isAllowedProfile } from './check-profiles.js';
import { createIssue, ToolError, type CheckResult } from './errors.js';
import type { ProjectPaths } from './project-paths.js';
import type { CheckProfile, RunChecksResult, ToolEnvelope } from './types.js';
import { okEnvelope } from './types.js';
import { computeCandidateSourceHash, writeCheckRunRecord } from './writer.js';

export interface RunChecksInput {
  candidateId?: string;
  scenarioId?: string;
  profiles: string[];
  maxLogLines?: number;
}

export interface CommandSpec {
  profile: CheckProfile;
  command: string[];
  cwd: string;
  env: Record<string, string>;
}

export interface CommandExecution {
  exitCode: number | null;
  stdout: string;
  stderr: string;
  durationMs: number;
}

export type CommandExecutor = (spec: CommandSpec) => Promise<CommandExecution>;

const FOCUSED_TESTS = [
  'src/demo/scenarios/generated/*.test.ts',
  'src/demo/scenarios/generated/candidates/*.test.ts',
  'src/demo/scenarios/index.test.ts',
  'src/demo/repositories/scenario.test.ts',
  'src/demo/services/project.test.ts',
  'src/demo/services/simulation.test.ts',
  'src/demo/handlers/project.test.ts',
  'src/demo/handlers/simulation.test.ts',
];

function tailLines(value: string, maxLines: number): string[] {
  return value
    .split(/\r?\n/)
    .filter((line) => line.trim().length > 0)
    .slice(-maxLines);
}

function createRunId(): string {
  return `check-${new Date().toISOString().replace(/[-:.TZ]/g, '').slice(0, 14)}`;
}

function resolveRunMode(input: RunChecksInput): RunChecksResult['runMode'] {
  if (input.candidateId) return 'candidate';
  if (input.scenarioId) return 'promoted';
  return 'general';
}

function previewCommandFor(input: RunChecksInput): string | undefined {
  if (input.candidateId) {
    return `VITE_APP_RUNTIME_MODE=demo-offline VITE_DEMO_ALLOW_CANDIDATE_SCENARIOS=true VITE_DEMO_SCENARIO_ID=${input.candidateId} yarn preview:demo-offline`;
  }

  if (input.scenarioId) {
    return `VITE_APP_RUNTIME_MODE=demo-offline VITE_DEMO_SCENARIO_ID=${input.scenarioId} yarn preview:demo-offline`;
  }

  return undefined;
}

function scenarioIdForRun(input: RunChecksInput): string | undefined {
  return input.candidateId ? input.scenarioId ?? input.candidateId : input.scenarioId;
}

function commandForProfile(paths: ProjectPaths, profile: CheckProfile, input: RunChecksInput): CommandSpec {
  const baseEnv: Record<string, string> = {};

  if (profile.startsWith('candidate') && !input.candidateId) {
    throw new ToolError(
      createIssue({
        path: 'candidateId',
        code: 'candidate_id_required',
        severity: 'error',
        actual: input.candidateId,
        expected: 'candidateId',
        fixHint: `Provide candidateId when running ${profile}.`,
        autoRepairable: false,
      })
    );
  }

  if (profile === 'promoted-demo-offline-build' && !input.scenarioId) {
    throw new ToolError(
      createIssue({
        path: 'scenarioId',
        code: 'scenario_id_required',
        severity: 'error',
        actual: input.scenarioId,
        expected: 'scenarioId',
        fixHint: 'Provide scenarioId when running promoted-demo-offline-build.',
        autoRepairable: false,
      })
    );
  }

  switch (profile) {
    case 'candidate-focused-tests':
      return {
        profile,
        command: ['yarn', 'test:run', ...FOCUSED_TESTS],
        cwd: paths.frontendRoot,
        env: {
          ...baseEnv,
          VITE_APP_RUNTIME_MODE: 'demo-offline',
          VITE_DEMO_ALLOW_CANDIDATE_SCENARIOS: 'true',
          VITE_DEMO_SCENARIO_ID: input.candidateId!,
        },
      };
    case 'frontend-type-check':
      return {
        profile,
        command: ['yarn', 'type-check'],
        cwd: paths.frontendRoot,
        env: baseEnv,
      };
    case 'candidate-demo-offline-build':
      return {
        profile,
        command: ['yarn', 'build:demo-offline'],
        cwd: paths.frontendRoot,
        env: {
          ...baseEnv,
          VITE_APP_RUNTIME_MODE: 'demo-offline',
          VITE_DEMO_ALLOW_CANDIDATE_SCENARIOS: 'true',
          VITE_DEMO_SCENARIO_ID: input.candidateId!,
        },
      };
    case 'promoted-demo-offline-build':
      return {
        profile,
        command: ['yarn', 'build:demo-offline'],
        cwd: paths.frontendRoot,
        env: {
          ...baseEnv,
          VITE_APP_RUNTIME_MODE: 'demo-offline',
          VITE_DEMO_SCENARIO_ID: input.scenarioId!,
        },
      };
  }
}

export async function spawnCommand(spec: CommandSpec): Promise<CommandExecution> {
  const startedAt = Date.now();

  return new Promise((resolve) => {
    const child: ChildProcessWithoutNullStreams = spawn(spec.command[0], spec.command.slice(1), {
      cwd: spec.cwd,
      env: {
        ...process.env,
        ...spec.env,
      },
      shell: false,
    });
    const stdout: Buffer[] = [];
    const stderr: Buffer[] = [];

    child.stdout.on('data', (chunk: Buffer) => stdout.push(chunk));
    child.stderr.on('data', (chunk: Buffer) => stderr.push(chunk));
    child.on('error', (error) => {
      stderr.push(Buffer.from(error.message));
    });
    child.on('close', (exitCode) => {
      resolve({
        exitCode,
        stdout: Buffer.concat(stdout).toString('utf8'),
        stderr: Buffer.concat(stderr).toString('utf8'),
        durationMs: Date.now() - startedAt,
      });
    });
  });
}

function resultFromExecution(
  spec: CommandSpec,
  execution: CommandExecution,
  maxLogLines: number
): CheckResult {
  const passed = execution.exitCode === 0;

  return {
    profile: spec.profile,
    command: spec.command,
    cwd: spec.cwd,
    exitCode: execution.exitCode,
    durationMs: execution.durationMs,
    passed,
    summary: passed
      ? `${spec.profile} passed.`
      : `${spec.profile} failed with exit code ${execution.exitCode}.`,
    stdoutTail: tailLines(execution.stdout, maxLogLines),
    stderrTail: tailLines(execution.stderr, maxLogLines),
    nextActions: passed
      ? spec.profile.startsWith('candidate')
        ? ['Review results, then call demo_offline_promote_candidate explicitly if all required checks passed.']
        : ['Use the build evidence in delivery notes.']
      : ['Fix the reported errors and rerun the same check profile.'],
  };
}

export async function runChecks(
  paths: ProjectPaths,
  input: RunChecksInput,
  executor: CommandExecutor = spawnCommand
): Promise<ToolEnvelope<RunChecksResult>> {
  if (input.candidateId && input.scenarioId && input.candidateId !== input.scenarioId) {
    throw new ToolError(
      createIssue({
        path: 'scenarioId',
        code: 'candidate_scenario_id_mismatch',
        severity: 'error',
        actual: input.scenarioId,
        expected: input.candidateId,
        fixHint: 'Candidate check runs must use the scenario ID compiled into the candidate file.',
        autoRepairable: false,
      })
    );
  }

  const invalidProfile = input.profiles.find((profile) => !isAllowedProfile(profile));

  if (invalidProfile) {
    throw new ToolError(
      createIssue({
        path: 'profiles',
        code: 'check_profile_not_allowed',
        severity: 'error',
        actual: invalidProfile,
        expected: ALLOWED_CHECK_PROFILES.join(', '),
        fixHint: 'Use one of the fixed check profiles; arbitrary shell commands are not supported.',
        autoRepairable: false,
      })
    );
  }

  const maxLogLines = input.maxLogLines ?? 40;
  const runId = createRunId();
  const results: CheckResult[] = [];
  const scenarioId = scenarioIdForRun(input);

  for (const profile of input.profiles as CheckProfile[]) {
    const spec = commandForProfile(paths, profile, input);
    const execution = await executor(spec);
    results.push(resultFromExecution(spec, execution, maxLogLines));
  }

  const passed = results.every((result) => result.passed);

  if (input.candidateId) {
    const candidateSourceHash = await computeCandidateSourceHash(paths, input.candidateId);

    await writeCheckRunRecord(paths, input.candidateId, {
      runId,
      candidateId: input.candidateId,
      scenarioId,
      candidateSourceHash,
      passed,
      profiles: input.profiles,
      results: results.map((result) => ({
        profile: result.profile,
        command: result.command,
        exitCode: result.exitCode,
        passed: result.passed,
      })),
      createdAt: new Date().toISOString(),
    });
  }

  return okEnvelope(
    passed ? 'All selected demo-offline checks passed.' : 'One or more demo-offline checks failed.',
    {
      runId,
      passed,
      scenarioId,
      candidateId: input.candidateId,
      runMode: resolveRunMode(input),
      recommendedPreviewCommand: previewCommandFor(input),
      results,
    },
    {
      artifacts: results.map((result) => ({
        kind: 'command',
        label: result.profile,
        metadata: {
          command: result.command,
          exitCode: result.exitCode,
          durationMs: result.durationMs,
        },
      })),
      nextActions: passed
        ? [
            input.candidateId
              ? 'Checks passed; candidate still requires explicit promote before becoming official.'
              : 'Checks passed; record the runId and build evidence.',
          ]
        : ['Fix failed checks before promoting or delivering the demo-offline package.'],
    }
  );
}
