import {
  assertDescriptorJsonIntegrity,
  assertRuntimePackageManifest,
  assertRuntimePackagePointer,
  assertRuntimePackageProvenance,
  assembleScenarioPackageFromRelease,
  computePackageSha256,
  DEMO_OFFLINE_CONTRACT_MANIFEST_PATH,
  releaseAssetPath,
  RUNTIME_PACKAGE_V2_ACTIVE_POINTER_PATH,
  RUNTIME_PACKAGE_V2_BUNDLE_DEFAULT_MANIFEST_PATH,
  RUNTIME_PACKAGE_V2_BUNDLE_DEFAULT_RELEASE_ID,
  RUNTIME_PACKAGE_V2_PREVIOUS_POINTER_PATH,
  type DemoOfflineContractManifest,
  type DemoScenarioPackage,
  type RuntimePackageDescriptor,
  type RuntimePackagePointer,
  type RuntimePackageV2Manifest,
  type RuntimeScenarioLoadIssue,
  type RuntimeScenarioMeta,
  type RuntimeScenarioSelection,
  type RuntimeScenarioSource,
  type RuntimeSliceDescriptor,
} from '@/demo/scenarios';

import type { DemoRuntimeLogger } from './logger';
import type { RuntimeConfig } from './mode';

export interface LoadRuntimeScenarioPackageOptions<TImportResult = unknown> {
  fetchJson?: <T>(path: string) => Promise<T>;
  now?: () => number;
  contractFingerprint?: string;
  importScenario?: (selection: RuntimeScenarioSelection<TImportResult>) => Promise<TImportResult>;
}

function createIssue(
  source: RuntimeScenarioLoadIssue['source'],
  stage: RuntimeScenarioLoadIssue['stage'],
  code: string,
  error: unknown
): RuntimeScenarioLoadIssue {
  return {
    source,
    stage,
    code,
    message: error instanceof Error ? error.message : String(error),
  };
}

function resolveRuntimeAssetUrl(path: string, now: () => number): string {
  const baseUri =
    typeof document !== 'undefined'
      ? document.baseURI
      : typeof window !== 'undefined'
        ? window.location.href
        : 'http://localhost/';
  const url = new URL(path, baseUri);
  url.searchParams.set('_demo_ts', String(now()));
  return url.toString();
}

async function fetchRuntimeJson<T>(path: string, now: () => number): Promise<T> {
  const response = await fetch(resolveRuntimeAssetUrl(path, now), { cache: 'no-store' });
  if (!response.ok) {
    throw new Error(`Failed to load ${path}: HTTP ${response.status}.`);
  }

  return response.json() as Promise<T>;
}

async function getCurrentContractFingerprint(options: {
  contractFingerprint?: string;
  fetchJson: <T>(path: string) => Promise<T>;
}): Promise<string> {
  if (options.contractFingerprint) {
    return options.contractFingerprint;
  }

  const contract = await options.fetchJson<Partial<DemoOfflineContractManifest>>(
    DEMO_OFFLINE_CONTRACT_MANIFEST_PATH
  );

  if (
    typeof contract.contractFingerprint !== 'string' ||
    !/^[a-f0-9]{64}$/.test(contract.contractFingerprint)
  ) {
    throw new Error('demo-contract/contract.json contractFingerprint is missing or invalid.');
  }

  return contract.contractFingerprint;
}

async function importSelection<TImportResult>(
  selection: RuntimeScenarioSelection<TImportResult>,
  options: LoadRuntimeScenarioPackageOptions<TImportResult>
): Promise<RuntimeScenarioSelection<TImportResult>> {
  if (!options.importScenario) {
    return selection;
  }

  return {
    ...selection,
    importResult: await options.importScenario(selection),
  };
}

function assertPointerCompatible(
  pointer: RuntimePackagePointer,
  manifest: RuntimePackageV2Manifest,
  contractFingerprint: string
): void {
  if (pointer.manifestSha256 !== manifest.rootSha256) {
    throw new Error('active.pointer.json manifestSha256 does not match manifest.rootSha256.');
  }

  if (pointer.contractFingerprint !== contractFingerprint) {
    throw new Error('active.pointer.json contractFingerprint does not match the current demo-offline shell.');
  }

  if (pointer.contractFingerprint !== manifest.contractFingerprint) {
    throw new Error('active.pointer.json contractFingerprint does not match manifest.contractFingerprint.');
  }

  if (pointer.scenarioFingerprint !== manifest.scenarioFingerprint) {
    throw new Error('active.pointer.json scenarioFingerprint does not match manifest scenarioFingerprint.');
  }
}

