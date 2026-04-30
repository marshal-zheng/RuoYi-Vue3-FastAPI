import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';

import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import { computeContractFingerprint, readOfflineStaticContract } from '../src/offline-static/contract.js';
import {
  computeDomcModuleFingerprints,
  computeDomcRegistryFingerprint,
} from '../src/domc.js';
import { generateOfflineStaticRuntimePackage } from '../src/offline-static/generate.js';
import { dryRunImportRuntimePackage } from '../src/offline-static/import-dry-run.js';
import { validateRuntimeInvariants } from '../src/offline-static/invariants.js';
import {
  assertOfflineStaticScenarioWritePath,
  resolveOfflineStaticTargetPaths,
} from '../src/offline-static/paths.js';
import {
  canonicalJsonSizeBytes,
  computeManifestRootSha256,
  createRuntimePackageV2Release,
  RUNTIME_PACKAGE_V2_BUNDLE_DEFAULT_RELEASE_ID,
  RUNTIME_PACKAGE_V2_MAX_SLICE_BYTES,
  RUNTIME_PACKAGE_V2_MAX_SLICE_RECORDS,
  type RuntimePackagePointer,
  type RuntimePackageV2Manifest,
} from '../src/offline-static/release-store.js';
import {
  activateRuntimePackage,
  createRuntimeScenarioMeta,
  validateRuntimeRelease,
  writeRuntimeCandidatePackage,
} from '../src/offline-static/writer.js';
import { computePackageSha256, computeScenarioFingerprint, sha256CanonicalJson } from '../src/hash.js';
import { createSemanticIssue } from '../src/semantic/index.js';
import type {
  CompiledDemoScenarioPackage,
  DemoDomcModuleContract,
  DemoDomcRegistry,
  DemoOfflineContractManifest,
  RuntimeScenarioMeta,
} from '../src/types.js';

let targetRoot: string;

function createScenarioPackage(id = 'runtime-writer-demo'): CompiledDemoScenarioPackage {
  return {
    schemaVersion: 1,
    scenario: {
      id,
      name: 'Runtime Writer Demo',
      version: '1.0.0',
      fingerprint: `${id}-fingerprint`,
      seed: id,
    },
    auth: {
      accounts: [
        {
          username: 'admin',
          password: 'admin123',
          userId: 1,
          roleIds: [1],
          roles: ['admin'],
          permissions: ['*:*:*'],
          user: { userName: 'admin' },
        },
      ],
      roles: [{ roleId: 1, roleKey: 'admin', roleName: '管理员', menuIds: [1], permissions: ['*:*:*'] }],
      permissions: [{ id: 'all', code: '*:*:*', label: '全部权限' }],
    },
    system: {
      menus: [
        {
          menuId: 1,
          parentId: 0,
          name: 'Demo',
          path: '/demo',
          orderNum: 1,
          visible: '0',
          status: '0',
          roles: ['admin'],
        },
      ],
      dictTypes: [{ dictId: 1, dictName: '演示字典', dictType: 'demo_type', status: '0' }],
      dicts: [{ id: 1, dictType: 'demo_type', dictLabel: '演示', dictValue: 'demo', dictSort: 1, status: '0' }],
      departments: [{ deptId: 100, parentId: 0, deptName: '演示部门', orderNum: 1, status: '0' }],
      posts: [{ postId: 1, postCode: 'demo', postName: '演示岗位', postSort: 1, status: '0' }],
      users: [
        {
          userId: 1,
          deptId: 100,
          userName: 'admin',
          nickName: '管理员',
          status: '0',
          roleIds: [1],
          postIds: [1],
        },
      ],
    },
    project: {
      projects: [
        {
          projectId: 1001,
          projectName: '演示项目',
          status: '0',
          createTime: '2026-04-29T00:00:00.000Z',
          updateTime: '2026-04-29T00:00:00.000Z',
        },
      ],
      versions: [
        {
          versionId: 2001,
          projectId: 1001,
          versionName: '演示版本',
          locked: true,
          status: '0',
          createTime: '2026-04-29T00:00:00.000Z',
          updateTime: '2026-04-29T00:00:00.000Z',
        },
      ],
      topologies: [
        {
          id: 'topology-1',
          projectId: 1001,
          versionId: 2001,
          graph: {
            nodes: [
              { id: 'node-1', label: '入口' },
              { id: 'node-2', label: '复核' },
            ],
            edges: [{ id: 'edge-1', source: 'node-1', target: 'node-2' }],
          },
          updateTime: '2026-04-29T00:00:00.000Z',
        },
      ],
    },
    simulation: {
      sessions: [
        {
          sessionId: 'session-1',
          projectId: 1001,
          versionId: 2001,
          status: 'running',
          createTime: '2026-04-29T00:00:00.000Z',
          updateTime: '2026-04-29T00:00:00.000Z',
        },
      ],
      messages: [{ id: 'message-1', sessionId: 'session-1', timestamp: '2026-04-29T00:00:00.000Z' }],
      bandwidth: [{ id: 'bandwidth-1', sessionId: 'session-1', portId: 'port-1', timestamp: '2026-04-29T00:00:00.000Z' }],
      alarms: [{ alarmId: 'alarm-1', sessionId: 'session-1', timestamp: '2026-04-29T00:00:00.000Z', severity: 'medium' }],
      faults: [],
      events: [{ eventId: 'event-1', sessionId: 'session-1', triggerTime: '2026-04-29T00:00:00.000Z' }],
      streamFrames: [{ frameId: 'frame-1', sessionId: 'session-1', order: 1, type: 'summary', delayMs: 10, payload: {} }],
    },
  };
}

