import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';

import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import { ToolError, issueFromUnknown } from '../src/errors.js';
import { ProjectPaths } from '../src/project-paths.js';

let repoRoot: string;
let paths: ProjectPaths;

async function createRepoFixture() {
  repoRoot = await fs.mkdtemp(path.join(os.tmpdir(), 'demo-offline-mcp-paths-'));
  await fs.mkdir(path.join(repoRoot, 'ruoyi-fastapi-frontend', 'src', 'demo', 'scenarios', 'generated', 'candidates'), {
    recursive: true,
  });
  await fs.mkdir(path.join(repoRoot, 'ruoyi-fastapi-frontend', 'src', 'demo', 'handlers'), {
    recursive: true,
  });
  await fs.mkdir(path.join(repoRoot, 'ruoyi-fastapi-backend'), { recursive: true });
  await fs.writeFile(path.join(repoRoot, 'AGENTS.md'), '# fixture\n', 'utf8');
  await fs.writeFile(
    path.join(repoRoot, 'ruoyi-fastapi-frontend', 'src', 'demo', 'scenarios', 'schema.ts'),
    'export const schema = 1;\n',
    'utf8'
  );

  repoRoot = await fs.realpath(repoRoot);
  paths = await ProjectPaths.create({ repoRoot });
}

describe('ProjectPaths', () => {
  beforeEach(createRepoFixture);

  afterEach(async () => {
    await fs.rm(repoRoot, { recursive: true, force: true });
  });

  it('resolves the repository demo path boundaries', () => {
    expect(paths.repoRoot).toBe(repoRoot);
    expect(paths.frontendRoot).toBe(path.join(repoRoot, 'ruoyi-fastapi-frontend'));
    expect(paths.demoRoot).toBe(path.join(repoRoot, 'ruoyi-fastapi-frontend', 'src', 'demo'));
    expect(paths.generatedRoot).toBe(
      path.join(repoRoot, 'ruoyi-fastapi-frontend', 'src', 'demo', 'scenarios', 'generated')
    );
    expect(paths.candidateRoot).toBe(
      path.join(repoRoot, 'ruoyi-fastapi-frontend', 'src', 'demo', 'scenarios', 'generated', 'candidates')
    );
  });

  it('allows reading existing files inside the repository', async () => {
    await expect(
      paths.resolveRepoReadPath('ruoyi-fastapi-frontend/src/demo/scenarios/schema.ts')
    ).resolves.toBe(path.join(repoRoot, 'ruoyi-fastapi-frontend', 'src', 'demo', 'scenarios', 'schema.ts'));
  });

  it('rejects traversal and outside-repository reads', async () => {
    await expect(paths.resolveRepoReadPath('../outside.ts')).rejects.toMatchObject({
      issue: expect.objectContaining({ code: 'path_traversal_rejected' }),
    });
    await expect(paths.resolveRepoReadPath('/etc/passwd')).rejects.toMatchObject({
      issue: expect.objectContaining({ code: 'read_outside_repo_rejected' }),
    });
  });

  it('allows generated and candidate writes under the allowlisted directory', async () => {
    await expect(paths.resolveGeneratedWritePath('real-estate.ts')).resolves.toBe(
      path.join(paths.generatedRoot, 'real-estate.ts')
    );
    await expect(paths.resolveCandidateWritePath('real-estate.candidate.ts')).resolves.toBe(
      path.join(paths.candidateRoot, 'real-estate.candidate.ts')
    );
  });

  it('rejects absolute, traversal, and generated-directory escape writes', async () => {
    await expect(paths.resolveGeneratedWritePath('/tmp/demo.ts')).rejects.toMatchObject({
      issue: expect.objectContaining({ code: 'absolute_path_rejected' }),
    });
    await expect(paths.resolveGeneratedWritePath('../handlers/demo.ts')).rejects.toMatchObject({
      issue: expect.objectContaining({ code: 'path_traversal_rejected' }),
    });
  });

  it('rejects symlink escape writes', async () => {
    const outsideDir = await fs.mkdtemp(path.join(os.tmpdir(), 'demo-offline-mcp-outside-'));
    const escapeLink = path.join(paths.generatedRoot, 'escape');
    await fs.symlink(outsideDir, escapeLink, 'dir');

    try {
      await expect(paths.resolveGeneratedWritePath('escape/bad.ts')).rejects.toMatchObject({
        issue: expect.objectContaining({ code: 'symlink_escape_rejected' }),
      });
    } finally {
      await fs.rm(outsideDir, { recursive: true, force: true });
    }
  });
});

describe('ToolError formatting', () => {
  it('exposes structured issues for tool callers', () => {
    const error = new ToolError({
      path: '$.profile',
      code: 'profile_not_allowed',
      severity: 'error',
      actual: 'rm -rf',
      expected: 'Named check profile',
      fixHint: 'Use one of the fixed check profiles.',
      autoRepairable: false,
    });

    expect(issueFromUnknown(error)).toEqual(error.issue);
  });
});
