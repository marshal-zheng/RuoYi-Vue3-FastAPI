import type {
  CompiledDemoScenarioPackage,
  DemoDomcModuleContract,
  DemoDomcRegistry,
  DemoOfflineBlockerIssue,
  GenerationPlan,
  IndustryDataDraft,
  ValidationIssue,
} from '../types.js';
import type { BusinessBlueprint, SemanticAnchorBinding } from '../semantic/types.js';

export type DemoAdapterCapability =
  | 'business-blueprint'
  | 'sourcePath-materialization'
  | 'semantic-anchor-bindings'
  | 'deterministic-seed';

export type DemoAdapterInputKind = 'business-blueprint' | 'default-scenario' | 'domc-registry';

export interface AdapterMaterialization {
  moduleId: string;
  sourcePath: string;
  order: number;
  materializationReason: 'semantic-generated' | 'copied-default' | 'runtime-required';
  records: Array<Record<string, unknown>>;
  domcModuleVersion: string;
  adapterId: string;
  adapterVersion: string;
}

export interface DemoAdapterDecision {
  ok: boolean;
  blocker?: DemoOfflineBlockerIssue;
  reason: string;
}

export interface DemoAdapterCanGenerateInput {
  domcRegistry: DemoDomcRegistry;
  moduleContracts: DemoDomcModuleContract[];
  contractFingerprint: string;
  domcFingerprint: string;
  targetCounts: GenerationPlan['targetCounts'];
}

export interface DemoAdapterPlanInput extends DemoAdapterCanGenerateInput {
  plan: GenerationPlan;
}

export interface DemoAdapterPlan {
  adapterId: string;
  adapterVersion: string;
  moduleIds: string[];
  outputSourcePaths: string[];
  evidence: string[];
}

export interface DemoAdapterCompileInput extends DemoAdapterCanGenerateInput {
  plan: GenerationPlan;
  blueprint: BusinessBlueprint;
  draft: IndustryDataDraft;
  bindings: SemanticAnchorBinding[];
  defaultScenarioPackage: CompiledDemoScenarioPackage;
}

export interface DemoAdapterCompileResult {
  adapterId: string;
  adapterVersion: string;
  moduleIds: string[];
  materializations: AdapterMaterialization[];
  semanticBindings: SemanticAnchorBinding[];
  summary: Record<string, unknown>;
}

export interface DemoAdapterValidateInput extends DemoAdapterCanGenerateInput {
  compileResult: DemoAdapterCompileResult;
}

export interface DemoAdapterValidationResult {
  valid: boolean;
  issues: ValidationIssue[];
}

export interface DemoGeneratorAdapter {
  adapterId: string;
  adapterVersion: string;
  priority: number;
  supportedModules: string[];
  supportedDomcVersions: string[];
  capabilities: DemoAdapterCapability[];
  inputKinds: DemoAdapterInputKind[];
  outputSourcePaths: string[];
  canGenerate(input: DemoAdapterCanGenerateInput): DemoAdapterDecision;
  plan(input: DemoAdapterPlanInput): DemoAdapterPlan;
  compile(input: DemoAdapterCompileInput): Promise<DemoAdapterCompileResult>;
  validate(input: DemoAdapterValidateInput): DemoAdapterValidationResult;
  explainBlocker(input: DemoAdapterCanGenerateInput): DemoOfflineBlockerIssue;
}
