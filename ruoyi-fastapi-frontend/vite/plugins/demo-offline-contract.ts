import fs from 'node:fs/promises';
import path from 'node:path';
import type { Plugin, ResolvedConfig, ViteDevServer } from 'vite';

import { defaultDemoScenario } from '../../src/demo/scenarios/default';
import { demoScenarioJsonSchema } from '../../src/demo/scenarios/scenario-json-schema';
import { DEMO_OFFLINE_GENERATOR_ADAPTER_VERSION } from '../../src/demo/scenarios/contract';
import { createDemoOfflineContractManifest } from '../../src/demo/scenarios/fingerprint';
import { createDemoDomcRegistry, demoDomcRegistryJsonSchema } from '../../src/demo/domc';
import {
  createRuntimePackageV2Release,
  RUNTIME_PACKAGE_V2_ACTIVE_POINTER_PATH,
  RUNTIME_PACKAGE_V2_BUNDLE_DEFAULT_RELEASE_ID,
} from '../../src/demo/scenarios/release-store';

export interface DemoOfflineContractPluginOptions {
  enabled: boolean;
}

interface DemoOfflineStaticAsset {
  path: string;
  value: unknown;
}

async function writeJson(filePath: string, value: unknown): Promise<void> {
  await fs.mkdir(path.dirname(filePath), { recursive: true });
  await fs.writeFile(filePath, `${JSON.stringify(value, null, 2)}\n`, 'utf8');
}

async function removeLegacyRuntimePackageFiles(scenariosDir: string): Promise<void> {
  await Promise.all(
    ['active.json', 'previous.json', 'active.meta.json'].map((fileName) =>
      fs.rm(path.join(scenariosDir, fileName), { force: true }),
    ),
  );
}

async function listFiles(root: string): Promise<string[]> {
  const entries = await fs.readdir(root, { withFileTypes: true }).catch(() => []);
  const nested = await Promise.all(
    entries.map(async (entry) => {
      const entryPath = path.join(root, entry.name);
      if (entry.isDirectory()) {
        return listFiles(entryPath);
      }
      return [entryPath];
    }),
  );

  return nested.flat();
}

async function assertHardCutV1Absence(scenariosDir: string): Promise<void> {
  const forbidden = new Set(['active.json', 'previous.json', 'active.meta.json']);
  const files = await listFiles(scenariosDir);
  const residue = files
    .filter((filePath) => forbidden.has(path.basename(filePath)))
    .map((filePath) => path.relative(scenariosDir, filePath).split(path.sep).join('/'));

  if (residue.length) {
    throw new Error(
      `demo-offline runtime package hard-cut v2 check failed; v1 files remain: ${residue.join(', ')}.`,
    );
  }
}

async function createDemoOfflineStaticAssets(): Promise<DemoOfflineStaticAsset[]> {
  const generatedAt = new Date().toISOString();
  const domcRegistry = await createDemoDomcRegistry(generatedAt);
  const contract = await createDemoOfflineContractManifest(generatedAt, {
    domcRegistry,
  });
  const release = await createRuntimePackageV2Release({
    releaseId: RUNTIME_PACKAGE_V2_BUNDLE_DEFAULT_RELEASE_ID,
    scenarioPackage: defaultDemoScenario,
    contractFingerprint: contract.contractFingerprint,
    generatorVersion: DEMO_OFFLINE_GENERATOR_ADAPTER_VERSION,
    generatedAt,
    activatedAt: generatedAt,
    topicKey: 'default',
    topicSummary: defaultDemoScenario.scenario.name,
    seed: defaultDemoScenario.scenario.seed ?? 'ruoyi-demo-offline-default',
    materializationReason: 'copied-default',
    domcRegistryFingerprint: domcRegistry.domcFingerprint,
    moduleContractFingerprints: contract.moduleContractFingerprints,
    adapterVersions: Object.fromEntries(
      contract.adapterReferences.map((reference) => [
        reference.adapterId,
        reference.adapterVersionRange,
      ]),
    ),
    adapterCapabilitySummary: contract.adapterReferences.map((reference) => ({
      moduleId: reference.moduleId,
      adapterId: reference.adapterId,
      adapterVersion: reference.adapterVersionRange,
      outputSourcePaths: reference.outputSourcePaths,
    })),
  });

  return [
    { path: 'demo-contract/contract.json', value: contract },
    { path: 'demo-contract/domc.registry.json', value: domcRegistry },
    {
      path: 'demo-contract/domc.registry.schema.json',
      value: demoDomcRegistryJsonSchema,
    },
    {
      path: 'demo-contract/scenario.schema.json',
      value: demoScenarioJsonSchema,
    },
    { path: 'demo-contract/default-scenario.json', value: defaultDemoScenario },
    ...release.slices.map((slice) => ({
      path: `demo-scenarios/releases/${RUNTIME_PACKAGE_V2_BUNDLE_DEFAULT_RELEASE_ID}/${slice.descriptor.path}`,
      value: slice.data,
    })),
    {
      path: `demo-scenarios/releases/${RUNTIME_PACKAGE_V2_BUNDLE_DEFAULT_RELEASE_ID}/provenance.json`,
      value: release.provenance,
    },
    {
      path: `demo-scenarios/releases/${RUNTIME_PACKAGE_V2_BUNDLE_DEFAULT_RELEASE_ID}/manifest.json`,
      value: release.manifest,
    },
    { path: RUNTIME_PACKAGE_V2_ACTIVE_POINTER_PATH, value: release.pointer },
  ];
}