async function loadManifest(
  fetchJson: <T>(path: string) => Promise<T>,
  source: RuntimeScenarioSource,
  path: string,
  contractFingerprint: string,
  expectedReleaseId?: string
): Promise<RuntimePackageV2Manifest> {
  let manifestValue: unknown;
  try {
    manifestValue = await fetchJson<RuntimePackageV2Manifest>(path);
  } catch (error) {
    throw createIssue(source, 'manifest', 'DEMO_RUNTIME_V2_MANIFEST_FETCH_FAILED', error);
  }

  try {
    return await assertRuntimePackageManifest(manifestValue, {
      releaseId: expectedReleaseId,
      contractFingerprint,
    });
  } catch (error) {
    throw createIssue(source, 'manifest', 'DEMO_RUNTIME_V2_MANIFEST_INVALID', error);
  }
}

async function fetchDescriptorJson(
  fetchJson: <T>(path: string) => Promise<T>,
  source: RuntimeScenarioSource,
  manifest: RuntimePackageV2Manifest,
  descriptor: RuntimePackageDescriptor
): Promise<unknown> {
  const path = releaseAssetPath(manifest.releaseId, descriptor.path);
  try {
    return await fetchJson<unknown>(path);
  } catch (error) {
    throw createIssue(source, 'descriptor', 'DEMO_RUNTIME_V2_DESCRIPTOR_FETCH_FAILED', error);
  }
}

async function assembleReleasePackage(
  fetchJson: <T>(path: string) => Promise<T>,
  source: RuntimeScenarioSource,
  manifest: RuntimePackageV2Manifest
): Promise<{ packageValue: DemoScenarioPackage; meta: RuntimeScenarioMeta }> {
  const slices: Array<{ descriptor: RuntimeSliceDescriptor; data: unknown }> = [];
  let hasProvenance = false;

  for (const descriptor of manifest.descriptors) {
    const descriptorJson = await fetchDescriptorJson(fetchJson, source, manifest, descriptor);

    try {
      await assertDescriptorJsonIntegrity(descriptor, descriptorJson);
    } catch (error) {
      throw createIssue(source, 'hash', 'DEMO_RUNTIME_V2_DESCRIPTOR_HASH_INVALID', error);
    }

    if (descriptor.kind === 'provenance') {
      hasProvenance = true;
      try {
        assertRuntimePackageProvenance(descriptorJson, { manifest });
      } catch (error) {
        throw createIssue(source, 'schema', 'DEMO_RUNTIME_V2_PROVENANCE_INVALID', error);
      }
    }

    if (descriptor.kind === 'slice') {
      slices.push({ descriptor, data: descriptorJson });
    }
  }

  if (!hasProvenance) {
    throw createIssue(
      source,
      'descriptor',
      'DEMO_RUNTIME_V2_PROVENANCE_DESCRIPTOR_MISSING',
      'manifest descriptors must include provenance.json'
    );
  }

  let packageValue: DemoScenarioPackage;
  try {
    packageValue = await assembleScenarioPackageFromRelease({ manifest, slices });
  } catch (error) {
    throw createIssue(source, 'schema', 'DEMO_RUNTIME_V2_PACKAGE_ASSEMBLY_FAILED', error);
  }

  const packageSha256 = await computePackageSha256(packageValue);

  return {
    packageValue,
    meta: {
      scenarioId: manifest.scenarioId,
      topicKey: manifest.scenarioId,
      schemaVersion: manifest.schemaVersion,
      contractFingerprint: manifest.contractFingerprint,
      generatorVersion: manifest.generatorVersion,
      seed: manifest.seed,
      generatedAt: manifest.generatedAt,
      validationSummary: {
        schemaValid: true,
        contractValid: true,
        invariantValid: true,
        dryRunValid: true,
        issueCount: 0,
      },
      sourceTarget: 'offline-static',
      scenarioFingerprint: manifest.scenarioFingerprint,
      packageSha256,
      releaseId: manifest.releaseId,
      manifestPath: `demo-scenarios/releases/${manifest.releaseId}/manifest.json`,
      manifestSha256: manifest.rootSha256,
      provenancePath: `demo-scenarios/releases/${manifest.releaseId}/provenance.json`,
    },
  };
}

