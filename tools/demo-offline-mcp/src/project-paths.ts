import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';

import { createIssue, ToolError } from './errors.js';

export interface ProjectPathsOptions {
  repoRoot?: string;
  cwd?: string;
}

export interface ResolvedProjectPaths {
  repoRoot: string;
  frontendRoot: string;
  demoRoot: string;
  generatedRoot: string;
  candidateRoot: string;
}

const FRONTEND_DIR = 'ruoyi-fastapi-frontend';
const DEMO_GENERATED_SEGMENTS = [
  FRONTEND_DIR,
  'src',
  'demo',
  'scenarios',
  'generated',
] as const;

function isInside(parent: string, child: string): boolean {
  const relativePath = path.relative(parent, child);
  return relativePath === '' || (!relativePath.startsWith('..') && !path.isAbsolute(relativePath));
}

function hasTraversal(value: string): boolean {
  return value.split(/[\\/]+/).some((segment) => segment === '..');
}

async function pathExists(value: string): Promise<boolean> {
  try {
    await fs.access(value);
    return true;
  } catch {
    return false;
  }
}

async function realpathIfExists(value: string): Promise<string> {
  if (await pathExists(value)) {
    return fs.realpath(value);
  }

  return path.resolve(value);
}

async function nearestExistingPath(value: string): Promise<string> {
  let current = path.resolve(value);

  while (!(await pathExists(current))) {
    const parent = path.dirname(current);

    if (parent === current) {
      return current;
    }

    current = parent;
  }

  return current;
}

async function findRepoRoot(cwd: string): Promise<string> {
  let current = path.resolve(cwd);

  while (true) {
    const frontendRoot = path.join(current, FRONTEND_DIR);
    const agentsFile = path.join(current, 'AGENTS.md');

    if ((await pathExists(frontendRoot)) && (await pathExists(agentsFile))) {
      return fs.realpath(current);
    }

    const parent = path.dirname(current);

    if (parent === current) {
      throw new ToolError(
        createIssue({
          path: cwd,
          code: 'repo_root_not_found',
          severity: 'error',
          actual: cwd,
          expected: 'Repository root containing AGENTS.md and ruoyi-fastapi-frontend/',
          fixHint: 'Pass --repo-root with the RuoYi-Vue3-FastAPI repository path.',
          autoRepairable: false,
        })
      );
    }

    current = parent;
  }
}

export class ProjectPaths implements ResolvedProjectPaths {
  readonly repoRoot: string;
  readonly frontendRoot: string;
  readonly demoRoot: string;
  readonly generatedRoot: string;
  readonly candidateRoot: string;

  private constructor(paths: ResolvedProjectPaths) {
    this.repoRoot = paths.repoRoot;
    this.frontendRoot = paths.frontendRoot;
    this.demoRoot = paths.demoRoot;
    this.generatedRoot = paths.generatedRoot;
    this.candidateRoot = paths.candidateRoot;
  }

  static async create(options: ProjectPathsOptions = {}): Promise<ProjectPaths> {
    const configuredRoot = options.repoRoot
      ? path.resolve(options.repoRoot)
      : await findRepoRoot(options.cwd ?? process.cwd());
    const repoRoot = await fs.realpath(configuredRoot);
    const frontendRoot = path.join(repoRoot, FRONTEND_DIR);
    const demoRoot = path.join(frontendRoot, 'src', 'demo');
    const generatedRoot = path.join(repoRoot, ...DEMO_GENERATED_SEGMENTS);
    const candidateRoot = path.join(generatedRoot, 'candidates');

    await assertExistingDirectory(frontendRoot, 'frontendRoot');
    await assertExistingDirectory(demoRoot, 'demoRoot');

    return new ProjectPaths({
      repoRoot,
      frontendRoot,
      demoRoot,
      generatedRoot: path.resolve(generatedRoot),
      candidateRoot: path.resolve(candidateRoot),
    });
  }

