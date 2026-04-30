import { describe, expect, it, vi } from 'vitest';

import {
  canonicalJsonSizeBytes,
  computeManifestRootSha256,
  createRuntimePackageV2Release,
  defaultDemoScenario,
  releaseAssetPath,
  sha256CanonicalJson,
  type DemoScenarioPackage,
  type RuntimePackageV2Manifest,
  type RuntimePackageV2ReleaseFiles,
} from '@/demo/scenarios';

import type { DemoRuntimeLogger } from './logger';
import type { RuntimeConfig } from './mode';
import { loadRuntimeScenarioPackage, runtimeScenarioPackagePaths } from './scenario-package-loader';

const CONTRACT_FINGERPRINT = 'a'.repeat(64);

const runtimeConfig: RuntimeConfig = {
  mode: 'demo-offline',
  mockMode: 'pure',
  apiPrefix: '/api',
  scenarioId: 'default',
  allowCandidateScenarios: false,
  debug: true,
  source: 'runtime-mode',
};

const logger: DemoRuntimeLogger = {
  debug: vi.fn(),
  info: vi.fn(),
  warn: vi.fn(),
  error: vi.fn(),
};

function cloneScenario(overrides: Partial<DemoScenarioPackage['scenario']>): DemoScenarioPackage {
  return {
    ...defaultDemoScenario,
    scenario: {
      ...defaultDemoScenario.scenario,
      ...overrides,
    },
  };
}

async function createRelease(
  releaseId: string,
  scenarioPackage: DemoScenarioPackage
): Promise<RuntimePackageV2ReleaseFiles> {
  return createRuntimePackageV2Release({
    releaseId,
    scenarioPackage,
    contractFingerprint: CONTRACT_FINGERPRINT,
    generatorVersion: 'test-generator',
    generatedAt: '2026-04-29T00:00:00.000Z',
    activatedAt: '2026-04-29T00:00:00.000Z',
    topicKey: scenarioPackage.scenario.id,
    topicSummary: scenarioPackage.scenario.name,
    seed: scenarioPackage.scenario.seed ?? releaseId,
    materializationReason: 'runtime-required',
  });
}

function releaseRecords(release: RuntimePackageV2ReleaseFiles): Record<string, unknown> {
  return {
    [release.pointer.manifestPath]: release.manifest,
    [releaseAssetPath(release.manifest.releaseId, 'provenance.json')]: release.provenance,
    ...Object.fromEntries(
      release.slices.map((slice) => [
        releaseAssetPath(release.manifest.releaseId, slice.descriptor.path),
        slice.data,
      ])
    ),
  };
}

function createFetchJson(records: Record<string, unknown>) {
  return vi.fn(async (path: string): Promise<unknown> => {
    if (!(path in records)) {
      throw new Error(`missing ${path}`);
    }

    return records[path];
  }) as unknown as ReturnType<typeof vi.fn> & (<T>(path: string) => Promise<T>);
}

