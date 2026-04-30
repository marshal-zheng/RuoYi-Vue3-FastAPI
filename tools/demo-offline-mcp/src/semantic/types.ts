import type { ValidationIssue } from '../types.js';

export type SemanticRiskSeverity = 'low' | 'medium' | 'high';

export interface SemanticDomainObject {
  id: string;
  label: string;
  description: string;
  attributes?: string[];
}

export interface SemanticDepartment {
  id: string;
  label: string;
  responsibility: string;
}

export interface SemanticPersona {
  id: string;
  name: string;
  role: string;
  departmentId: string;
  actions: string[];
}

export interface SemanticProcessStage {
  id: string;
  label: string;
  sequence: number;
  description: string;
  action: string;
}

export interface SemanticRiskType {
  id: string;
  label: string;
  severity: SemanticRiskSeverity;
  description: string;
  riskSignals: string[];
}

export interface SemanticMetricDefinition {
  id: string;
  name: string;
  description: string;
  unit: string;
  valueSamples: string[];
  trend?: 'up' | 'down' | 'flat';
}

export interface SemanticStoryBeat {
  id: string;
  title: string;
  summary: string;
  domainObjectId: string;
  departmentId: string;
  personaId: string;
  processStageId: string;
  riskTypeId: string;
  metricDefinitionIds: string[];
  outcome: string;
}

export interface BusinessBlueprint {
  schemaVersion: 1;
  topic: string;
  businessDescription?: string;
  topicKey: string;
  seed: string;
  contractFingerprint: string;
  generatorVersion: string;
  industry: {
    name: string;
    keywords: string[];
  };
  domainObjects: SemanticDomainObject[];
  departments: SemanticDepartment[];
  personas: SemanticPersona[];
  processStages: SemanticProcessStage[];
  riskTypes: SemanticRiskType[];
  metricDefinitions: SemanticMetricDefinition[];
  storyBeats: SemanticStoryBeat[];
}

export type SemanticAnchorType =
  | 'storyBeat'
  | 'domainObject'
  | 'persona'
  | 'role'
  | 'processStage'
  | 'riskType'
  | 'metricDefinition';

export interface SemanticAnchorRef {
  type: SemanticAnchorType;
  id: string;
  label: string;
}

export interface SemanticAnchorBinding {
  recordKind: 'primary' | 'supporting';
  recordPath: string;
  recordKey: string;
  module: 'project' | 'simulation';
  anchors: SemanticAnchorRef[];
  supports?: string[];
}

export type SemanticGate =
  | 'blueprint-schema'
  | 'blueprint-semantic-minimum'
  | 'diversity'
  | 'semantic-coverage';

export interface SemanticQualityIssue extends ValidationIssue {
  gate: SemanticGate;
}

export interface SemanticQualitySummary {
  blueprintValid: boolean;
  diversityValid: boolean;
  semanticCoverageValid: boolean;
  issueCount: number;
  warningCount: number;
  errorCount: number;
}

export interface SemanticBlueprintSummary {
  domainObjectCount: number;
  personaCount: number;
  departmentCount: number;
  processStageCount: number;
  riskTypeCount: number;
  metricDefinitionCount: number;
  storyBeatCount: number;
}

export interface SemanticCoverageSummaryItem {
  recordPath: string;
  recordKey: string;
  anchorTypes: SemanticAnchorType[];
  anchorIds: string[];
  anchorLabels: string[];
}

export interface SemanticAnchorBindingSummaryItem extends SemanticCoverageSummaryItem {
  recordKind: SemanticAnchorBinding['recordKind'];
  module: SemanticAnchorBinding['module'];
  supports: string[];
}

export interface SemanticQualityReport {
  schemaVersion: 1;
  scenarioId: string;
  topicKey: string;
  seed: string;
  generatorVersion: string;
  summary: SemanticQualitySummary;
  blueprintSummary: SemanticBlueprintSummary;
  diversitySummary: Record<string, unknown>;
  semanticCoverageSummary: SemanticCoverageSummaryItem[];
  anchorBindingSummary: SemanticAnchorBindingSummaryItem[];
  issues: SemanticQualityIssue[];
}

export interface SemanticValidationResult<TSummary = Record<string, unknown>> {
  valid: boolean;
  summary: TSummary;
  issues: SemanticQualityIssue[];
}