function createScenarioSchemaFixture(): Record<string, unknown> {
  return {
    $schema: 'https://json-schema.org/draft/2020-12/schema',
    title: 'DemoScenarioPackage',
    type: 'object',
    required: ['schemaVersion', 'scenario', 'auth', 'system', 'project', 'simulation'],
    properties: {
      schemaVersion: { enum: [1] },
      scenario: {
        type: 'object',
        required: ['id', 'name', 'version', 'fingerprint'],
        properties: {
          id: { type: 'string' },
          name: { type: 'string' },
          version: { type: 'string' },
          fingerprint: { type: 'string' },
          seed: { type: 'string' },
        },
      },
      project: {
        type: 'object',
        required: ['projects', 'versions', 'topologies'],
        properties: {
          projects: {
            type: 'array',
            items: {
              type: 'object',
              required: ['projectId', 'projectName', 'status', 'createTime', 'updateTime'],
              properties: {
                projectId: { type: 'number' },
                projectName: { type: 'string' },
                status: { enum: ['0', '1'] },
                createTime: { type: 'string' },
                updateTime: { type: 'string' },
              },
            },
          },
          versions: { type: 'array' },
          topologies: { type: 'array' },
        },
      },
    },
  };
}

function createMinimalDomcModule(input: {
  moduleId: string;
  capability: 'generatable' | 'copyOnly';
  sourcePaths: string[];
  contract: DemoOfflineContractManifest;
}): DemoDomcModuleContract {
  const tables = input.contract.indexedDbMapping.tables.filter((table) => input.sourcePaths.includes(table.sourcePath));
  const firstSourcePath = input.sourcePaths[0];
  const handlerSource = `src/demo/handlers/${input.moduleId}.ts`;

  return {
    moduleId: input.moduleId,
    moduleVersion: '1.0.0',
    lifecycle: 'active',
    capability: input.capability,
    owner: 'unit-test',
    sourcePaths: input.sourcePaths,
    indexedDbTables: tables,
    handlerCoverage: [
      {
        module: input.moduleId,
        source: handlerSource,
        apiPrefix: '/api',
        coveredRoutes: [`GET /${input.moduleId}`],
        unsupportedBehavior: 'DEMO_API_NOT_IMPLEMENTED',
      },
    ],
    uiJourneys: [
      {
        journeyId: `${input.moduleId}-journey`,
        entry: `/${input.moduleId}`,
        primarySourcePath: firstSourcePath,
        requiredSupportSourcePaths: input.sourcePaths.slice(1),
        listFields: [tables[0]?.primaryKey ?? 'id'],
        detailFields: [tables[0]?.primaryKey ?? 'id'],
        keyActions: [{ action: 'list', demoBehavior: 'unit-test' }],
        emptyState: 'unit-test empty',
        errorState: 'unit-test error',
        minimumDemoChain: input.sourcePaths,
      },
    ],
    entities: tables.map((table) => ({
      entity: `${input.moduleId}.${table.table}`,
      sourcePath: table.sourcePath,
      indexedDbTable: table.table,
      primaryKey: table.primaryKey,
      minItems: table.minItems ?? 0,
      fields: [
        {
          name: table.primaryKey,
          required: true,
          nullable: false,
          semanticKind: 'identifier',
          defaultRepair: 'block',
        },
      ],
      references: [],
      ownership: {
        recordOwner: input.capability === 'copyOnly' ? 'default-scenario' : 'adapter',
        mergePolicy: input.capability === 'copyOnly' ? 'copy-only' : 'replace-sourcePath',
      },
    })),
    stateMachines: [],
    invariants: [],
    diversityRules: [],
    materializationPolicy: input.sourcePaths.map((sourcePath, index) => ({
      sourcePath,
      order: (index + 1) * 100000,
      materializationReason: input.capability === 'copyOnly' ? 'copied-default' : 'semantic-generated',
      minItems: tables.find((table) => table.sourcePath === sourcePath)?.minItems ?? 0,
    })),
    ...(input.capability === 'generatable'
      ? {
          adapterRef: {
            adapterId: 'project-simulation',
            adapterVersionRange: '^1.0.0',
            capabilities: ['business-blueprint', 'sourcePath-materialization', 'semantic-anchor-bindings', 'deterministic-seed'],
            outputSourcePaths: input.sourcePaths,
            priority: 100,
          },
        }
      : {
          copyOnly: {
            source: 'demo-contract/default-scenario.json',
            sourcePaths: input.sourcePaths,
            reason: 'unit-test copyOnly module',
            minItems: Object.fromEntries(tables.map((table) => [table.sourcePath, table.minItems ?? 0])),
          },
        }),
    migrationSources: ['unit-test'],
  };
}

