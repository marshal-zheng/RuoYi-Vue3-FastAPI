import { describe, expect, it } from 'vitest';

import { defaultDemoScenario } from './default';
import {
  assertDemoContractExportSafe,
  canonicalJson,
  computeContractFingerprint,
  computeDemoScenarioFingerprint,
  computeDomcRegistryFingerprint,
  computePackageSha256,
  createDemoOfflineContractManifest,
  createDemoOfflineContractManifestDraft,
  createDemoDomcRegistry,
  createDemoDomcRegistryDraft,
  demoDomcRegistryJsonSchema,
  createRuntimePackageV2Release,
  demoScenarioJsonSchema,
  RUNTIME_PACKAGE_V2_ACTIVE_POINTER_PATH,
  RUNTIME_PACKAGE_V2_BUNDLE_DEFAULT_MANIFEST_PATH,
  RUNTIME_PACKAGE_V2_BUNDLE_DEFAULT_RELEASE_ID,
  validateDemoDomcRegistry,
} from './index';

describe('demo scenario contract primitives', () => {
  it('exports a local static JSON Schema without remote references', () => {
    expect(demoScenarioJsonSchema).toMatchObject({
      $schema: 'https://json-schema.org/draft/2020-12/schema',
      type: 'object',
      required: ['schemaVersion', 'scenario', 'auth', 'system', 'project', 'simulation'],
    });
    expect(JSON.stringify(demoScenarioJsonSchema)).not.toContain('"$ref"');
    expect(() => assertDemoContractExportSafe(demoScenarioJsonSchema)).not.toThrow();
  });

  it('canonicalizes JSON with stable object key ordering', () => {
    expect(canonicalJson({ b: 2, a: { d: 4, c: 3 } })).toBe(
      canonicalJson({ a: { c: 3, d: 4 }, b: 2 })
    );
  });

  it('separates scenario content identity from package hash', async () => {
    const scenarioFingerprint = await computeDemoScenarioFingerprint(defaultDemoScenario);
    const packageHash = await computePackageSha256(defaultDemoScenario);
    const declaredFingerprintChanged = {
      ...defaultDemoScenario,
      scenario: {
        ...defaultDemoScenario.scenario,
        fingerprint: 'changed-declared-fingerprint',
      },
    };

    await expect(computeDemoScenarioFingerprint(declaredFingerprintChanged)).resolves.toBe(
      scenarioFingerprint
    );
    await expect(computePackageSha256(declaredFingerprintChanged)).resolves.not.toBe(packageHash);
    expect(scenarioFingerprint).toMatch(/^[a-f0-9]{64}$/);
    expect(packageHash).toMatch(/^[a-f0-9]{64}$/);
  });

  it('computes contract fingerprints from stable contract inputs', async () => {
    const firstDraft = createDemoOfflineContractManifestDraft('2026-04-29T00:00:00.000Z');
    const secondDraft = {
      ...createDemoOfflineContractManifestDraft('2026-04-30T00:00:00.000Z'),
      contractFingerprint: 'ignored-existing-fingerprint',
    };
    const changedAdapterDraft = {
      ...firstDraft,
      runtimeAdapterVersion: 'changed-runtime-adapter',
    };

    await expect(computeContractFingerprint(secondDraft)).resolves.toBe(
      await computeContractFingerprint(firstDraft)
    );
    await expect(computeContractFingerprint(changedAdapterDraft)).resolves.not.toBe(
      await computeContractFingerprint(firstDraft)
    );
  });

  it('creates a safe P0 contract manifest with a reproducible fingerprint', async () => {
    const manifest = await createDemoOfflineContractManifest('2026-04-29T00:00:00.000Z');

    expect(manifest.contractFingerprint).toMatch(/^[a-f0-9]{64}$/);
    expect(manifest.generatedModules).toEqual(['project', 'simulation']);
    expect(manifest.copiedModules).toEqual(['auth', 'system']);
    expect(manifest.domcRegistryFingerprint).toMatch(/^[a-f0-9]{64}$/);
    expect(manifest.domcRegistryPath).toBe('demo-contract/domc.registry.json');
    expect(manifest.adapterReferences).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          moduleId: 'project',
          adapterId: 'project-simulation',
          capability: 'generatable',
        }),
        expect.objectContaining({
          moduleId: 'auth',
          adapterId: 'copy-only-default-scenario',
          capability: 'copyOnly',
        }),
      ])
    );
    expect(manifest.moduleContractFingerprints.project).toMatch(/^[a-f0-9]{64}$/);
    expect(manifest.indexedDbMapping.tables).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          table: 'projects',
          sourcePath: 'project.projects',
          primaryKey: 'projectId',
        }),
        expect.objectContaining({
          table: 'simulationSessions',
          sourcePath: 'simulation.sessions',
          primaryKey: 'sessionId',
        }),
      ])
    );
    expect(() => assertDemoContractExportSafe(manifest)).not.toThrow();
  });

  it('exports a local DOMC registry schema and stable registry fingerprint', async () => {
    const registry = await createDemoDomcRegistry('2026-04-29T00:00:00.000Z');
    const sameRegistryDifferentTime = createDemoDomcRegistryDraft('2026-04-30T00:00:00.000Z');
    const changedAdapterDraft = {
      ...createDemoDomcRegistryDraft('2026-04-29T00:00:00.000Z'),
      modules: createDemoDomcRegistryDraft('2026-04-29T00:00:00.000Z').modules.map((module) =>
        module.moduleId === 'project'
          ? {
              ...module,
              adapterRef: module.adapterRef
                ? { ...module.adapterRef, adapterVersionRange: '^2.0.0' }
                : module.adapterRef,
            }
          : module
      ),
    };

    expect(demoDomcRegistryJsonSchema).toMatchObject({
      $schema: 'https://json-schema.org/draft/2020-12/schema',
      title: 'DemoDomcRegistry',
    });
    expect(JSON.stringify(demoDomcRegistryJsonSchema)).not.toContain('"$ref"');
    await expect(computeDomcRegistryFingerprint(sameRegistryDifferentTime)).resolves.toBe(
      registry.domcFingerprint
    );
    await expect(computeDomcRegistryFingerprint(changedAdapterDraft)).resolves.not.toBe(
      registry.domcFingerprint
    );
    expect(await validateDemoDomcRegistry(registry)).toMatchObject({ valid: true });
  });

  it('describes project/simulation as generatable and auth/system as copyOnly DOMC modules', async () => {
    const registry = await createDemoDomcRegistry('2026-04-29T00:00:00.000Z');

    expect(registry.modules).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          moduleId: 'project',
          capability: 'generatable',
          adapterRef: expect.objectContaining({ adapterId: 'project-simulation' }),
          sourcePaths: ['project.projects', 'project.versions', 'project.topologies'],
        }),
        expect.objectContaining({
          moduleId: 'simulation',
          capability: 'generatable',
          sourcePaths: expect.arrayContaining(['simulation.sessions', 'simulation.streamFrames']),
        }),
        expect.objectContaining({
          moduleId: 'auth',
          capability: 'copyOnly',
          copyOnly: expect.objectContaining({ source: 'demo-contract/default-scenario.json' }),
        }),
        expect.objectContaining({
          moduleId: 'system',
          capability: 'copyOnly',
          copyOnly: expect.objectContaining({ source: 'demo-contract/default-scenario.json' }),
        }),
      ])
    );
  });

  it('returns DOMC validation issues for invalid sourcePath drift', async () => {
    const registry = await createDemoDomcRegistry('2026-04-29T00:00:00.000Z');
    const invalidRegistry = {
      ...registry,
      domcFingerprint: '',
      modules: registry.modules.map((module) =>
        module.moduleId === 'project'
          ? {
              ...module,
              sourcePaths: ['project.projects', 'project.missing'],
            }
          : module
      ),
    };

    const validation = await validateDemoDomcRegistry(invalidRegistry);

    expect(validation.valid).toBe(false);
    expect(validation.issues).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ code: 'domc_source_path_table_mapping_missing' }),
      ])
    );
  });

  it('materializes bundle-default as a v2 release store without v1 runtime paths', async () => {
    const release = await createRuntimePackageV2Release({
      releaseId: RUNTIME_PACKAGE_V2_BUNDLE_DEFAULT_RELEASE_ID,
      scenarioPackage: defaultDemoScenario,
      contractFingerprint: 'a'.repeat(64),
      generatorVersion: 'test-generator',
      generatedAt: '2026-04-29T00:00:00.000Z',
      topicKey: 'default',
      topicSummary: 'Default',
      seed: defaultDemoScenario.scenario.seed ?? 'default',
      materializationReason: 'copied-default',
      domcRegistryFingerprint: 'b'.repeat(64),
      moduleContractFingerprints: { project: 'c'.repeat(64) },
      adapterVersions: { 'project-simulation': '1.0.0' },
      adapterCapabilitySummary: [
        {
          moduleId: 'project',
          adapterId: 'project-simulation',
          adapterVersion: '1.0.0',
          outputSourcePaths: ['project.projects'],
        },
      ],
    });
    const outputPaths = [
      RUNTIME_PACKAGE_V2_ACTIVE_POINTER_PATH,
      RUNTIME_PACKAGE_V2_BUNDLE_DEFAULT_MANIFEST_PATH,
      'demo-scenarios/releases/bundle-default/provenance.json',
      ...release.slices.map(
        (slice) => `demo-scenarios/releases/bundle-default/${slice.descriptor.path}`
      ),
    ];

    expect(release.pointer.manifestPath).toBe(RUNTIME_PACKAGE_V2_BUNDLE_DEFAULT_MANIFEST_PATH);
    expect(release.pointer.manifestSha256).toBe(release.manifest.rootSha256);
    expect(release.manifest.descriptors).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ kind: 'provenance', path: 'provenance.json' }),
        expect.objectContaining({ kind: 'slice', sourcePath: 'project.projects' }),
        expect.objectContaining({ kind: 'slice', sourcePath: 'simulation.sessions' }),
      ])
    );
    expect(release.provenance).toMatchObject({
      domcRegistryFingerprint: 'b'.repeat(64),
      moduleContractFingerprints: { project: 'c'.repeat(64) },
      adapterVersions: { 'project-simulation': '1.0.0' },
    });
    expect(release.provenance.materials).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ kind: 'domc-registry' }),
        expect.objectContaining({ kind: 'domc-module-contract' }),
        expect.objectContaining({ kind: 'generator-adapter' }),
      ])
    );
    expect(outputPaths).not.toContain('demo-scenarios/active.json');
    expect(outputPaths).not.toContain('demo-scenarios/previous.json');
    expect(outputPaths).not.toContain('demo-scenarios/active.meta.json');
  });

  it('records materializationReason per sourcePath when DOMC provenance supplies it', async () => {
    const release = await createRuntimePackageV2Release({
      releaseId: 'domc-reason-demo',
      scenarioPackage: defaultDemoScenario,
      contractFingerprint: 'a'.repeat(64),
      generatorVersion: 'test-generator',
      generatedAt: '2026-04-29T00:00:00.000Z',
      topicKey: 'domc-reason-demo',
      topicSummary: 'DOMC reason demo',
      seed: defaultDemoScenario.scenario.seed ?? 'default',
      materializationReason: 'runtime-required',
      materializationReasonsBySourcePath: {
        'auth.accounts': 'copied-default',
        'project.projects': 'semantic-generated',
      },
    });
    const descriptors = release.manifest.descriptors.filter((descriptor) => descriptor.kind === 'slice');

    expect(descriptors).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          sourcePath: 'auth.accounts',
          materializationReason: 'copied-default',
        }),
        expect.objectContaining({
          sourcePath: 'project.projects',
          materializationReason: 'semantic-generated',
        }),
        expect.objectContaining({
          sourcePath: 'system.menus',
          materializationReason: 'runtime-required',
        }),
      ])
    );
  });
});
