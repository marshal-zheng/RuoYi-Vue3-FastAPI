import fs from 'node:fs/promises';
import path from 'node:path';

import { createIssue, ToolError } from '../errors.js';

export interface OfflineStaticTargetPaths {
  targetRoot: string;
  demoScenariosRoot: string;
  demoContractRoot: string;
  activePointerPath: string;
  previousPointerPath: string;
  timelinePath: string;
  releasesRoot: string;
  stagingRoot: string;
  failedRoot: string;
  bundleDefaultManifestPath: string;
  /** @deprecated v1 residue path, retained only for diagnostics/tests during hard-cut cleanup. */
  activePath: string;
  /** @deprecated v1 residue path, retained only for diagnostics/tests during hard-cut cleanup. */
  activeMetaPath: string;
  /** @deprecated v1 residue path, retained only for diagnostics/tests during hard-cut cleanup. */
  previousPath: string;
  /** @deprecated v1 candidate path, not used by v2 release store. */
  activeNextPath: string;
  /** @deprecated v1 candidate path, not used by v2 release store. */
  activeNextMetaPath: string;
  /** @deprecated v1 active semantic report path, not used by v2 release store. */
  activeSemanticReportPath: string;
  /** @deprecated v1 candidate semantic report path, not used by v2 release store. */
  activeNextSemanticReportPath: string;
  semanticFailedReportPath: string;
  auditLogPath: string;
}

export interface ResolveOfflineStaticTargetOptions {
  targetRoot: string;
}

function isInside(parent: string, child: string): boolean {
  const relativePath = path.relative(parent, child);
  return relativePath === '' || (!relativePath.startsWith('..') && !path.isAbsolute(relativePath));
}

function hasTraversal(value: string): boolean {
  return value.split(/[\\/]+/).some((segment) => segment === '..');
}

async function pathExists(value: string): Promise<boolean> {
  return fs
    .access(value)
    .then(() => true)
    .catch(() => false);
}

async function nearestExistingPath(value: string): Promise<string> {
  let current = path.resolve(value);

  while (!(await pathExists(current))) {
    const parent = path.dirname(current);
    if (parent === current) return current;
    current = parent;
  }

  return current;
}

function offlinePathError(pathValue: string, code: string, fixHint: string): ToolError {
  return new ToolError(
    createIssue({
      path: pathValue,
      code,
      severity: 'error',
      actual: pathValue,
      expected: 'Read demo-contract/** and write demo-scenarios/** inside the offline package root.',
      fixHint,
      autoRepairable: false,
    })
  );
}

export async function resolveOfflineStaticTargetPaths(
  options: ResolveOfflineStaticTargetOptions
): Promise<OfflineStaticTargetPaths> {
  if (!options.targetRoot?.trim()) {
    throw offlinePathError('target.root', 'offline_static_target_root_required', 'Pass target.root pointing to dist-demo-offline.');
  }

  if (hasTraversal(options.targetRoot)) {
    throw offlinePathError(options.targetRoot, 'path_traversal_rejected', 'target.root cannot contain .. segments.');
  }

  const targetRoot = await fs.realpath(path.resolve(options.targetRoot)).catch(() => undefined);

  if (!targetRoot) {
    throw offlinePathError(
      options.targetRoot,
      'offline_static_target_missing',
      'Build or provide a dist-demo-offline directory before using offline-static target.'
    );
  }

  const demoScenariosRoot = path.join(targetRoot, 'demo-scenarios');
  const demoContractRoot = path.join(targetRoot, 'demo-contract');
  const releasesRoot = path.join(demoScenariosRoot, 'releases');

  return {
    targetRoot,
    demoScenariosRoot,
    demoContractRoot,
    activePointerPath: path.join(demoScenariosRoot, 'active.pointer.json'),
    previousPointerPath: path.join(demoScenariosRoot, 'previous.pointer.json'),
    timelinePath: path.join(demoScenariosRoot, 'timeline.json'),
    releasesRoot,
    stagingRoot: path.join(releasesRoot, '.staging'),
    failedRoot: path.join(releasesRoot, '.failed'),
    bundleDefaultManifestPath: path.join(releasesRoot, 'bundle-default', 'manifest.json'),
    activePath: path.join(demoScenariosRoot, 'active.json'),
    activeMetaPath: path.join(demoScenariosRoot, 'active.meta.json'),
    previousPath: path.join(demoScenariosRoot, 'previous.json'),
    activeNextPath: path.join(demoScenariosRoot, 'active.next.json'),
    activeNextMetaPath: path.join(demoScenariosRoot, 'active.next.meta.json'),
    activeSemanticReportPath: path.join(demoScenariosRoot, 'active.semantic-report.json'),
    activeNextSemanticReportPath: path.join(demoScenariosRoot, 'active.next.semantic-report.json'),
    semanticFailedReportPath: path.join(demoScenariosRoot, 'semantic-failed-report.json'),
    auditLogPath: path.join(targetRoot, '.audit', 'demo-offline-mcp.jsonl'),
  };
}