function createDomcRegistry(contract: DemoOfflineContractManifest): DemoDomcRegistry {
  const registry: DemoDomcRegistry = {
    schemaVersion: 1,
    registryVersion: 'unit-test-domc',
    generatedAt: '2026-04-29T00:00:00.000Z',
    domcFingerprint: '',
    contractVersion: 1,
    platformLayer: 'DOMC',
    modules: [
      createMinimalDomcModule({
        moduleId: 'auth',
        capability: 'copyOnly',
        sourcePaths: ['auth.accounts', 'auth.roles', 'auth.permissions'],
        contract,
      }),
      createMinimalDomcModule({
        moduleId: 'system',
        capability: 'copyOnly',
        sourcePaths: ['system.menus', 'system.dictTypes', 'system.dicts', 'system.departments', 'system.posts', 'system.users'],
        contract,
      }),
      createMinimalDomcModule({
        moduleId: 'project',
        capability: 'generatable',
        sourcePaths: ['project.projects', 'project.versions', 'project.topologies'],
        contract,
      }),
      createMinimalDomcModule({
        moduleId: 'simulation',
        capability: 'generatable',
        sourcePaths: [
          'simulation.sessions',
          'simulation.messages',
          'simulation.bandwidth',
          'simulation.alarms',
          'simulation.faults',
          'simulation.events',
          'simulation.streamFrames',
        ],
        contract,
      }),
    ],
    qualityGates: [{ gate: 'domc-schema' }],
    migrationSources: ['unit-test'],
  };
  registry.domcFingerprint = computeDomcRegistryFingerprint(registry);
  return registry;
}

function createContract(schema: Record<string, unknown>): {
  contract: DemoOfflineContractManifest;
  domcRegistry: DemoDomcRegistry;
} {
  const contract: DemoOfflineContractManifest = {
    contractVersion: 1,
    schemaVersion: 1,
    generatedAt: '2026-04-29T00:00:00.000Z',
    runtimeAdapterVersion: 'runtime-test',
    generatorAdapterVersion: 'generator-test',
    contractFingerprint: '',
    supportedModules: ['auth', 'system', 'project', 'simulation'],
    generatedModules: ['project', 'simulation'],
    copiedModules: ['auth', 'system'],
    domcRegistryFingerprint: '',
    domcRegistryPath: 'demo-contract/domc.registry.json',
    moduleContractFingerprints: {},
    adapterReferences: [],
    indexedDbMapping: {
      dbName: 'ruoyi-demo-offline',
      dbVersion: 2,
      tables: [
        { table: 'accounts', sourcePath: 'auth.accounts', primaryKey: 'username', indexes: ['userId'], minItems: 1 },
        { table: 'roles', sourcePath: 'auth.roles', primaryKey: 'roleId', indexes: ['roleKey'], minItems: 1 },
        { table: 'permissions', sourcePath: 'auth.permissions', primaryKey: 'id', indexes: ['code'], minItems: 1 },
        { table: 'menus', sourcePath: 'system.menus', primaryKey: 'menuId', indexes: ['path'], minItems: 1 },
        { table: 'dictTypes', sourcePath: 'system.dictTypes', primaryKey: 'dictId', indexes: ['dictType'] },
        { table: 'dicts', sourcePath: 'system.dicts', primaryKey: 'id', indexes: ['dictType'] },
        { table: 'departments', sourcePath: 'system.departments', primaryKey: 'deptId', indexes: ['parentId'] },
        { table: 'posts', sourcePath: 'system.posts', primaryKey: 'postId', indexes: ['postCode'] },
        { table: 'systemUsers', sourcePath: 'system.users', primaryKey: 'userId', indexes: ['userName'] },
        { table: 'projects', sourcePath: 'project.projects', primaryKey: 'projectId', indexes: ['projectName'], minItems: 1 },
        { table: 'projectVersions', sourcePath: 'project.versions', primaryKey: 'versionId', indexes: ['projectId'], minItems: 1 },
        { table: 'topologies', sourcePath: 'project.topologies', primaryKey: 'id', indexes: ['projectId'], minItems: 1 },
        { table: 'simulationSessions', sourcePath: 'simulation.sessions', primaryKey: 'sessionId', indexes: ['projectId'], minItems: 1 },
        { table: 'simulationMessages', sourcePath: 'simulation.messages', primaryKey: 'id', indexes: ['sessionId'] },
        { table: 'simulationBandwidth', sourcePath: 'simulation.bandwidth', primaryKey: 'id', indexes: ['sessionId'] },
        { table: 'simulationAlarms', sourcePath: 'simulation.alarms', primaryKey: 'alarmId', indexes: ['sessionId'] },
        { table: 'simulationFaults', sourcePath: 'simulation.faults', primaryKey: 'faultId', indexes: ['sessionId'] },
        { table: 'simulationEvents', sourcePath: 'simulation.events', primaryKey: 'eventId', indexes: ['sessionId'] },
        { table: 'simulationFrames', sourcePath: 'simulation.streamFrames', primaryKey: 'frameId', indexes: ['sessionId'] },
      ],
    },
    handlerCoverage: [],
    moduleContracts: [],
    invariants: [],
  };
  const domcRegistry = createDomcRegistry(contract);
  contract.domcRegistryFingerprint = domcRegistry.domcFingerprint;
  contract.moduleContractFingerprints = computeDomcModuleFingerprints(domcRegistry);
  contract.adapterReferences = domcRegistry.modules.map((moduleContract) => ({
    moduleId: moduleContract.moduleId,
    adapterId: moduleContract.adapterRef?.adapterId ?? 'copy-only-default-scenario',
    adapterVersionRange: moduleContract.adapterRef?.adapterVersionRange ?? 'default-scenario',
    capability: moduleContract.capability,
    outputSourcePaths: moduleContract.adapterRef?.outputSourcePaths ?? moduleContract.sourcePaths,
  }));
  contract.contractFingerprint = computeContractFingerprint(contract, schema);
  return { contract, domcRegistry };
}

async function writeJson(filePath: string, value: unknown): Promise<void> {
  await fs.mkdir(path.dirname(filePath), { recursive: true });
  await fs.writeFile(filePath, `${JSON.stringify(value, null, 2)}\n`, 'utf8');
}