function toAssetMap(assets: DemoOfflineStaticAsset[]): Map<string, string> {
  return new Map(assets.map((asset) => [asset.path, `${JSON.stringify(asset.value, null, 2)}\n`]));
}

function normalizeRequestAssetPath(requestUrl?: string): string | undefined {
  if (!requestUrl) {
    return undefined;
  }

  const pathname = new URL(requestUrl, 'http://demo-offline.local').pathname;
  return decodeURIComponent(pathname).replace(/^\/+/, '');
}

function isDemoOfflineStaticPath(assetPath: string): boolean {
  return assetPath.startsWith('demo-contract/') || assetPath.startsWith('demo-scenarios/');
}

function configureDemoOfflineDevServer(server: ViteDevServer): void {
  let assetsPromise: Promise<Map<string, string>> | undefined;

  const getAssets = () => {
    assetsPromise ??= createDemoOfflineStaticAssets().then(toAssetMap);
    return assetsPromise;
  };

  server.middlewares.use(async (request, response, next) => {
    const assetPath = normalizeRequestAssetPath(request.url);
    if (!assetPath || !isDemoOfflineStaticPath(assetPath)) {
      next();
      return;
    }

    if (request.method !== 'GET' && request.method !== 'HEAD') {
      next();
      return;
    }

    let body: string | undefined;
    try {
      const assets = await getAssets();
      body = assets.get(assetPath);
    } catch (error) {
      next(error);
      return;
    }

    response.setHeader('Content-Type', 'application/json; charset=utf-8');
    response.setHeader('Cache-Control', 'no-store');

    if (body === undefined) {
      response.statusCode = 404;
      response.end(
        JSON.stringify({
          code: 'DEMO_OFFLINE_ASSET_NOT_FOUND',
          message: `${assetPath} is not generated by demo-offline dev middleware.`,
        }),
      );
      return;
    }

    response.statusCode = 200;
    response.end(request.method === 'HEAD' ? undefined : body);
  });
}

export default function createDemoOfflineContractPlugin({
  enabled,
}: DemoOfflineContractPluginOptions): Plugin {
  let config: ResolvedConfig;

  return {
    name: 'demo-offline-contract-export',
    configResolved(resolvedConfig) {
      config = resolvedConfig;
    },
    configureServer(server) {
      if (!enabled) {
        return;
      }

      configureDemoOfflineDevServer(server);
    },
    async closeBundle() {
      if (!enabled || config.command !== 'build') {
        return;
      }

      const outDir = path.resolve(config.root, config.build.outDir);
      const scenariosDir = path.join(outDir, 'demo-scenarios');
      const assets = await createDemoOfflineStaticAssets();

      await removeLegacyRuntimePackageFiles(scenariosDir);
      await Promise.all(
        assets.map((asset) => writeJson(path.join(outDir, asset.path), asset.value)),
      );
      await assertHardCutV1Absence(scenariosDir);
    },
  };
}
