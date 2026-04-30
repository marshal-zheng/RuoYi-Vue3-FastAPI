import type {
  CompiledDemoScenarioPackage,
  RuntimeScenarioMeta,
  RuntimeValidationSummary,
  ToolEnvelope,
} from '../types.js';
import { okEnvelope } from '../types.js';
import { readOfflineStaticContract } from '../offline-static/contract.js';
import { dryRunImportRuntimePackage } from '../offline-static/import-dry-run.js';
import { validateRuntimeInvariants } from '../offline-static/invariants.js';
import { resolveOfflineStaticTargetPaths, type OfflineStaticTargetPaths } from '../offline-static/paths.js';
import {
  summarizeRuntimeValidation,
  validateRuntimeMeta,
  validateRuntimeScenarioPackage,
} from '../offline-static/scenario-validation.js';
import { activateRuntimePackage, writeRuntimeCandidatePackage } from '../offline-static/writer.js';
import type { DemoTargetAdapter } from './index.js';

export class OfflineStaticTargetAdapter implements DemoTargetAdapter {
  readonly kind = 'offline-static' as const;
  private readonly pathsPromise: Promise<OfflineStaticTargetPaths>;

  constructor(targetRoot: string) {
    this.pathsPromise = resolveOfflineStaticTargetPaths({ targetRoot });
  }

  async readContract() {
    return (await readOfflineStaticContract(await this.pathsPromise)).contract;
  }

  async validate(
    packageValue: CompiledDemoScenarioPackage,
    meta?: RuntimeScenarioMeta
  ): Promise<ToolEnvelope<RuntimeValidationSummary>> {
    const contractBundle = await readOfflineStaticContract(await this.pathsPromise);
    const schemaIssues = validateRuntimeScenarioPackage(
      packageValue,
      contractBundle.scenarioSchema,
      contractBundle.contract
    );
    const contractIssues = validateRuntimeMeta(packageValue, meta, contractBundle.contract);
    const invariantIssues = validateRuntimeInvariants(packageValue);
    const summary = summarizeRuntimeValidation(schemaIssues, contractIssues, invariantIssues);
    const errors = [...schemaIssues, ...contractIssues, ...invariantIssues].filter(
      (issue) => issue.severity === 'error'
    );

    if (errors.length) {
      return { ok: false, summary: 'Runtime package validation failed.', data: summary, errors };
    }

    return okEnvelope('Runtime package validation succeeded.', summary);
  }

  async dryRun(packageValue: CompiledDemoScenarioPackage) {
    const contractBundle = await readOfflineStaticContract(await this.pathsPromise);
    return dryRunImportRuntimePackage(contractBundle.contract, packageValue);
  }

  async writeCandidate(packageValue: CompiledDemoScenarioPackage, meta: RuntimeScenarioMeta) {
    return writeRuntimeCandidatePackage(await this.pathsPromise, packageValue, meta);
  }

  async activate() {
    return activateRuntimePackage(await this.pathsPromise);
  }
}