async function tryLoadPointerRelease<TImportResult>(
  fetchJson: <T>(path: string) => Promise<T>,
  source: Exclude<RuntimeScenarioSource, 'bundle-default-v2'>,
  pointerPath: string,
  contractFingerprint: string,
  fallbackReason: RuntimeScenarioLoadIssue | undefined,
  options: LoadRuntimeScenarioPackageOptions<TImportResult>
): Promise<RuntimeScenarioSelection<TImportResult>> {
  let pointer: RuntimePackagePointer;
  try {
    pointer = assertRuntimePackagePointer(await fetchJson<RuntimePackagePointer>(pointerPath));
  } catch (error) {
    throw createIssue(source, 'pointer', 'DEMO_RUNTIME_V2_POINTER_INVALID', error);
  }

  const manifest = await loadManifest(
    fetchJson,
    source,
    pointer.manifestPath,
    contractFingerprint,
    pointer.releaseId
  );

  try {
    assertPointerCompatible(pointer, manifest, contractFingerprint);
  } catch (error) {
    throw createIssue(source, 'pointer', 'DEMO_RUNTIME_V2_POINTER_CONTRACT_INVALID', error);
  }

  const { packageValue, meta } = await assembleReleasePackage(fetchJson, source, manifest);
  const selection: RuntimeScenarioSelection<TImportResult> = {
    source,
    package: packageValue,
    meta,
    fallbackReason,
  };

  try {
    return await importSelection(selection, options);
  } catch (error) {
    throw createIssue(source, 'import', 'DEMO_RUNTIME_V2_IMPORT_FAILED', error);
  }
}

async function loadBundleDefault<TImportResult>(
  fetchJson: <T>(path: string) => Promise<T>,
  contractFingerprint: string,
  fallbackReason: RuntimeScenarioLoadIssue | undefined,
  options: LoadRuntimeScenarioPackageOptions<TImportResult>
): Promise<RuntimeScenarioSelection<TImportResult>> {
  const manifest = await loadManifest(
    fetchJson,
    'bundle-default-v2',
    RUNTIME_PACKAGE_V2_BUNDLE_DEFAULT_MANIFEST_PATH,
    contractFingerprint,
    RUNTIME_PACKAGE_V2_BUNDLE_DEFAULT_RELEASE_ID
  );
  const { packageValue, meta } = await assembleReleasePackage(
    fetchJson,
    'bundle-default-v2',
    manifest
  );
  const selection: RuntimeScenarioSelection<TImportResult> = {
    source: 'bundle-default-v2',
    package: packageValue,
    meta,
    fallbackReason,
  };

  try {
    return await importSelection(selection, options);
  } catch (error) {
    throw createIssue('bundle-default-v2', 'import', 'DEMO_RUNTIME_V2_IMPORT_FAILED', error);
  }
}

export async function loadRuntimeScenarioPackage<TImportResult = unknown>(
  _config: RuntimeConfig,
  logger: DemoRuntimeLogger,
  options: LoadRuntimeScenarioPackageOptions<TImportResult> = {}
): Promise<RuntimeScenarioSelection<TImportResult>> {
  const now = options.now ?? Date.now;
  const fetchJson = options.fetchJson ?? (<T>(path: string) => fetchRuntimeJson<T>(path, now));
  const contractFingerprint = await getCurrentContractFingerprint({ ...options, fetchJson });

  try {
    return await tryLoadPointerRelease(
      fetchJson,
      'runtime-active-v2',
      RUNTIME_PACKAGE_V2_ACTIVE_POINTER_PATH,
      contractFingerprint,
      undefined,
      options
    );
  } catch (activeIssue) {
    const issue = activeIssue as RuntimeScenarioLoadIssue;
    logger.warn('runtime active v2 release 不可用，尝试 previous pointer。', issue);

    try {
      return await tryLoadPointerRelease(
        fetchJson,
        'runtime-previous-v2',
        RUNTIME_PACKAGE_V2_PREVIOUS_POINTER_PATH,
        contractFingerprint,
        issue,
        options
      );
    } catch (previousIssue) {
      const fallbackIssue = previousIssue as RuntimeScenarioLoadIssue;
      logger.warn('runtime previous v2 release 不可用，回退 bundle default v2 release。', fallbackIssue);
      return loadBundleDefault(fetchJson, contractFingerprint, fallbackIssue, options);
    }
  }
}

export const runtimeScenarioPackagePaths = {
  activePointer: RUNTIME_PACKAGE_V2_ACTIVE_POINTER_PATH,
  previousPointer: RUNTIME_PACKAGE_V2_PREVIOUS_POINTER_PATH,
  bundleDefaultManifest: RUNTIME_PACKAGE_V2_BUNDLE_DEFAULT_MANIFEST_PATH,
  contractManifest: DEMO_OFFLINE_CONTRACT_MANIFEST_PATH,
  legacyActive: 'demo-scenarios/active.json',
  legacyPrevious: 'demo-scenarios/previous.json',
  legacyActiveMeta: 'demo-scenarios/active.meta.json',
} as const;
