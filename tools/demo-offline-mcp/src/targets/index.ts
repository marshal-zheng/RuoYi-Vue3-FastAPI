import type {
  CompiledDemoScenarioPackage,
  DemoOfflineContractManifest,
  ImportDryRunSummary,
  RuntimeScenarioMeta,
  RuntimeValidationSummary,
  ToolEnvelope,
} from '../types.js';

export type DemoTargetKind = 'source-generated' | 'offline-static';

export interface DemoTargetAdapter {
  kind: DemoTargetKind;
  readContract?(): Promise<DemoOfflineContractManifest>;
  validate?(packageValue: CompiledDemoScenarioPackage, meta?: RuntimeScenarioMeta): Promise<ToolEnvelope<RuntimeValidationSummary>>;
  dryRun?(packageValue: CompiledDemoScenarioPackage): Promise<ToolEnvelope<ImportDryRunSummary>>;
  writeCandidate?(packageValue: CompiledDemoScenarioPackage, meta: RuntimeScenarioMeta): Promise<ToolEnvelope<unknown>>;
  activate?(): Promise<ToolEnvelope<unknown>>;
}
