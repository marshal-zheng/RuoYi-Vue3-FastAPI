import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { randomBytes } from 'node:crypto';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import {
  createRuntimePackageV2Release,
  RUNTIME_PACKAGE_V2_ACTIVE_POINTER_PATH,
  RUNTIME_PACKAGE_V2_PREVIOUS_POINTER_PATH,
  RUNTIME_PACKAGE_V2_TIMELINE_PATH,
} from '../src/demo/scenarios/release-store.ts';
import type { DemoOfflineContractManifest } from '../src/demo/scenarios/contract.ts';
import { composeSmartMarketOperationsDemoScenario } from '../src/demo/scenarios/generated/smart-market-operations-demo.ts';

const RELEASE_ID = 'smart-market-ops-demo-6930cae15f2f';

async function jsonRead<T>(filePath: string): Promise<T> {
  const raw = await readFile(filePath, 'utf8');
  return JSON.parse(raw) as T;
}

function eventIdHex(): string {
  return randomBytes(16).toString('hex');
}

async function main() {
  const __dirname = path.dirname(fileURLToPath(import.meta.url));
  const projectRoot = path.resolve(__dirname, '..');
  const outDirArg = process.argv[2]?.trim();
  const outDir = path.resolve(projectRoot, outDirArg ?? 'dist-demo-offline');

  const contractPath = path.join(outDir, 'demo-contract', 'contract.json');
  const contract = await jsonRead<DemoOfflineContractManifest>(contractPath);

  const fp =
    typeof contract.contractFingerprint === 'string' ? contract.contractFingerprint : '';
  if (!/^[a-f0-9]{64}$/.test(fp)) {
    throw new Error(`${contractPath} contractFingerprint invalid.`);
  }

  const domcFp =
    typeof contract.domcRegistryFingerprint === 'string' ? contract.domcRegistryFingerprint : '';
  const moduleFp = contract.moduleContractFingerprints;
  if (
    typeof moduleFp?.auth !== 'string' ||
    typeof moduleFp?.system !== 'string' ||
    typeof moduleFp?.project !== 'string' ||
    typeof moduleFp?.simulation !== 'string'
  ) {
    throw new Error(`${contractPath} moduleContractFingerprints incomplete.`);
  }

  const generatedAt = new Date().toISOString();
  const scenarioPackage = composeSmartMarketOperationsDemoScenario(generatedAt);

  const release = await createRuntimePackageV2Release({
    releaseId: RELEASE_ID,
    scenarioPackage,
    contractFingerprint: fp,
    generatorVersion: 'demo-offline-generator-p0.2-script-activate',
    generatedAt,
    activatedAt: generatedAt,
    seed: scenarioPackage.scenario.seed ?? RELEASE_ID,
    topicKey: scenarioPackage.scenario.id,
    topicSummary: scenarioPackage.scenario.name,
    materializationReason: 'semantic-generated',
    domcRegistryFingerprint: domcFp,
    moduleContractFingerprints: {
      auth: moduleFp.auth,
      system: moduleFp.system,
      project: moduleFp.project,
      simulation: moduleFp.simulation,
    },
    adapterVersions: {
      'copy-only-default-scenario': 'default-scenario',
      'project-simulation': '1.0.0',
    },
    adapterCapabilitySummary:
      contract.adapterReferences?.map((r) => ({
        moduleId: r.moduleId as 'auth' | 'system' | 'project' | 'simulation',
        adapterId: r.adapterId,
        adapterVersion: r.adapterVersionRange,
        outputSourcePaths: [...r.outputSourcePaths],
      })) ?? [],
    materializationReasonsBySourcePath: Object.fromEntries(
      [
        'auth.accounts',
        'auth.roles',
        'auth.permissions',
        'system.menus',
        'system.dictTypes',
        'system.dicts',
        'system.departments',
        'system.posts',
        'system.users',
      ].map((sourcePath) => [sourcePath, 'copied-default'] as const)
    ),
  });

  const scenariosRoot = path.join(outDir, 'demo-scenarios');
  const releaseRoot = path.join(scenariosRoot, 'releases', RELEASE_ID);

  for (const slice of release.slices) {
    const abs = path.join(releaseRoot, slice.descriptor.path);
    await mkdir(path.dirname(abs), { recursive: true });
    await writeFile(abs, `${JSON.stringify(slice.data, null, 2)}\n`, 'utf8');
  }

  await writeFile(
    path.join(releaseRoot, 'manifest.json'),
    `${JSON.stringify(release.manifest, null, 2)}\n`,
    'utf8'
  );
  await writeFile(
    path.join(releaseRoot, 'provenance.json'),
    `${JSON.stringify(release.provenance, null, 2)}\n`,
    'utf8'
  );

  const activePointerPath = path.join(outDir, RUNTIME_PACKAGE_V2_ACTIVE_POINTER_PATH);
  const previousPointerPath = path.join(outDir, RUNTIME_PACKAGE_V2_PREVIOUS_POINTER_PATH);

  try {
    const prior = await readFile(activePointerPath, 'utf8');
    await writeFile(previousPointerPath, `${JSON.stringify(JSON.parse(prior), null, 2)}\n`, 'utf8');
  } catch {
    // ignore if missing
  }

  await writeFile(activePointerPath, `${JSON.stringify(release.pointer, null, 2)}\n`, 'utf8');

  const timelinePath = path.join(outDir, RUNTIME_PACKAGE_V2_TIMELINE_PATH);
  let timeline: unknown[] = [];
  try {
    timeline = JSON.parse(await readFile(timelinePath, 'utf8'));
  } catch {
    timeline = [];
  }
  const sha256 = release.manifest.rootSha256;
  const summaries = ['staged', 'verified', 'activated'] as const;
  const nowIso = generatedAt;
  for (const s of summaries) {
    timeline.push({
      eventId: eventIdHex(),
      time: nowIso,
      eventType: s,
      releaseId: RELEASE_ID,
      actor: 'manual',
      manifestSha256: sha256,
      result: 'success',
      summary: `${s} v2 runtime release ${RELEASE_ID}.`,
    });
  }
  await writeFile(timelinePath, `${JSON.stringify(timeline, null, 2)}\n`, 'utf8');

  // eslint-disable-next-line no-console
  console.info(
    `Activated "${scenarioPackage.scenario.name}" (${RELEASE_ID})\nmanifest ${sha256}\noutDir: ${outDir}`
  );
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