export async function assertOfflineStaticReadPath(paths: OfflineStaticTargetPaths, filePath: string): Promise<string> {
  const resolved = path.resolve(filePath);
  const realRoot = await fs.realpath(paths.targetRoot);
  const realTarget = await fs.realpath(resolved).catch(() => undefined);

  if (!realTarget || !isInside(realRoot, realTarget)) {
    throw offlinePathError(filePath, 'offline_static_read_rejected', 'Read paths must exist inside the offline package root.');
  }

  if (!isInside(path.join(realRoot, 'demo-contract'), realTarget) && !isInside(path.join(realRoot, 'demo-scenarios'), realTarget)) {
    throw offlinePathError(filePath, 'offline_static_read_rejected', 'Only demo-contract/** and demo-scenarios/** are readable.');
  }

  return realTarget;
}

export async function assertOfflineStaticScenarioWritePath(
  paths: OfflineStaticTargetPaths,
  filePath: string
): Promise<string> {
  const resolved = path.resolve(filePath);
  const realRoot = await fs.realpath(paths.targetRoot);
  const scenarioRoot = path.join(realRoot, 'demo-scenarios');

  if (!isInside(scenarioRoot, resolved)) {
    throw offlinePathError(filePath, 'write_outside_demo_scenarios_rejected', 'Writes are limited to demo-scenarios/**.');
  }

  if (resolved === path.join(realRoot, 'index.html') || isInside(path.join(realRoot, 'assets'), resolved)) {
    throw offlinePathError(filePath, 'offline_static_forbidden_write_rejected', 'Do not write index.html or assets/**.');
  }

  await fs.mkdir(scenarioRoot, { recursive: true });
  const nearestExisting = await nearestExistingPath(resolved);
  const realNearestExisting = await fs.realpath(nearestExisting);

  if (!isInside(scenarioRoot, realNearestExisting)) {
    throw offlinePathError(filePath, 'symlink_escape_rejected', 'Write path resolves outside demo-scenarios/**.');
  }

  if (await pathExists(resolved)) {
    const realTarget = await fs.realpath(resolved);
    if (!isInside(scenarioRoot, realTarget)) {
      throw offlinePathError(filePath, 'symlink_escape_rejected', 'Write target resolves outside demo-scenarios/**.');
    }
  }

  return resolved;
}

export async function assertOfflineStaticReleaseStoreWritePath(
  paths: OfflineStaticTargetPaths,
  filePath: string
): Promise<string> {
  const resolved = await assertOfflineStaticScenarioWritePath(paths, filePath);
  const realRoot = await fs.realpath(paths.targetRoot);

  if (resolved === path.join(realRoot, 'index.html') || isInside(path.join(realRoot, 'assets'), resolved)) {
    throw offlinePathError(filePath, 'offline_static_forbidden_write_rejected', 'Do not write index.html or assets/**.');
  }

  return resolved;
}

export function releaseDirectoryPath(paths: OfflineStaticTargetPaths, releaseId: string): string {
  return path.join(paths.releasesRoot, releaseId);
}

export function stagingReleaseDirectoryPath(paths: OfflineStaticTargetPaths, releaseId: string): string {
  return path.join(paths.stagingRoot, releaseId);
}

export function failedReleaseDirectoryPath(paths: OfflineStaticTargetPaths, releaseId: string): string {
  return path.join(paths.failedRoot, releaseId);
}

export function relativeToOfflineRoot(paths: OfflineStaticTargetPaths, filePath: string): string {
  return path.relative(paths.targetRoot, filePath).split(path.sep).join('/');
}