  async resolveRepoReadPath(inputPath: string): Promise<string> {
    if (hasTraversal(inputPath)) {
      throw this.pathError(inputPath, 'path_traversal_rejected', 'Read paths cannot contain .. segments.');
    }

    const target = path.isAbsolute(inputPath)
      ? path.resolve(inputPath)
      : path.resolve(this.repoRoot, inputPath);
    const realTarget = await realpathIfExists(target);
    const realRepoRoot = await fs.realpath(this.repoRoot);

    if (!isInside(realRepoRoot, realTarget)) {
      throw this.pathError(
        inputPath,
        'read_outside_repo_rejected',
        'Read paths must resolve inside the repository root.'
      );
    }

    if (!(await pathExists(realTarget))) {
      throw this.pathError(inputPath, 'read_path_missing', 'Read path must exist before scanning.');
    }

    return realTarget;
  }

  async resolveGeneratedWritePath(relativePath: string): Promise<string> {
    return this.resolveWritePath(relativePath, this.generatedRoot, 'write_outside_generated_rejected');
  }

  async resolveCandidateWritePath(relativePath: string): Promise<string> {
    return this.resolveWritePath(relativePath, this.candidateRoot, 'write_outside_candidates_rejected');
  }

  relativeToRepo(inputPath: string): string {
    return path.relative(this.repoRoot, inputPath);
  }

  private async resolveWritePath(
    relativePath: string,
    allowedRoot: string,
    outsideCode: string
  ): Promise<string> {
    if (path.isAbsolute(relativePath)) {
      throw this.pathError(relativePath, 'absolute_path_rejected', 'Write paths must be repository-relative.');
    }

    if (hasTraversal(relativePath)) {
      throw this.pathError(relativePath, 'path_traversal_rejected', 'Write paths cannot contain .. segments.');
    }

    const target = path.resolve(allowedRoot, relativePath);
    const normalizedAllowedRoot = path.resolve(allowedRoot);

    if (!isInside(normalizedAllowedRoot, target)) {
      throw this.pathError(relativePath, outsideCode, 'Write paths must stay inside the generated scenario directory.');
    }

    await fs.mkdir(normalizedAllowedRoot, { recursive: true });

    const nearestExisting = await nearestExistingPath(target);
    const realNearestExisting = await fs.realpath(nearestExisting);
    const realAllowedRoot = await fs.realpath(normalizedAllowedRoot);

    if (!isInside(realAllowedRoot, realNearestExisting)) {
      throw this.pathError(relativePath, 'symlink_escape_rejected', 'Write path resolves outside the allowed root.');
    }

    if (await pathExists(target)) {
      const realTarget = await fs.realpath(target);

      if (!isInside(realAllowedRoot, realTarget)) {
        throw this.pathError(relativePath, 'symlink_escape_rejected', 'Write path resolves outside the allowed root.');
      }
    }

    return target;
  }

  private pathError(actual: string, code: string, fixHint: string): ToolError {
    return new ToolError(
      createIssue({
        path: actual,
        code,
        severity: 'error',
        actual,
        expected:
          'Read inside repository root; write inside ruoyi-fastapi-frontend/src/demo/scenarios/generated/**.',
        fixHint,
        autoRepairable: false,
      })
    );
  }
}

async function assertExistingDirectory(targetPath: string, label: string): Promise<void> {
  const stat = await fs.stat(targetPath).catch(() => undefined);

  if (!stat?.isDirectory()) {
    throw new ToolError(
      createIssue({
        path: label,
        code: 'required_directory_missing',
        severity: 'error',
        actual: targetPath,
        expected: 'Existing directory',
        fixHint: `Create or pass a repository root that contains ${label}.`,
        autoRepairable: false,
      })
    );
  }
}

export async function createTempRepoFixture(prefix = 'demo-offline-mcp-'): Promise<ProjectPaths> {
  const repoRoot = await fs.mkdtemp(path.join(os.tmpdir(), prefix));
  await fs.mkdir(path.join(repoRoot, FRONTEND_DIR, 'src', 'demo', 'scenarios', 'generated', 'candidates'), {
    recursive: true,
  });
  await fs.mkdir(path.join(repoRoot, 'ruoyi-fastapi-backend'), { recursive: true });
  await fs.writeFile(path.join(repoRoot, 'AGENTS.md'), '# test repo\n', 'utf8');

  return ProjectPaths.create({ repoRoot });
}