describe('RuntimeScenarioPackageLoader', () => {
  it('loads active v2 release and imports it', async () => {
    const active = cloneScenario({ id: 'runtime-active-demo' });
    const activeRelease = await createRelease('runtime-active-demo', active);
    const fetchJson = createFetchJson({
      [runtimeScenarioPackagePaths.activePointer]: activeRelease.pointer,
      ...releaseRecords(activeRelease),
    });
    const importScenario = vi.fn(async () => ({ imported: true }));

    const selection = await loadRuntimeScenarioPackage(runtimeConfig, logger, {
      fetchJson,
      contractFingerprint: CONTRACT_FINGERPRINT,
      importScenario,
    });

    expect(selection.source).toBe('runtime-active-v2');
    expect(selection.package.scenario.id).toBe('runtime-active-demo');
    expect(importScenario).toHaveBeenCalledWith(
      expect.objectContaining({ source: 'runtime-active-v2' })
    );
  });

  it('loads the current shell fingerprint from demo-contract when no override is injected', async () => {
    const active = cloneScenario({ id: 'runtime-contract-artifact-demo' });
    const activeRelease = await createRelease('runtime-contract-artifact-demo', active);
    const fetchJson = createFetchJson({
      [runtimeScenarioPackagePaths.contractManifest]: {
        contractFingerprint: CONTRACT_FINGERPRINT,
      },
      [runtimeScenarioPackagePaths.activePointer]: activeRelease.pointer,
      ...releaseRecords(activeRelease),
    });

    const selection = await loadRuntimeScenarioPackage(runtimeConfig, logger, {
      fetchJson,
    });

    expect(selection.source).toBe('runtime-active-v2');
    expect(selection.package.scenario.id).toBe('runtime-contract-artifact-demo');
    expect(fetchJson).toHaveBeenCalledWith(runtimeScenarioPackagePaths.contractManifest);
  });

  it('falls back to previous v2 when active manifest hash fails', async () => {
    const activeRelease = await createRelease(
      'runtime-active-demo',
      cloneScenario({ id: 'runtime-active-demo' })
    );
    const previousRelease = await createRelease(
      'runtime-previous-demo',
      cloneScenario({ id: 'runtime-previous-demo' })
    );
    const brokenActiveManifest = {
      ...activeRelease.manifest,
      rootSha256: 'b'.repeat(64),
    };
    const fetchJson = createFetchJson({
      [runtimeScenarioPackagePaths.activePointer]: activeRelease.pointer,
      [runtimeScenarioPackagePaths.previousPointer]: previousRelease.pointer,
      ...releaseRecords(activeRelease),
      [activeRelease.pointer.manifestPath]: brokenActiveManifest,
      ...releaseRecords(previousRelease),
    });

    const selection = await loadRuntimeScenarioPackage(runtimeConfig, logger, {
      fetchJson,
      contractFingerprint: CONTRACT_FINGERPRINT,
    });

    expect(selection.source).toBe('runtime-previous-v2');
    expect(selection.package.scenario.id).toBe('runtime-previous-demo');
    expect(selection.fallbackReason).toMatchObject({
      source: 'runtime-active-v2',
      stage: 'manifest',
    });
  });

  it('falls back when provenance schema is invalid even if hashes are consistent', async () => {
    const activeRelease = await createRelease(
      'runtime-active-demo',
      cloneScenario({ id: 'runtime-active-demo' })
    );
    const previousRelease = await createRelease(
      'runtime-previous-demo',
      cloneScenario({ id: 'runtime-previous-demo' })
    );
    const brokenProvenance = {
      ...activeRelease.provenance,
      topicKey: '',
    };
    const brokenManifest: RuntimePackageV2Manifest = {
      ...activeRelease.manifest,
      descriptors: activeRelease.manifest.descriptors.map((descriptor) =>
        descriptor.kind === 'provenance'
          ? {
              ...descriptor,
              sha256: '',
              sizeBytes: canonicalJsonSizeBytes(brokenProvenance),
            }
          : descriptor
      ),
    };
    const provenanceDescriptor = brokenManifest.descriptors.find(
      (descriptor) => descriptor.kind === 'provenance'
    );
    if (!provenanceDescriptor) throw new Error('missing provenance descriptor');
    provenanceDescriptor.sha256 = await sha256CanonicalJson(brokenProvenance);
    brokenManifest.rootSha256 = await computeManifestRootSha256(brokenManifest);
    activeRelease.pointer.manifestSha256 = brokenManifest.rootSha256;

    const fetchJson = createFetchJson({
      [runtimeScenarioPackagePaths.activePointer]: activeRelease.pointer,
      [runtimeScenarioPackagePaths.previousPointer]: previousRelease.pointer,
      ...releaseRecords(activeRelease),
      [activeRelease.pointer.manifestPath]: brokenManifest,
      [releaseAssetPath(activeRelease.manifest.releaseId, 'provenance.json')]: brokenProvenance,
      ...releaseRecords(previousRelease),
    });

    const selection = await loadRuntimeScenarioPackage(runtimeConfig, logger, {
      fetchJson,
      contractFingerprint: CONTRACT_FINGERPRINT,
    });

    expect(selection.source).toBe('runtime-previous-v2');
    expect(selection.fallbackReason).toMatchObject({
      source: 'runtime-active-v2',
      code: 'DEMO_RUNTIME_V2_PROVENANCE_INVALID',
    });
  });

  it('falls back to fixed bundle-default v2 when active and previous fail', async () => {
    const defaultRelease = await createRelease('bundle-default', defaultDemoScenario);
    const fetchJson = createFetchJson({
      [runtimeScenarioPackagePaths.bundleDefaultManifest]: defaultRelease.manifest,
      ...releaseRecords(defaultRelease),
    });

    const selection = await loadRuntimeScenarioPackage(runtimeConfig, logger, {
      fetchJson,
      contractFingerprint: CONTRACT_FINGERPRINT,
    });

    expect(selection.source).toBe('bundle-default-v2');
    expect(selection.package.scenario.id).toBe('default');
    expect(selection.fallbackReason).toMatchObject({
      source: 'runtime-previous-v2',
    });
  });

  it('does not depend on timeline during startup', async () => {
    const activeRelease = await createRelease(
      'runtime-active-demo',
      cloneScenario({ id: 'runtime-active-demo' })
    );
    const fetchJson = createFetchJson({
      [runtimeScenarioPackagePaths.activePointer]: activeRelease.pointer,
      'demo-scenarios/timeline.json': { broken: true },
      ...releaseRecords(activeRelease),
    });

    const selection = await loadRuntimeScenarioPackage(runtimeConfig, logger, {
      fetchJson,
      contractFingerprint: CONTRACT_FINGERPRINT,
    });

    expect(selection.source).toBe('runtime-active-v2');
    expect(fetchJson).not.toHaveBeenCalledWith('demo-scenarios/timeline.json');
  });

  it('ignores legacy v1 residue files', async () => {
    const activeRelease = await createRelease(
      'runtime-active-demo',
      cloneScenario({ id: 'runtime-active-demo' })
    );
    const fetchJson = createFetchJson({
      [runtimeScenarioPackagePaths.activePointer]: activeRelease.pointer,
      [runtimeScenarioPackagePaths.legacyActive]: { legacy: true },
      [runtimeScenarioPackagePaths.legacyPrevious]: { legacy: true },
      [runtimeScenarioPackagePaths.legacyActiveMeta]: { legacy: true },
      ...releaseRecords(activeRelease),
    });

    const selection = await loadRuntimeScenarioPackage(runtimeConfig, logger, {
      fetchJson,
      contractFingerprint: CONTRACT_FINGERPRINT,
    });

    expect(selection.source).toBe('runtime-active-v2');
    expect(fetchJson).not.toHaveBeenCalledWith(runtimeScenarioPackagePaths.legacyActive);
    expect(fetchJson).not.toHaveBeenCalledWith(runtimeScenarioPackagePaths.legacyPrevious);
    expect(fetchJson).not.toHaveBeenCalledWith(runtimeScenarioPackagePaths.legacyActiveMeta);
  });

  it('falls back to previous v2 when active import fails', async () => {
    const activeRelease = await createRelease(
      'runtime-active-demo',
      cloneScenario({ id: 'runtime-active-demo' })
    );
    const previousRelease = await createRelease(
      'runtime-previous-demo',
      cloneScenario({ id: 'runtime-previous-demo' })
    );
    const fetchJson = createFetchJson({
      [runtimeScenarioPackagePaths.activePointer]: activeRelease.pointer,
      [runtimeScenarioPackagePaths.previousPointer]: previousRelease.pointer,
      ...releaseRecords(activeRelease),
      ...releaseRecords(previousRelease),
    });
    const importScenario = vi
      .fn()
      .mockRejectedValueOnce(new Error('active import failed'))
      .mockResolvedValueOnce({ imported: true });

    const selection = await loadRuntimeScenarioPackage(runtimeConfig, logger, {
      fetchJson,
      contractFingerprint: CONTRACT_FINGERPRINT,
      importScenario,
    });

    expect(selection.source).toBe('runtime-previous-v2');
    expect(importScenario).toHaveBeenCalledTimes(2);
  });
});
