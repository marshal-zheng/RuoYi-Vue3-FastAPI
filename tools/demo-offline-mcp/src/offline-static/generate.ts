import path from 'node:path';

import { ToolError, createIssue } from '../errors.js';
import { computeScenarioFingerprint } from '../hash.js';
import { resolveDemoGeneratorAdapters, validateAdapterMaterializations } from '../adapters/registry.js';
import { assembleDemoScenarioPackage } from './assembler.js';
import type {
  DemoDomcRegistry,
  DemoOfflineBlockerIssue,
  GenerationPlan,
  IndustryDataDraft,
  OfflineStaticActivationResult,
  ToolEnvelope,
} from '../types.js';
import { errorEnvelope } from '../types.js';
import {
  compileBlueprintToIndustryDraft,
  createSemanticQualityReport,
  generateDeterministicBusinessBlueprint,
  validateBusinessBlueprint,
  validateDiversity,
  validateSemanticCoverage,
  type SemanticQualityIssue,
  type SemanticQualityReport,
} from '../semantic/index.js';
import { computeContractFingerprint, readOfflineStaticContract } from './contract.js';
import { validateRuntimeInvariants } from './invariants.js';
import { resolveOfflineStaticTargetPaths } from './paths.js';
import {
  summarizeRuntimeValidation,
  validateRuntimeMeta,
  validateRuntimeScenarioPackage,
} from './scenario-validation.js';
import {
  activateRuntimePackage,
  createRuntimeScenarioMeta,
  writeSemanticFailureReport,
  writeRuntimeCandidatePackage,
} from './writer.js';
import { createStableSeed, normalizeTopicKey } from './topic.js';

export interface GenerateOfflineStaticRuntimePackageInput {
  topic: string;
  businessDescription?: string;
  scenarioId?: string;
  scenarioName?: string;
  projectCount?: number;
  targetRoot: string;
  activate?: boolean;
  semanticIssueOverrides?: SemanticQualityIssue[];
  requestedModules?: readonly string[] | 'default' | 'all';
}

export const GENERATOR_VERSION = 'demo-offline-generator-p0.2-semantic-blueprint';

function normalizeCount(value: number | undefined, fallback: number): number {
  if (typeof value !== 'number' || !Number.isFinite(value)) return fallback;
  return Math.max(1, Math.min(8, Math.floor(value)));
}

