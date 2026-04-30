import type {
  DemoHandlerCoverage,
  DemoIndexedDbTableMapping,
  DemoInvariantDefinition,
  DemoScenarioModule,
} from '../scenarios/contract';

export type DemoDomcModuleId = string;
export type DemoDomcLifecycle = 'active' | 'deprecated' | 'experimental';
export type DemoDomcCapability = 'generatable' | 'copyOnly' | 'unsupported';
export type DemoDomcFieldSemanticKind =
  | 'identifier'
  | 'displayName'
  | 'description'
  | 'status'
  | 'enum'
  | 'timestamp'
  | 'owner'
  | 'department'
  | 'metric'
  | 'risk'
  | 'money'
  | 'quantity'
  | 'foreignKey'
  | 'opaquePayload';

export type DemoDomcQualityGateId =
  | 'domc-schema'
  | 'domc-registry-integrity'
  | 'domc-fingerprint'
  | 'adapter-registry'
  | 'adapter-capability'
  | 'module-blocker'
  | 'ui-journey-coverage'
  | 'handler-mapping-coverage'
  | 'contract-drift'
  | 'domc-provenance'
  | 'adapter-regression';

export type DemoDomcSemanticAnchorType =
  | 'storyBeat'
  | 'domainObject'
  | 'persona'
  | 'role'
  | 'processStage'
  | 'riskType'
  | 'metricDefinition';

export interface DemoDomcQualityGate {
  gate: DemoDomcQualityGateId;
  severity: 'error' | 'warning';
  description: string;
}

export interface DemoDomcAdapterReference {
  adapterId: string;
  adapterVersionRange: string;
  capabilities: readonly string[];
  outputSourcePaths: readonly string[];
  priority?: number;
}

export interface DemoDomcCopyOnlyPolicy {
  source: 'demo-contract/default-scenario.json' | 'bundle-default-v2';
  sourcePaths: readonly string[];
  reason: string;
  minItems: Record<string, number>;
}

export interface DemoDomcIndexedDbTableRef
  extends Pick<DemoIndexedDbTableMapping, 'table' | 'sourcePath' | 'primaryKey' | 'indexes' | 'minItems'> {}

export interface DemoDomcHandlerCoverageRef
  extends Pick<DemoHandlerCoverage, 'module' | 'source' | 'apiPrefix' | 'coveredRoutes' | 'unsupportedBehavior'> {}

export interface DemoDomcInvariantRef
  extends Pick<DemoInvariantDefinition, 'id' | 'description' | 'severity' | 'paths'> {}

export interface DemoDomcReferenceContract {
  field: string;
  targetEntity: string;
  targetField: string;
  relation: 'one-to-one' | 'many-to-one' | 'one-to-many' | 'many-to-many';
  required: boolean;
}

export interface DemoDomcFieldContract {
  name: string;
  required: boolean;
  nullable: boolean;
  semanticKind: DemoDomcFieldSemanticKind;
  enumValues?: readonly string[];
  defaultRepair?: 'derive' | 'copy-default' | 'block';
}

export interface DemoDomcEntityContract {
  entity: string;
  sourcePath: string;
  indexedDbTable: string;
  primaryKey: string;
  minItems: number;
  fields: readonly DemoDomcFieldContract[];
  references: readonly DemoDomcReferenceContract[];
  ownership: {
    recordOwner: 'adapter' | 'default-scenario' | 'runtime-required';
    mergePolicy: 'replace-sourcePath' | 'append-shards' | 'copy-only';
  };
}

export interface DemoDomcStateMachine {
  field: string;
  allowedStates: readonly string[];
  defaultState: string;
  terminalStates: readonly string[];
  transitions: readonly { from: string; to: readonly string[] }[];
  illegalCombinations: readonly { fields: readonly string[]; reason: string }[];
  defaultRepair: 'derive' | 'copy-default' | 'block';
}

export interface DemoDomcUiJourney {
  journeyId: string;
  entry: string;
  primarySourcePath: string;
  requiredSupportSourcePaths: readonly string[];
  listFields: readonly string[];
  detailFields: readonly string[];
  keyActions: readonly { action: string; demoBehavior: string }[];
  emptyState: string;
  errorState: string;
  minimumDemoChain: readonly string[];
}

export interface DemoDomcDiversityRule {
  ruleId: string;
  primarySourcePath: string;
  fields: readonly string[];
  dimensions: readonly string[];
  duplicateThreshold: number;
  templateSimilarityThreshold: number;
  severity: 'error' | 'warning';
  explainableExceptions: readonly string[];
}

export interface DemoDomcSemanticAnchorRule {
  ruleId: string;
  sourcePath: string;
  minAnchorTypes: number;
  requiredAnchorTypes: readonly DemoDomcSemanticAnchorType[];
  supportCategories: readonly string[];
}

export interface DemoDomcMaterializationPolicy {
  sourcePath: string;
  order: number;
  materializationReason: 'semantic-generated' | 'copied-default' | 'runtime-required';
  minItems: number;
}

export interface DemoDomcModuleContract {
  moduleId: DemoDomcModuleId;
  moduleVersion: string;
  lifecycle: DemoDomcLifecycle;
  capability: DemoDomcCapability;
  owner: string;
  sourcePaths: readonly string[];
  indexedDbTables: readonly DemoDomcIndexedDbTableRef[];
  handlerCoverage: readonly DemoDomcHandlerCoverageRef[];
  uiJourneys: readonly DemoDomcUiJourney[];
  entities: readonly DemoDomcEntityContract[];
  stateMachines: readonly DemoDomcStateMachine[];
  invariants: readonly DemoDomcInvariantRef[];
  diversityRules: readonly DemoDomcDiversityRule[];
  semanticAnchors?: readonly DemoDomcSemanticAnchorRule[];
  materializationPolicy: readonly DemoDomcMaterializationPolicy[];
  adapterRef?: DemoDomcAdapterReference;
  copyOnly?: DemoDomcCopyOnlyPolicy;
  unsupportedReason?: string;
  migrationSources: readonly string[];
}

export interface DemoDomcRegistry {
  schemaVersion: 1;
  registryVersion: string;
  generatedAt: string;
  domcFingerprint: string;
  contractVersion: 1;
  platformLayer: 'DOMC';
  modules: readonly DemoDomcModuleContract[];
  qualityGates: readonly DemoDomcQualityGate[];
  migrationSources: readonly string[];
}

export type DemoDomcRegistryDraft = Omit<DemoDomcRegistry, 'domcFingerprint'> & {
  domcFingerprint?: string;
};

export interface DemoDomcValidationIssue {
  path: string;
  code: string;
  severity: 'error' | 'warning';
  actual?: unknown;
  expected: string;
  fixHint: string;
  gate: DemoDomcQualityGateId;
}

export interface DemoDomcValidationResult {
  valid: boolean;
  issues: readonly DemoDomcValidationIssue[];
}

export interface DemoDomcAdapterReferenceSummary {
  moduleId: DemoScenarioModule;
  adapterId: string;
  adapterVersionRange: string;
  capability: DemoDomcCapability;
  outputSourcePaths: readonly string[];
}