async function writeRelease(root: string, release: ReturnType<typeof createRuntimePackageV2Release>): Promise<void> {
  const releaseDir = path.join(root, 'demo-scenarios', 'releases', release.manifest.releaseId);
  for (const slice of release.slices) {
    await writeJson(path.join(releaseDir, slice.descriptor.path), slice.data);
  }
  for (const artifact of release.artifacts) {
    await writeJson(path.join(releaseDir, artifact.descriptor.path), artifact.data);
  }
  await writeJson(path.join(releaseDir, 'provenance.json'), release.provenance);
  await writeJson(path.join(releaseDir, 'manifest.json'), release.manifest);
}

async function readStagedManifest(paths: Awaited<ReturnType<typeof resolveOfflineStaticTargetPaths>>, releaseId: string) {
  const manifestPath = path.join(paths.stagingRoot, releaseId, 'manifest.json');
  return JSON.parse(await fs.readFile(manifestPath, 'utf8')) as RuntimePackageV2Manifest;
}

async function writeStagedManifest(
  paths: Awaited<ReturnType<typeof resolveOfflineStaticTargetPaths>>,
  releaseId: string,
  manifest: RuntimePackageV2Manifest
): Promise<void> {
  manifest.rootSha256 = computeManifestRootSha256(manifest);
  await writeJson(path.join(paths.stagingRoot, releaseId, 'manifest.json'), manifest);
}

async function writeOfflineFixture(): Promise<void> {
  targetRoot = await fs.mkdtemp(path.join(os.tmpdir(), 'offline-static-target-'));
  const defaultScenario = createScenarioPackage('default');
  defaultScenario.scenario.fingerprint = computeScenarioFingerprint(defaultScenario);
  const schema = createScenarioSchemaFixture();
  const { contract, domcRegistry } = createContract(schema);
  const defaultRelease = createRuntimePackageV2Release({
    releaseId: RUNTIME_PACKAGE_V2_BUNDLE_DEFAULT_RELEASE_ID,
    scenarioPackage: defaultScenario,
    contractFingerprint: contract.contractFingerprint,
    generatorVersion: 'generator-test',
    generatedAt: '2026-04-29T00:00:00.000Z',
    topicKey: 'default',
    topicSummary: 'Default',
    seed: 'default',
    validationSummary: {
      schemaValid: true,
      contractValid: true,
      invariantValid: true,
      dryRunValid: true,
      issueCount: 0,
    },
    materializationReason: 'copied-default',
    tableMappings: contract.indexedDbMapping.tables,
  });

  await fs.mkdir(path.join(targetRoot, 'demo-contract'), { recursive: true });
  await fs.mkdir(path.join(targetRoot, 'demo-scenarios'), { recursive: true });
  await fs.mkdir(path.join(targetRoot, 'assets'), { recursive: true });
  await fs.writeFile(path.join(targetRoot, 'index.html'), '<!doctype html>\n', 'utf8');
  await writeJson(path.join(targetRoot, 'demo-contract', 'contract.json'), contract);
  await writeJson(path.join(targetRoot, 'demo-contract', 'domc.registry.json'), domcRegistry);
  await writeJson(path.join(targetRoot, 'demo-contract', 'domc.registry.schema.json'), {
    $schema: 'https://json-schema.org/draft/2020-12/schema',
    title: 'UnitTestDomcRegistry',
    type: 'object',
  });
  await writeJson(path.join(targetRoot, 'demo-contract', 'scenario.schema.json'), schema);
  await writeJson(path.join(targetRoot, 'demo-contract', 'default-scenario.json'), defaultScenario);
  await writeRelease(targetRoot, defaultRelease);
  await writeJson(path.join(targetRoot, 'demo-scenarios', 'active.pointer.json'), defaultRelease.pointer);
  await writeJson(path.join(targetRoot, 'demo-scenarios', 'active.json'), { legacy: true });
}

async function createRuntimeMeta(
  scenarioPackage: CompiledDemoScenarioPackage
): Promise<RuntimeScenarioMeta> {
  const paths = await resolveOfflineStaticTargetPaths({ targetRoot });
  const { contract } = await readOfflineStaticContract(paths);
  return createRuntimeScenarioMeta({
    scenarioPackage,
    topicKey: scenarioPackage.scenario.id,
    seed: scenarioPackage.scenario.seed ?? scenarioPackage.scenario.id,
    contractFingerprint: contract.contractFingerprint,
    generatorVersion: 'generator-test',
    validationSummary: {
      schemaValid: true,
      contractValid: true,
      invariantValid: true,
      issueCount: 0,
    },
  });
}