export function createOfflineStaticPlan(input: {
  topic: string;
  businessDescription?: string;
  topicKey: string;
  scenarioId: string;
  scenarioName: string;
  projectCount: number;
  domcRegistry?: DemoDomcRegistry;
  requestedModules?: readonly string[] | 'default' | 'all';
}): GenerationPlan {
  const wantsAll =
    input.requestedModules === 'all' ||
    /全亮|全量|全部|所有|全模块|整站/.test(`${input.topic}\n${input.businessDescription ?? ''}`);
  const defaultPlan: GenerationPlan = {
    scenarioId: input.scenarioId,
    scenarioName: input.scenarioName,
    industry: input.topic,
    brief: input.businessDescription || input.topic,
    scope: ['project', 'simulation'],
    copiedSlices: ['auth', 'system'],
    targetCounts: {
      projects: input.projectCount,
      versionsPerProject: 1,
      sessionsPerProject: 1,
    },
    trace: [
      {
        slice: 'project',
        status: 'generate',
        evidence: ['demo-contract/contract.json', 'project module contract'],
      },
      {
        slice: 'simulation',
        status: 'generate',
        evidence: ['demo-contract/contract.json', 'simulation module contract'],
      },
      {
        slice: 'auth',
        status: 'copy',
        evidence: ['demo-contract/default-scenario.json'],
      },
      {
        slice: 'system',
        status: 'copy',
        evidence: ['demo-contract/default-scenario.json'],
      },
    ],
  };

  if (!input.domcRegistry) {
    return defaultPlan;
  }

  const requested =
    input.requestedModules === 'all'
      ? input.domcRegistry.modules.map((moduleContract) => moduleContract.moduleId)
      : input.requestedModules && input.requestedModules !== 'default'
        ? [...input.requestedModules]
        : ['project', 'simulation', 'auth', 'system'];
  if (requested.includes('simulation') && !requested.includes('project')) {
    requested.unshift('project');
  }
  const moduleTrace: NonNullable<GenerationPlan['moduleTrace']> = [];
  const trace: GenerationPlan['trace'] = [];
  const scope: GenerationPlan['scope'] = [];
  const copiedSlices: GenerationPlan['copiedSlices'] = [];

  const unknownModules = requested.filter(
    (moduleId) => !input.domcRegistry?.modules.some((moduleContract) => moduleContract.moduleId === moduleId)
  );
  unknownModules.forEach((moduleId) => {
    const blocker = createModuleBlocker({
      moduleId,
      code: 'domc_module_missing',
      actual: moduleId,
      expected: 'Requested module exists in DOMC registry',
      fixHint: 'Add DOMC, IndexedDB mapping, handler coverage, UI journey, invariants, and adapter before generation.',
      missingArtifacts: [
        `ruoyi-fastapi-frontend/src/demo/domc/modules/${moduleId}.domc.ts`,
        `tools/demo-offline-mcp/src/adapters/${moduleId}/adapter.ts`,
      ],
      nextActions: ['Create the module DOMC contract.', 'Implement and register a compatible MCP adapter.'],
    });
    moduleTrace.push({
      moduleId,
      capability: 'unsupported',
      status: 'blocked',
      sourcePaths: [],
      evidence: ['demo-contract/domc.registry.json'],
      blocker,
    });
    trace.push({ slice: moduleId, status: 'blocked', evidence: ['demo-contract/domc.registry.json'], blocker });
  });

  input.domcRegistry.modules
    .filter((moduleContract) => requested.includes(moduleContract.moduleId))
    .forEach((moduleContract) => {
      if (moduleContract.capability === 'generatable') {
        scope.push(moduleContract.moduleId as GenerationPlan['scope'][number]);
        moduleTrace.push({
          moduleId: moduleContract.moduleId,
          capability: moduleContract.capability,
          status: 'generate',
          sourcePaths: moduleContract.sourcePaths,
          adapterId: moduleContract.adapterRef?.adapterId,
          evidence: ['demo-contract/domc.registry.json', ...moduleContract.handlerCoverage.map((handler) => handler.source)],
        });
        trace.push({
          slice: moduleContract.moduleId,
          status: 'generate',
          evidence: ['demo-contract/domc.registry.json', ...moduleContract.handlerCoverage.map((handler) => handler.source)],
        });
        return;
      }

      if (moduleContract.capability === 'copyOnly') {
        copiedSlices.push(moduleContract.moduleId as GenerationPlan['copiedSlices'][number]);
        moduleTrace.push({
          moduleId: moduleContract.moduleId,
          capability: moduleContract.capability,
          status: 'copy',
          sourcePaths: moduleContract.sourcePaths,
          evidence: [moduleContract.copyOnly?.source ?? 'demo-contract/default-scenario.json'],
        });
        trace.push({
          slice: moduleContract.moduleId,
          status: 'copy',
          evidence: [moduleContract.copyOnly?.source ?? 'demo-contract/default-scenario.json'],
        });
        return;
      }

      const blocker = createModuleBlocker({
        moduleId: moduleContract.moduleId,
        code: 'domc_module_unsupported',
        actual: moduleContract.unsupportedReason ?? 'unsupported',
        expected: 'Module is generatable or copyOnly',
        fixHint: 'Complete module DOMC and adapter DoD before generation.',
        missingArtifacts: [`tools/demo-offline-mcp/src/adapters/${moduleContract.moduleId}/adapter.ts`],
        nextActions: ['Implement missing DOMC artifacts or keep the module unsupported.'],
      });
      moduleTrace.push({
        moduleId: moduleContract.moduleId,
        capability: moduleContract.capability,
        status: 'unsupported',
        sourcePaths: moduleContract.sourcePaths,
        evidence: ['demo-contract/domc.registry.json'],
        blocker,
      });
      trace.push({ slice: moduleContract.moduleId, status: 'unsupported', evidence: ['demo-contract/domc.registry.json'], blocker });
    });

  if (wantsAll) {
    const blocker = createModuleBlocker({
      moduleId: 'p0-unsupported-business-modules',
      code: 'domc_all_modules_request_blocked',
      actual: 'all modules requested',
      expected: 'Only DOMC-backed project/simulation generation and auth/system copyOnly are available',
      fixHint: 'Request supported modules or implement DOMC + adapter for each additional business module.',
      missingArtifacts: [
        'DOMC for unregistered business modules',
        'IndexedDB mapping',
        'MSW handler coverage',
        'UI journey',
        'generator adapter',
      ],
      nextActions: ['Implement module Definition of Done before full-site generation.'],
    });
    moduleTrace.push({
      moduleId: 'p0-unsupported-business-modules',
      capability: 'unsupported',
      status: 'blocked',
      sourcePaths: [],
      evidence: ['docs/specs/demo-offline-domc-registry-and-generator-adapters/requirements.md'],
      blocker,
    });
    trace.push({
      slice: 'p0-unsupported-business-modules',
      status: 'blocked',
      evidence: ['demo-contract/domc.registry.json'],
      blocker,
    });
  }

  return {
    ...defaultPlan,
    scope: [...new Set(scope)],
    copiedSlices: [...new Set(copiedSlices)],
    trace,
    moduleTrace,
  };
}

