import fs from 'node:fs/promises';
import path from 'node:path';

import { ProjectPaths } from './project-paths.js';
import type { DemoOfflineContext, DemoOfflineContextDomcModule, ToolEnvelope } from './types.js';
import { okEnvelope } from './types.js';

export interface ScanContextOptions {
  includeGenerated?: boolean;
  includeCandidates?: boolean;
}

const DEFAULT_SCRIPT_VALUE = '';

const HANDLER_SOURCES = [
  { name: 'auth', file: 'auth.ts' },
  { name: 'system', file: 'system.ts' },
  { name: 'system-admin', file: 'system-admin.ts' },
  { name: 'project', file: 'project.ts' },
  { name: 'simulation', file: 'simulation.ts' },
] as const;

function normalizeSlashes(value: string): string {
  return value.split(path.sep).join('/');
}

async function readText(filePath: string): Promise<string> {
  return fs.readFile(filePath, 'utf8');
}

async function listFiles(directory: string): Promise<string[]> {
  try {
    const entries = await fs.readdir(directory, { withFileTypes: true });
    return entries
      .filter((entry) => entry.isFile())
      .map((entry) => path.join(directory, entry.name))
      .sort();
  } catch {
    return [];
  }
}

function extractScenarioIdentity(source: string): { id: string; name: string } | undefined {
  const scenarioBlock = source.match(/scenario\s*:\s*\{[\s\S]*?\n\s*\}/)?.[0] ?? source;
  const id = scenarioBlock.match(/\bid\s*:\s*['"`]([^'"`]+)['"`]/)?.[1];
  const name = scenarioBlock.match(/\bname\s*:\s*['"`]([^'"`]+)['"`]/)?.[1];

  if (!id || !name) {
    return undefined;
  }

  return { id, name };
}

async function scanScenarioFiles(
  paths: ProjectPaths,
  kind: 'generated' | 'candidate',
  directory: string
): Promise<DemoOfflineContext['scenarios']> {
  const files = (await listFiles(directory)).filter((filePath) => {
    const basename = path.basename(filePath);
    if (basename === 'index.ts' || basename.endsWith('.test.ts')) return false;
    return kind === 'candidate' ? basename.endsWith('.candidate.ts') : basename.endsWith('.ts');
  });

  const scenarios: DemoOfflineContext['scenarios'] = [];

  for (const filePath of files) {
    const identity = extractScenarioIdentity(await readText(filePath));

    if (identity) {
      scenarios.push({
        ...identity,
        kind,
        path: normalizeSlashes(paths.relativeToRepo(filePath)),
      });
    }
  }

  return scenarios;
}

async function readPackageScripts(frontendRoot: string): Promise<DemoOfflineContext['scripts']> {
  const packageJson = JSON.parse(await readText(path.join(frontendRoot, 'package.json'))) as {
    scripts?: Record<string, string>;
  };
  const scripts = packageJson.scripts ?? {};

  return {
    buildDemoOffline: scripts['build:demo-offline'] ?? DEFAULT_SCRIPT_VALUE,
    previewDemoOffline: scripts['preview:demo-offline'] ?? DEFAULT_SCRIPT_VALUE,
    typeCheck: scripts['type-check'] ?? DEFAULT_SCRIPT_VALUE,
    testRun: scripts['test:run'] ?? DEFAULT_SCRIPT_VALUE,
  };
}

async function scanHandlers(paths: ProjectPaths): Promise<DemoOfflineContext['handlers']> {
  const handlersRoot = path.join(paths.demoRoot, 'handlers');

  return Promise.all(
    HANDLER_SOURCES.map(async (handler) => {
      const source = path.join(handlersRoot, handler.file);
      return {
        name: handler.name,
        source: normalizeSlashes(paths.relativeToRepo(source)),
        covered: await fs
          .access(source)
          .then(() => true)
          .catch(() => false),
      };
    })
  );
}

function extractStringArray(source: string, constName: string): string[] {
  const match = source.match(new RegExp(`const\\s+${constName}\\s*=\\s*\\[([\\s\\S]*?)\\]\\s*as\\s+const`));
  if (!match) return [];
  return [...(match[1] ?? '').matchAll(/['"`]([^'"`]+)['"`]/g)]
    .map((item) => item[1] ?? '')
    .filter(Boolean);
}

async function scanDomcModules(paths: ProjectPaths): Promise<DemoOfflineContextDomcModule[]> {
  const modulesRoot = path.join(paths.demoRoot, 'domc', 'modules');
  const moduleFiles = (await listFiles(modulesRoot)).filter((filePath) => filePath.endsWith('.domc.ts'));

  return Promise.all(
    moduleFiles.map(async (filePath) => {
      const source = await readText(filePath);
      const moduleId = source.match(/\bmoduleId\s*:\s*['"`]([^'"`]+)['"`]/)?.[1] ?? path.basename(filePath, '.domc.ts');
      const capability =
        (source.match(/\bcapability\s*:\s*['"`](generatable|copyOnly|unsupported)['"`]/)?.[1] as
          | DemoOfflineContextDomcModule['capability']
          | undefined) ?? 'unsupported';
      const lifecycle =
        (source.match(/\blifecycle\s*:\s*['"`](active|deprecated|experimental)['"`]/)?.[1] as
          | DemoOfflineContextDomcModule['lifecycle']
          | undefined) ?? 'experimental';
      const adapterId = source.match(/\badapterId\s*:\s*['"`]([^'"`]+)['"`]/)?.[1];
      const sourcePaths = extractStringArray(source, 'sourcePaths');
      const evidence = [normalizeSlashes(paths.relativeToRepo(filePath))];

      return {
        moduleId,
        capability,
        lifecycle,
        sourcePaths,
        ...(adapterId ? { adapterId } : {}),
        evidence,
      };
    })
  );
}

export async function scanDemoOfflineContext(
  paths: ProjectPaths,
  options: ScanContextOptions = {}
): Promise<ToolEnvelope<DemoOfflineContext>> {
  const includeGenerated = options.includeGenerated ?? true;
  const includeCandidates = options.includeCandidates ?? true;
  const schemaPath = path.join(paths.demoRoot, 'scenarios', 'schema.ts');
  const defaultPath = path.join(paths.demoRoot, 'scenarios', 'default.ts');
  const scenarioIndexPath = path.join(paths.demoRoot, 'scenarios', 'index.ts');
  const repositoryPath = path.join(paths.demoRoot, 'repositories', 'scenario.ts');
  const httpHandlersPath = path.join(paths.demoRoot, 'handlers', 'http.ts');
  const defaultIdentity = extractScenarioIdentity(await readText(defaultPath));
  const scenarios: DemoOfflineContext['scenarios'] = [];

  if (defaultIdentity) {
    scenarios.push({
      ...defaultIdentity,
      kind: 'default',
      path: normalizeSlashes(paths.relativeToRepo(defaultPath)),
    });
  }

  if (includeGenerated) {
    scenarios.push(...(await scanScenarioFiles(paths, 'generated', paths.generatedRoot)));
  }

  if (includeCandidates) {
    scenarios.push(...(await scanScenarioFiles(paths, 'candidate', paths.candidateRoot)));
  }

  const scripts = await readPackageScripts(paths.frontendRoot);
  const handlers = await scanHandlers(paths);
  const domcModules = await scanDomcModules(paths);
  const httpHandlers = await readText(httpHandlersPath);
  const scenarioIndex = await readText(scenarioIndexPath);
  const repository = await readText(repositoryPath);
  const schema = await readText(schemaPath);
  const safeSlices = domcModules
    .filter((moduleContract) => moduleContract.capability === 'generatable' && moduleContract.lifecycle === 'active')
    .map((moduleContract) => moduleContract.moduleId);
  const copiedSlices = domcModules
    .filter((moduleContract) => moduleContract.capability === 'copyOnly' && moduleContract.lifecycle === 'active')
    .map((moduleContract) => moduleContract.moduleId);

  const context: DemoOfflineContext = {
    repoRoot: paths.repoRoot,
    frontendRoot: paths.frontendRoot,
    generatedRoot: paths.generatedRoot,
    schemaVersion: 1,
    safeSlices,
    copiedSlices,
    domcModules,
    handlers,
    scenarios,
    scripts,
    risks: [
      {
        code: 'domc_scan_limited_to_demo_root',
        message:
          'Source-generated scanning uses DOMC module declarations under ruoyi-fastapi-frontend/src/demo/domc/** and demo-related frontend scripts.',
        source: 'docs/specs/demo-offline-domc-registry-and-generator-adapters/requirements.md',
      },
      {
        code: 'unsupported_slices_not_generated',
        message:
          'Modules without active DOMC generatable capability and compatible adapter evidence are unsafe to generate.',
        source: normalizeSlashes(paths.relativeToRepo(schemaPath)),
      },
      ...(httpHandlers.includes('DEMO_API_NOT_IMPLEMENTED')
        ? [
            {
              code: 'demo_api_not_implemented_catch_all',
              message: 'Uncovered demo API requests continue to return DEMO_API_NOT_IMPLEMENTED.',
              source: normalizeSlashes(paths.relativeToRepo(httpHandlersPath)),
            },
          ]
        : []),
      ...(!scenarioIndex.includes('generatedScenarioRegistry') || !repository.includes('ensureScenario')
        ? [
            {
              code: 'demo_runtime_chain_incomplete',
              message: 'Scenario registry or ScenarioRepository evidence was not found during scan.',
              source: normalizeSlashes(paths.relativeToRepo(scenarioIndexPath)),
            },
          ]
        : []),
    ],
  };

  if (!schema.includes('DemoScenarioPackage')) {
    context.risks.push({
      code: 'schema_contract_not_detected',
      message: 'DemoScenarioPackage contract was not detected in schema.ts.',
      source: normalizeSlashes(paths.relativeToRepo(schemaPath)),
    });
  }

  return okEnvelope('Scanned demo-offline context for project and simulation generation.', context, {
    artifacts: [
      { kind: 'file', label: 'Demo scenario schema', path: normalizeSlashes(paths.relativeToRepo(schemaPath)) },
      { kind: 'file', label: 'Default demo scenario', path: normalizeSlashes(paths.relativeToRepo(defaultPath)) },
      {
        kind: 'file',
        label: 'Scenario repository import chain',
        path: normalizeSlashes(paths.relativeToRepo(repositoryPath)),
      },
      {
        kind: 'file',
        label: 'Demo handler coverage',
        path: normalizeSlashes(paths.relativeToRepo(httpHandlersPath)),
      },
    ],
    nextActions: ['Create a generation plan from an industry brief before drafting data.'],
  });
}

export function formatDemoOfflineContext(context: DemoOfflineContext): string {
  const scenarios = context.scenarios
    .map((scenario) => `- ${scenario.kind}: ${scenario.id} (${scenario.name})`)
    .join('\n');
  const handlers = context.handlers
    .map((handler) => `- ${handler.name}: ${handler.covered ? 'covered' : 'missing'} (${handler.source})`)
    .join('\n');

  return [
    '# Demo Offline Context',
    '',
    `Safe slices: ${context.safeSlices.join(', ')}`,
    `Copied slices: ${context.copiedSlices.join(', ')}`,
    '',
    '## Scenarios',
    scenarios || '- none',
    '',
    '## Handlers',
    handlers || '- none',
    '',
    '## Scripts',
    `- build:demo-offline: ${context.scripts.buildDemoOffline}`,
    `- preview:demo-offline: ${context.scripts.previewDemoOffline}`,
    `- type-check: ${context.scripts.typeCheck}`,
    `- test:run: ${context.scripts.testRun}`,
  ].join('\n');
}