describe('offline-static target v2 release store', () => {
  beforeEach(writeOfflineFixture);

  afterEach(async () => {
    await fs.rm(targetRoot, { recursive: true, force: true });
  });

  it('enforces target write boundaries', async () => {
    const paths = await resolveOfflineStaticTargetPaths({ targetRoot });

    await expect(assertOfflineStaticScenarioWritePath(paths, paths.activePointerPath)).resolves.toBe(paths.activePointerPath);
    await expect(assertOfflineStaticScenarioWritePath(paths, path.join(targetRoot, 'assets', 'bad.json'))).rejects.toMatchObject({
      issue: expect.objectContaining({ code: 'write_outside_demo_scenarios_rejected' }),
    });
    await expect(assertOfflineStaticScenarioWritePath(paths, path.join(targetRoot, 'index.html'))).rejects.toMatchObject({
      issue: expect.objectContaining({ code: 'write_outside_demo_scenarios_rejected' }),
    });
  });

  it('reads contract files and validates the contract fingerprint', async () => {
    const paths = await resolveOfflineStaticTargetPaths({ targetRoot });
    await expect(readOfflineStaticContract(paths)).resolves.toMatchObject({
      contract: {
        contractFingerprint: expect.stringMatching(/^[a-f0-9]{64}$/),
      },
    });

    const contractPath = path.join(targetRoot, 'demo-contract', 'contract.json');
    const contract = JSON.parse(await fs.readFile(contractPath, 'utf8')) as DemoOfflineContractManifest;
    contract.runtimeAdapterVersion = 'changed';
    await fs.writeFile(contractPath, `${JSON.stringify(contract, null, 2)}\n`, 'utf8');

    await expect(readOfflineStaticContract(paths)).rejects.toMatchObject({
      issue: expect.objectContaining({ code: 'contract_fingerprint_mismatch' }),
    });
  });

  it('returns structured invariant issues for broken cross references', () => {
    const scenarioPackage = createScenarioPackage();
    scenarioPackage.project.versions[0].projectId = 9999;

    expect(validateRuntimeInvariants(scenarioPackage)).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          path: 'project.versions[0].projectId',
          code: 'project_version_project_missing',
        }),
      ])
    );
  });

  it('dry-runs IndexedDB import in an isolated database', async () => {
    const paths = await resolveOfflineStaticTargetPaths({ targetRoot });
    const { contract } = await readOfflineStaticContract(paths);
    const result = await dryRunImportRuntimePackage(contract, createScenarioPackage());

    expect(result).toMatchObject({
      ok: true,
      data: {
        inserted: {
          projects: 1,
          simulationSessions: 1,
        },
      },
    });
  });

  it('stages, publishes, and activates with previous pointer backup', async () => {
    const paths = await resolveOfflineStaticTargetPaths({ targetRoot });
    const scenarioPackage = createScenarioPackage('activated-demo');
    scenarioPackage.scenario.fingerprint = computeScenarioFingerprint(scenarioPackage);
    const meta = await createRuntimeMeta(scenarioPackage);

    const staged = await writeRuntimeCandidatePackage(paths, scenarioPackage, meta);
    expect(staged).toMatchObject({
      ok: true,
      data: {
        phase: 'staged',
        packageFormat: 'v2',
        releaseId: expect.any(String),
      },
    });

    const activated = await activateRuntimePackage(paths, { releaseId: staged.data?.releaseId });
    expect(activated).toMatchObject({
      ok: true,
      data: {
        phase: 'activated',
        activePointerPath: 'demo-scenarios/active.pointer.json',
        previousPointerPath: 'demo-scenarios/previous.pointer.json',
      },
    });

    const previousPointer = JSON.parse(await fs.readFile(paths.previousPointerPath, 'utf8')) as RuntimePackagePointer;
    const activePointer = JSON.parse(await fs.readFile(paths.activePointerPath, 'utf8')) as RuntimePackagePointer;
    expect(previousPointer.releaseId).toBe('bundle-default');
    expect(activePointer.releaseId).toBe(staged.data?.releaseId);
    await expect(fs.readFile(path.join(paths.releasesRoot, activePointer.releaseId, 'manifest.json'), 'utf8')).resolves.toContain(
      'activated-demo'
    );
  });

  it('blocks existing published releaseIds and keeps active pointer unchanged', async () => {
    const paths = await resolveOfflineStaticTargetPaths({ targetRoot });
    const scenarioPackage = createScenarioPackage('immutable-demo');
    scenarioPackage.scenario.fingerprint = computeScenarioFingerprint(scenarioPackage);
    const meta = await createRuntimeMeta(scenarioPackage);
    const firstStage = await writeRuntimeCandidatePackage(paths, scenarioPackage, meta);
    await activateRuntimePackage(paths, { releaseId: firstStage.data?.releaseId });
    const before = await fs.readFile(paths.activePointerPath, 'utf8');
    const result = await writeRuntimeCandidatePackage(paths, scenarioPackage, meta);

    expect(result).toMatchObject({
      ok: false,
      errors: expect.arrayContaining([
        expect.objectContaining({ code: 'runtime_v2_release_already_exists' }),
      ]),
    });
    await expect(fs.readFile(paths.activePointerPath, 'utf8')).resolves.toBe(before);
  });

  it('does not switch active pointer when staged release validation fails', async () => {
    const paths = await resolveOfflineStaticTargetPaths({ targetRoot });
    const scenarioPackage = createScenarioPackage('bad-demo');
    scenarioPackage.project.projects = [];
    scenarioPackage.scenario.fingerprint = computeScenarioFingerprint(scenarioPackage);
    const meta = await createRuntimeMeta(scenarioPackage);
    const before = await fs.readFile(paths.activePointerPath, 'utf8');

    const staged = await writeRuntimeCandidatePackage(paths, scenarioPackage, meta);

    expect(staged).toMatchObject({
      ok: false,
      errors: expect.arrayContaining([
        expect.objectContaining({ code: 'runtime_v2_release_materialization_failed' }),
      ]),
    });
    await expect(fs.readFile(paths.activePointerPath, 'utf8')).resolves.toBe(before);
  });

  it('quarantines staging when IndexedDB import dry-run fails', async () => {
    const paths = await resolveOfflineStaticTargetPaths({ targetRoot });
    const scenarioPackage = createScenarioPackage('dry-run-fails-demo');
    scenarioPackage.system.dicts = [
      {
        dictType: 'demo_type',
        dictLabel: '缺少主键',
        dictValue: 'missing-primary-key',
        dictSort: 1,
        status: '0',
      },
    ];
    scenarioPackage.scenario.fingerprint = computeScenarioFingerprint(scenarioPackage);
    const meta = await createRuntimeMeta(scenarioPackage);
    const before = await fs.readFile(paths.activePointerPath, 'utf8');
    const staged = await writeRuntimeCandidatePackage(paths, scenarioPackage, meta);
    const releaseId = staged.data!.releaseId!;

    const result = await activateRuntimePackage(paths, { releaseId });

    expect(result).toMatchObject({
      ok: false,
      data: {
        phase: 'dry_run_failed',
      },
      errors: expect.arrayContaining([
        expect.objectContaining({ code: 'runtime_import_dry_run_failed' }),
      ]),
    });
    await expect(fs.readFile(paths.activePointerPath, 'utf8')).resolves.toBe(before);
    await expect(fs.access(path.join(paths.stagingRoot, releaseId))).rejects.toBeTruthy();
    await expect(fs.access(path.join(paths.failedRoot, releaseId))).resolves.toBeUndefined();
  });

  it('detects manifest descriptor hash corruption', async () => {
    const paths = await resolveOfflineStaticTargetPaths({ targetRoot });
    const scenarioPackage = createScenarioPackage('hash-demo');
    scenarioPackage.scenario.fingerprint = computeScenarioFingerprint(scenarioPackage);
    const meta = await createRuntimeMeta(scenarioPackage);
    const staged = await writeRuntimeCandidatePackage(paths, scenarioPackage, meta);
    const releaseId = staged.data!.releaseId!;
    const provenancePath = path.join(
      paths.stagingRoot,
      releaseId,
      'provenance.json'
    );
    await writeJson(provenancePath, { corrupted: true });

    const result = await validateRuntimeRelease(paths, releaseId, { fromStaging: true });

    expect(result).toMatchObject({
      ok: false,
      errors: expect.arrayContaining([
        expect.objectContaining({ code: 'runtime_v2_descriptor_sha256_mismatch' }),
      ]),
    });
  });

  it('rejects invalid provenance even when descriptor and manifest hashes are updated', async () => {
    const paths = await resolveOfflineStaticTargetPaths({ targetRoot });
    const scenarioPackage = createScenarioPackage('provenance-schema-demo');
    scenarioPackage.scenario.fingerprint = computeScenarioFingerprint(scenarioPackage);
    const meta = await createRuntimeMeta(scenarioPackage);
    const staged = await writeRuntimeCandidatePackage(paths, scenarioPackage, meta);
    const releaseId = staged.data!.releaseId!;
    const manifest = await readStagedManifest(paths, releaseId);
    const provenancePath = path.join(paths.stagingRoot, releaseId, 'provenance.json');
    const provenance = JSON.parse(await fs.readFile(provenancePath, 'utf8')) as Record<string, unknown>;
    delete provenance.topicKey;
    const provenanceDescriptor = manifest.descriptors.find((descriptor) => descriptor.kind === 'provenance')!;
    provenanceDescriptor.sha256 = sha256CanonicalJson(provenance);
    provenanceDescriptor.sizeBytes = canonicalJsonSizeBytes(provenance);

    await writeJson(provenancePath, provenance);
    await writeStagedManifest(paths, releaseId, manifest);

    const result = await validateRuntimeRelease(paths, releaseId, { fromStaging: true });

    expect(result).toMatchObject({
      ok: false,
      errors: expect.arrayContaining([
        expect.objectContaining({ code: 'runtime_v2_provenance_schema_invalid' }),
      ]),
    });
  });

  it('rejects slice descriptors missing required v2 metadata after root hash recomputation', async () => {
    const paths = await resolveOfflineStaticTargetPaths({ targetRoot });
    const scenarioPackage = createScenarioPackage('descriptor-schema-demo');
    scenarioPackage.scenario.fingerprint = computeScenarioFingerprint(scenarioPackage);
    const meta = await createRuntimeMeta(scenarioPackage);
    const staged = await writeRuntimeCandidatePackage(paths, scenarioPackage, meta);
    const releaseId = staged.data!.releaseId!;
    const manifest = await readStagedManifest(paths, releaseId);
    const sliceDescriptor = manifest.descriptors.find((descriptor) => descriptor.kind === 'slice') as
      | (RuntimePackageV2Manifest['descriptors'][number] & { module?: string })
      | undefined;
    expect(sliceDescriptor).toBeTruthy();
    delete sliceDescriptor!.module;
    await writeStagedManifest(paths, releaseId, manifest);

    const result = await validateRuntimeRelease(paths, releaseId, { fromStaging: true });

    expect(result).toMatchObject({
      ok: false,
      errors: expect.arrayContaining([
        expect.objectContaining({ code: 'runtime_v2_manifest_schema_invalid' }),
      ]),
    });
  });

  it('splits oversized sourcePath slices into stable reviewable shards', async () => {
    const paths = await resolveOfflineStaticTargetPaths({ targetRoot });
    const { contract } = await readOfflineStaticContract(paths);
    const scenarioPackage = createScenarioPackage('sharded-demo');
    scenarioPackage.project.projects = Array.from(
      { length: RUNTIME_PACKAGE_V2_MAX_SLICE_RECORDS + 1 },
      (_, index) => ({
        projectId: 1001 + index,
        projectName: `演示项目-${index}`,
        status: '0',
        createTime: '2026-04-29T00:00:00.000Z',
        updateTime: '2026-04-29T00:00:00.000Z',
      })
    );
    scenarioPackage.scenario.fingerprint = computeScenarioFingerprint(scenarioPackage);

    const release = createRuntimePackageV2Release({
      releaseId: 'sharded-demo-release',
      scenarioPackage,
      contractFingerprint: contract.contractFingerprint,
      generatorVersion: 'generator-test',
      generatedAt: '2026-04-29T00:00:00.000Z',
      topicKey: 'sharded-demo',
      topicSummary: 'Sharded Demo',
      seed: 'sharded-demo',
      validationSummary: {
        schemaValid: true,
        contractValid: true,
        invariantValid: true,
        dryRunValid: true,
        issueCount: 0,
      },
      tableMappings: contract.indexedDbMapping.tables,
    });
    const projectSlices = release.slices.filter(
      (slice) => slice.descriptor.sourcePath === 'project.projects'
    );

    expect(projectSlices).toHaveLength(2);
    expect(projectSlices.map((slice) => slice.descriptor.path)).toEqual([
      'slices/project.projects.part-001.json',
      'slices/project.projects.part-002.json',
    ]);
    expect(projectSlices.reduce((total, slice) => total + slice.descriptor.recordCount, 0)).toBe(
      RUNTIME_PACKAGE_V2_MAX_SLICE_RECORDS + 1
    );
    projectSlices.forEach((slice) => {
      expect(slice.descriptor.recordCount).toBeLessThanOrEqual(RUNTIME_PACKAGE_V2_MAX_SLICE_RECORDS);
      expect(slice.descriptor.sizeBytes).toBeLessThanOrEqual(RUNTIME_PACKAGE_V2_MAX_SLICE_BYTES);
    });
    expect(projectSlices[0].descriptor).toMatchObject({ shardIndex: 0, shardCount: 2 });
    expect(projectSlices[1].descriptor).toMatchObject({ shardIndex: 1, shardCount: 2 });
  });

  it('computes scenario fingerprints by deleting the declared fingerprint field', () => {
    const scenarioPackage = createScenarioPackage('fingerprint-demo');
    const deleteInput = JSON.parse(JSON.stringify(scenarioPackage)) as CompiledDemoScenarioPackage & {
      scenario: Partial<CompiledDemoScenarioPackage['scenario']>;
    };
    const blankInput = JSON.parse(JSON.stringify(scenarioPackage)) as CompiledDemoScenarioPackage;
    delete deleteInput.scenario.fingerprint;
    blankInput.scenario.fingerprint = '';

    expect(computeScenarioFingerprint(scenarioPackage)).toBe(sha256CanonicalJson(deleteInput));
    expect(computeScenarioFingerprint(scenarioPackage)).not.toBe(sha256CanonicalJson(blankInput));
  });

  it('generates and activates a deterministic 二手电脑回收 runtime v2 release', async () => {
    const result = await generateOfflineStaticRuntimePackage({
      topic: '二手电脑回收项目演示',
      businessDescription: '突出回收评估、检测、报价、入库和环保流转。',
      targetRoot,
      activate: true,
      projectCount: 2,
    });

    expect(result).toMatchObject({
      ok: true,
      data: {
        phase: 'activated',
        packageFormat: 'v2',
        topicKey: expect.any(String),
        domcRegistryFingerprint: expect.stringMatching(/^[a-f0-9]{64}$/),
        adapterVersions: { 'project-simulation': '1.0.0' },
        moduleTrace: expect.arrayContaining([
          expect.objectContaining({ moduleId: 'project', status: 'generate' }),
          expect.objectContaining({ moduleId: 'simulation', status: 'generate' }),
          expect.objectContaining({ moduleId: 'auth', status: 'copy' }),
          expect.objectContaining({ moduleId: 'system', status: 'copy' }),
        ]),
        activePointerPath: 'demo-scenarios/active.pointer.json',
        manifestPath: expect.stringContaining('demo-scenarios/releases/'),
      },
    });
    const activePointer = JSON.parse(
      await fs.readFile(path.join(targetRoot, 'demo-scenarios', 'active.pointer.json'), 'utf8')
    ) as RuntimePackagePointer;
    await expect(
      fs.readFile(path.join(targetRoot, 'demo-scenarios', 'releases', activePointer.releaseId, 'slices', 'project.projects.json'), 'utf8')
    ).resolves.toContain('二手电脑回收项目演示');
    await expect(fs.readFile(path.join(targetRoot, 'demo-scenarios', 'active.json'), 'utf8')).resolves.toContain(
      'legacy'
    );
    const manifest = JSON.parse(
      await fs.readFile(path.join(targetRoot, 'demo-scenarios', 'releases', activePointer.releaseId, 'manifest.json'), 'utf8')
    ) as RuntimePackageV2Manifest;
    const provenance = JSON.parse(
      await fs.readFile(path.join(targetRoot, 'demo-scenarios', 'releases', activePointer.releaseId, 'provenance.json'), 'utf8')
    ) as Record<string, unknown>;
    expect(manifest).toMatchObject({
      domcRegistryFingerprint: result.data?.domcRegistryFingerprint,
      adapterVersions: { 'project-simulation': '1.0.0' },
    });
    expect(manifest.descriptors).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          kind: 'slice',
          sourcePath: 'auth.accounts',
          materializationReason: 'copied-default',
        }),
        expect.objectContaining({
          kind: 'slice',
          sourcePath: 'system.menus',
          materializationReason: 'copied-default',
        }),
        expect.objectContaining({
          kind: 'slice',
          sourcePath: 'project.projects',
          materializationReason: 'semantic-generated',
        }),
        expect.objectContaining({
          kind: 'slice',
          sourcePath: 'simulation.sessions',
          materializationReason: 'semantic-generated',
        }),
      ])
    );
    expect(provenance).toMatchObject({
      domcRegistryFingerprint: result.data?.domcRegistryFingerprint,
      adapterVersions: { 'project-simulation': '1.0.0' },
    });
    expect(provenance.materials).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ kind: 'domc-registry' }),
        expect.objectContaining({ kind: 'domc-module-contract' }),
        expect.objectContaining({ kind: 'generator-adapter' }),
      ])
    );
  });

  it('returns structured DOMC blockers for all-module and unknown-module requests', async () => {
    const allModules = await generateOfflineStaticRuntimePackage({
      topic: '全模块整站演示',
      businessDescription: '希望所有业务菜单都生成最终数据。',
      targetRoot,
      activate: false,
    });
    const unknownModule = await generateOfflineStaticRuntimePackage({
      topic: '客户管理演示',
      targetRoot,
      activate: false,
      requestedModules: ['customer'],
    });

    expect(allModules).toMatchObject({
      ok: false,
      errors: expect.arrayContaining([
        expect.objectContaining({
          code: 'domc_all_modules_request_blocked',
          gate: 'module-blocker',
          missingArtifacts: expect.arrayContaining(['generator adapter']),
          nextActions: expect.any(Array),
        }),
      ]),
    });
    expect(unknownModule).toMatchObject({
      ok: false,
      errors: expect.arrayContaining([
        expect.objectContaining({
          code: 'domc_module_missing',
          gate: 'module-blocker',
          missingArtifacts: expect.arrayContaining([
            'ruoyi-fastapi-frontend/src/demo/domc/modules/customer.domc.ts',
            'tools/demo-offline-mcp/src/adapters/customer/adapter.ts',
          ]),
          nextActions: expect.any(Array),
        }),
      ]),
    });
  });

  it('writes semantic reports and keeps repeated staging stable for identical input', async () => {
    const input = {
      topic: '无人机巡检任务管理',
      businessDescription: '突出航线排程、热成像缺陷复核和空域审批。',
      targetRoot,
      activate: false,
      projectCount: 4,
    };
    const firstResult = await generateOfflineStaticRuntimePackage(input);
    const secondResult = await generateOfflineStaticRuntimePackage(input);

    expect(firstResult).toMatchObject({
      ok: true,
      data: {
        phase: 'staged',
        semanticQualitySummary: {
          errorCount: 0,
        },
        semanticReportPath: expect.stringContaining('semantic-report.json'),
      },
    });
    expect(firstResult.data?.releaseId).toBe(secondResult.data?.releaseId);

    const releaseId = firstResult.data!.releaseId!;
    const projectSlice = await fs.readFile(
      path.join(targetRoot, 'demo-scenarios', 'releases', '.staging', releaseId, 'slices', 'project.projects.json'),
      'utf8'
    );
    const report = JSON.parse(
      await fs.readFile(
        path.join(targetRoot, 'demo-scenarios', 'releases', '.staging', releaseId, 'semantic-report.json'),
        'utf8'
      )
    ) as Record<string, unknown>;

    expect(projectSlice).toContain('巡检');
    expect(report).toMatchObject({
      summary: {
        errorCount: 0,
      },
      blueprintSummary: {
        domainObjectCount: expect.any(Number),
      },
    });
  });

  it('blocks semantic errors before staging and allows warning-only activation', async () => {
    const semanticError = createSemanticIssue({
      gate: 'diversity',
      path: 'draft.projects',
      code: 'forced_semantic_error',
      severity: 'error',
      actual: 'unit-test',
      expected: 'No semantic errors',
      fixHint: 'Repair the Blueprint-level semantic sources before writing the v2 release.',
    });
    const errorResult = await generateOfflineStaticRuntimePackage({
      topic: '无人机巡检任务管理',
      businessDescription: '突出航线排程、热成像缺陷复核和空域审批。',
      targetRoot,
      activate: false,
      projectCount: 4,
      semanticIssueOverrides: [semanticError],
    });

    expect(errorResult).toMatchObject({
      ok: false,
      data: {
        phase: 'validation_failed',
        semanticReportPath: 'demo-scenarios/semantic-failed-report.json',
      },
      errors: expect.arrayContaining([expect.objectContaining({ code: 'forced_semantic_error' })]),
    });
    await expect(fs.access(path.join(targetRoot, 'demo-scenarios', 'releases', '.staging'))).rejects.toBeTruthy();

    const semanticWarning = createSemanticIssue({
      gate: 'diversity',
      path: 'draft.projects.stage',
      code: 'forced_semantic_warning',
      severity: 'warning',
      actual: 'unit-test',
      expected: 'Reviewable warning',
      fixHint: 'Review the Blueprint stage distribution before customer delivery.',
    });
    const warningResult = await generateOfflineStaticRuntimePackage({
      topic: '制造设备巡检管理',
      businessDescription: '突出设备台账、巡检计划和异常复核。',
      targetRoot,
      activate: true,
      projectCount: 4,
      semanticIssueOverrides: [semanticWarning],
    });

    expect(warningResult).toMatchObject({
      ok: true,
      errors: expect.arrayContaining([expect.objectContaining({ code: 'forced_semantic_warning' })]),
      data: {
        phase: 'activated',
        semanticReportPath: expect.stringContaining('semantic-report.json'),
      },
    });
    await expect(
      fs.readFile(path.join(targetRoot, warningResult.data!.semanticReportPath!), 'utf8')
    ).resolves.toContain('forced_semantic_warning');
  });
});