function createModuleBlocker(input: {
  moduleId: string;
  code: string;
  actual?: unknown;
  expected: string;
  fixHint: string;
  missingArtifacts: string[];
  nextActions: string[];
}): DemoOfflineBlockerIssue {
  return {
    path: `domc.modules[${input.moduleId}]`,
    code: input.code,
    severity: 'error',
    actual: input.actual,
    expected: input.expected,
    fixHint: input.fixHint,
    autoRepairable: false,
    gate: 'module-blocker',
    missingArtifacts: input.missingArtifacts,
    nextActions: input.nextActions,
  };
}

export function createDeterministicIndustryDraft(input: {
  topic: string;
  businessDescription?: string;
  topicKey: string;
  scenarioId: string;
  scenarioName: string;
  seed: string;
  projectCount: number;
  contractFingerprint?: string;
  generatorVersion?: string;
}): IndustryDataDraft {
  const blueprint = generateDeterministicBusinessBlueprint({
    topic: input.topic,
    businessDescription: input.businessDescription,
    topicKey: input.topicKey,
    seed: input.seed,
    contractFingerprint: input.contractFingerprint ?? 'source-generated',
    generatorVersion: input.generatorVersion ?? GENERATOR_VERSION,
    projectCount: input.projectCount,
  });

  return compileBlueprintToIndustryDraft({
    blueprint,
    scenarioId: input.scenarioId,
    scenarioName: input.scenarioName,
    projectCount: input.projectCount,
  }).draft;
}

function semanticIssuesForResponse(issues: SemanticQualityIssue[]): SemanticQualityIssue[] | undefined {
  return issues.length ? issues : undefined;
}

function attachSemanticReport(
  envelope: ToolEnvelope<OfflineStaticActivationResult>,
  report: SemanticQualityReport,
  reportPath: string,
  issues: SemanticQualityIssue[]
): ToolEnvelope<OfflineStaticActivationResult> {
  if (!envelope.data) {
    return {
      ...envelope,
      errors: envelope.errors ?? semanticIssuesForResponse(issues),
    };
  }

  return {
    ...envelope,
    data: {
      ...envelope.data,
      semanticQualitySummary: report.summary,
      semanticReportPath: reportPath,
      semanticQualityReport: report,
      paths: [...new Set([...envelope.data.paths, reportPath])],
    },
    errors: envelope.errors ?? semanticIssuesForResponse(issues),
  };
}

function attachDomcTrace(
  envelope: ToolEnvelope<OfflineStaticActivationResult>,
  plan: GenerationPlan
): ToolEnvelope<OfflineStaticActivationResult> {
  if (!envelope.data) return envelope;
  return {
    ...envelope,
    data: {
      ...envelope.data,
      moduleTrace: plan.moduleTrace,
    },
  };
}

export async function generateOfflineStaticRuntimePackage(
  input: GenerateOfflineStaticRuntimePackageInput
): Promise<ToolEnvelope<OfflineStaticActivationResult>> {
  const paths = await resolveOfflineStaticTargetPaths({ targetRoot: input.targetRoot });
  const contractBundle = await readOfflineStaticContract(paths);
  const actualContractFingerprint = computeContractFingerprint(
    contractBundle.contract,
    contractBundle.scenarioSchema
  );

  if (actualContractFingerprint !== contractBundle.contract.contractFingerprint) {
    throw new ToolError(
      createIssue({
        path: 'demo-contract/contract.json.contractFingerprint',
        code: 'contract_fingerprint_mismatch',
        severity: 'error',
        actual: contractBundle.contract.contractFingerprint,
        expected: actualContractFingerprint,
        fixHint: 'Rebuild the offline shell before generating runtime data.',
        autoRepairable: false,
      })
    );
  }

  const topicKey = normalizeTopicKey(input.topic, input.businessDescription);
  const seed = createStableSeed({
    topicKey,
    businessDescription: input.businessDescription,
    contractFingerprint: contractBundle.contract.contractFingerprint,
    generatorVersion: GENERATOR_VERSION,
  });
  const scenarioId = input.scenarioId?.trim() || `${topicKey}-runtime-demo`;
  const scenarioName = input.scenarioName?.trim() || `${input.topic} runtime demo`;
  const projectCount = normalizeCount(input.projectCount, 4);
  const plan = createOfflineStaticPlan({
    topic: input.topic,
    businessDescription: input.businessDescription,
    topicKey,
    scenarioId,
    scenarioName,
    projectCount,
    domcRegistry: contractBundle.domcRegistry,
    requestedModules: input.requestedModules,
  });
  const planBlockers = [
    ...(plan.moduleTrace ?? []).flatMap((trace) => (trace.blocker ? [trace.blocker] : [])),
    ...plan.trace.flatMap((trace) => (trace.blocker ? [trace.blocker] : [])),
  ].filter((blocker, index, all) => all.findIndex((item) => item.code === blocker.code && item.path === blocker.path) === index);

  if (planBlockers.length) {
    return errorEnvelope('DOMC generation plan contains blockers; runtime package was not generated.', planBlockers, {
      data: {
        phase: 'validation_failed',
        targetKind: 'offline-static',
        packageFormat: 'v2',
        targetRoot: paths.targetRoot,
        scenarioId,
        topicKey,
        seed,
        contractFingerprint: contractBundle.contract.contractFingerprint,
        scenarioFingerprint: '',
        domcRegistryFingerprint: contractBundle.domcRegistry.domcFingerprint,
        moduleContractFingerprints: contractBundle.contract.moduleContractFingerprints,
        moduleTrace: plan.moduleTrace,
        paths: [],
      },
      nextActions: planBlockers.flatMap((blocker) => blocker.nextActions),
    });
  }
  const blueprint = generateDeterministicBusinessBlueprint({
    topic: input.topic,
    businessDescription: input.businessDescription,
    topicKey,
    seed,
    contractFingerprint: contractBundle.contract.contractFingerprint,
    generatorVersion: GENERATOR_VERSION,
    projectCount,
  });
  const blueprintValidation = validateBusinessBlueprint(blueprint, { projectCount });

  if (!blueprintValidation.valid || !blueprintValidation.blueprint) {
    return errorEnvelope('Business Blueprint failed semantic validation and was not compiled.', blueprintValidation.issues, {
      data: {
        phase: 'validation_failed',
        targetKind: 'offline-static',
        targetRoot: paths.targetRoot,
        scenarioId,
        topicKey,
        seed,
        contractFingerprint: contractBundle.contract.contractFingerprint,
        scenarioFingerprint: '',
        semanticQualitySummary: {
          blueprintValid: false,
          diversityValid: false,
          semanticCoverageValid: false,
          issueCount: blueprintValidation.issues.length,
          warningCount: blueprintValidation.issues.filter((issue) => issue.severity === 'warning').length,
          errorCount: blueprintValidation.issues.filter((issue) => issue.severity === 'error').length,
        },
        paths: [],
      },
    });
  }

  const { draft, bindings } = compileBlueprintToIndustryDraft({
    blueprint,
    scenarioId,
    scenarioName,
    projectCount,
  });
  const requestedGeneratableModules = plan.scope;
  const moduleContracts = contractBundle.domcRegistry.modules.filter((moduleContract) =>
    requestedGeneratableModules.includes(moduleContract.moduleId as (typeof requestedGeneratableModules)[number])
  );
  const resolvedAdapters = resolveDemoGeneratorAdapters({
    domcRegistry: contractBundle.domcRegistry,
    requestedModules: requestedGeneratableModules,
    contractFingerprint: contractBundle.contract.contractFingerprint,
    targetCounts: plan.targetCounts,
  });

  if (resolvedAdapters.blockers.length) {
    return errorEnvelope('DOMC adapter resolution failed; runtime package was not generated.', resolvedAdapters.blockers, {
      data: {
        phase: 'validation_failed',
        targetKind: 'offline-static',
        packageFormat: 'v2',
        targetRoot: paths.targetRoot,
        scenarioId,
        topicKey,
        seed,
        contractFingerprint: contractBundle.contract.contractFingerprint,
        scenarioFingerprint: '',
        domcRegistryFingerprint: contractBundle.domcRegistry.domcFingerprint,
        moduleContractFingerprints: contractBundle.contract.moduleContractFingerprints,
        moduleTrace: plan.moduleTrace,
        paths: [],
      },
      nextActions: resolvedAdapters.blockers.flatMap((blocker) => blocker.nextActions),
    });
  }

  const adapterResults = await Promise.all(
    resolvedAdapters.selected.map((adapter) =>
      adapter.compile({
        domcRegistry: contractBundle.domcRegistry,
        moduleContracts,
        contractFingerprint: contractBundle.contract.contractFingerprint,
        domcFingerprint: contractBundle.domcRegistry.domcFingerprint,
        targetCounts: plan.targetCounts,
        plan,
        blueprint,
        draft,
        bindings,
        defaultScenarioPackage: contractBundle.defaultScenario,
      })
    )
  );
  const adapterIssues = [
    ...resolvedAdapters.selected.flatMap((adapter, adapterIndex) => {
      const compileResult = adapterResults[adapterIndex];
      return [
        ...validateAdapterMaterializations({
          domcRegistry: contractBundle.domcRegistry,
          adapter,
          materializations: compileResult.materializations,
        }),
        ...adapter.validate({
          domcRegistry: contractBundle.domcRegistry,
          moduleContracts,
          contractFingerprint: contractBundle.contract.contractFingerprint,
          domcFingerprint: contractBundle.domcRegistry.domcFingerprint,
          targetCounts: plan.targetCounts,
          compileResult,
        }).issues,
      ];
    }),
  ];

  if (adapterIssues.some((issue) => issue.severity === 'error')) {
    return errorEnvelope('DOMC adapter output failed validation and was not assembled.', adapterIssues, {
      data: {
        phase: 'validation_failed',
        targetKind: 'offline-static',
        packageFormat: 'v2',
        targetRoot: paths.targetRoot,
        scenarioId,
        topicKey,
        seed,
        contractFingerprint: contractBundle.contract.contractFingerprint,
        scenarioFingerprint: '',
        domcRegistryFingerprint: contractBundle.domcRegistry.domcFingerprint,
        moduleContractFingerprints: contractBundle.contract.moduleContractFingerprints,
        moduleTrace: plan.moduleTrace,
        paths: [],
      },
    });
  }

  const adapterMaterializations = adapterResults.flatMap((result) => result.materializations);
  const adapterBindings = adapterResults.flatMap((result) => result.semanticBindings);
  const assembled = assembleDemoScenarioPackage({
    scenario: {
      id: scenarioId,
      name: scenarioName,
      version: draft.scenario.version ?? '1.0.0',
      fingerprint: '',
      seed,
    },
    defaultScenarioPackage: contractBundle.defaultScenario,
    domcRegistry: contractBundle.domcRegistry,
    generatedMaterializations: adapterMaterializations,
    copyOnlyModules: plan.copiedSlices,
  });

  if (!assembled.scenarioPackage) {
    return errorEnvelope('DOMC assembler failed validation and was not written.', assembled.issues, {
      data: {
        phase: 'validation_failed',
        targetKind: 'offline-static',
        packageFormat: 'v2',
        targetRoot: paths.targetRoot,
        scenarioId,
        topicKey,
        seed,
        contractFingerprint: contractBundle.contract.contractFingerprint,
        scenarioFingerprint: '',
        domcRegistryFingerprint: contractBundle.domcRegistry.domcFingerprint,
        moduleContractFingerprints: contractBundle.contract.moduleContractFingerprints,
        moduleTrace: plan.moduleTrace,
        paths: [],
      },
    });
  }

  const scenarioPackage = assembled.scenarioPackage;
  scenarioPackage.scenario.seed = seed;
  scenarioPackage.scenario.fingerprint = computeScenarioFingerprint(scenarioPackage);

  const initialSummary = {
    schemaValid: true,
    contractValid: true,
    invariantValid: true,
    issueCount: 0,
  };
  const meta = await createRuntimeScenarioMeta({
    scenarioPackage,
    topicKey,
    seed,
    contractFingerprint: contractBundle.contract.contractFingerprint,
    generatorVersion: GENERATOR_VERSION,
    validationSummary: initialSummary,
  });
  meta.domcRegistryFingerprint = contractBundle.domcRegistry.domcFingerprint;
  meta.moduleContractFingerprints = contractBundle.contract.moduleContractFingerprints;
  meta.adapterVersions = Object.fromEntries(
    adapterResults.map((result) => [result.adapterId, result.adapterVersion])
  );
  meta.adapterCapabilitySummary = adapterResults.flatMap((result) =>
    result.moduleIds.map((moduleId) => ({
      moduleId,
      adapterId: result.adapterId,
      adapterVersion: result.adapterVersion,
      outputSourcePaths: result.materializations
        .filter((materialization) => materialization.moduleId === moduleId)
        .map((materialization) => materialization.sourcePath),
    }))
  );
  const schemaIssues = validateRuntimeScenarioPackage(
    scenarioPackage,
    contractBundle.scenarioSchema,
    contractBundle.contract
  );
  const contractIssues = validateRuntimeMeta(scenarioPackage, meta, contractBundle.contract);
  const invariantIssues = validateRuntimeInvariants(scenarioPackage);
  meta.validationSummary = summarizeRuntimeValidation(schemaIssues, contractIssues, invariantIssues);
  const validationErrors = [...schemaIssues, ...contractIssues, ...invariantIssues].filter(
    (issue) => issue.severity === 'error'
  );

  if (validationErrors.length) {
    return errorEnvelope('Generated runtime package failed validation and was not written.', validationErrors, {
      data: {
        phase: 'validation_failed',
        targetKind: 'offline-static',
        targetRoot: paths.targetRoot,
        scenarioId,
        topicKey,
        seed,
        contractFingerprint: contractBundle.contract.contractFingerprint,
        scenarioFingerprint: scenarioPackage.scenario.fingerprint,
        validationSummary: meta.validationSummary,
        paths: [],
      },
    });
  }

  const diversity = validateDiversity({ blueprint, draft, scenarioPackage });
  const coverage = validateSemanticCoverage({ blueprint, bindings: adapterBindings, scenarioPackage });
  const semanticIssues = [
    ...blueprintValidation.issues,
    ...diversity.issues,
    ...coverage.issues,
    ...(input.semanticIssueOverrides ?? []),
  ];
  const semanticReport = createSemanticQualityReport({
    scenarioId,
    topicKey,
    seed,
    generatorVersion: GENERATOR_VERSION,
    blueprint,
    diversitySummary: diversity.summary as unknown as Record<string, unknown>,
    semanticCoverageSummary: coverage.summary.records,
    bindings: adapterBindings,
    issues: semanticIssues,
  });
  const semanticErrors = semanticIssues.filter((issue) => issue.severity === 'error');
  if (semanticErrors.length) {
    const semanticFailedReportPath = await writeSemanticFailureReport(paths, semanticReport);
    return errorEnvelope('Generated runtime package failed semantic quality gates and was not written.', semanticErrors, {
      data: {
        phase: 'validation_failed',
        targetKind: 'offline-static',
        targetRoot: paths.targetRoot,
        scenarioId,
        topicKey,
        seed,
        contractFingerprint: contractBundle.contract.contractFingerprint,
        scenarioFingerprint: scenarioPackage.scenario.fingerprint,
        validationSummary: meta.validationSummary,
        semanticQualitySummary: semanticReport.summary,
        semanticReportPath: semanticFailedReportPath,
        semanticQualityReport: semanticReport,
        paths: [semanticFailedReportPath],
      },
      artifacts: [
        {
          kind: 'report',
          label: semanticFailedReportPath,
          path: path.join(paths.targetRoot, semanticFailedReportPath),
        },
      ],
      nextActions: ['Repair the Business Blueprint or Blueprint-to-draft mapping, then regenerate the runtime package.'],
    });
  }

  const writtenBase = await writeRuntimeCandidatePackage(paths, scenarioPackage, meta, {
    semanticReport,
    businessDescription: input.businessDescription,
  });
  const written = attachSemanticReport(
    writtenBase,
    semanticReport,
    writtenBase.data?.semanticReportPath ?? 'demo-scenarios/releases/.staging/semantic-report.json',
    semanticIssues
  );
  if (!input.activate) {
    return attachDomcTrace(written, plan);
  }

  const activatedBase = await activateRuntimePackage(paths, { releaseId: written.data?.releaseId });
  return attachDomcTrace(
    attachSemanticReport(
      activatedBase,
      semanticReport,
      activatedBase.data?.semanticReportPath ?? written.data?.semanticReportPath ?? '',
      semanticIssues
    ),
    plan
  );
}
