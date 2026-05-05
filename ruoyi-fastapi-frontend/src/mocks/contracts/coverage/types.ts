export const CONTRACT_COVERAGE_STATUSES = [
  'mock-handled',
  'real-only',
  'unsupported-501',
  'legacy-local-contract',
  'missing',
] as const;

export const CONTRACT_SCHEMA_STATUSES = [
  'openapi-validated',
  'schema-unavailable',
  'binary-response',
  'local-schema-validated',
  'not-applicable',
] as const;

export type ContractHttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH' | 'OPTIONS' | 'HEAD';

export type ContractCoverageStatus = (typeof CONTRACT_COVERAGE_STATUSES)[number];

export type ContractSchemaStatus = (typeof CONTRACT_SCHEMA_STATUSES)[number];

export type ContractPersistenceBoundary =
  | 'dexie'
  | 'readonly'
  | 'unsupported-501'
  | 'real-only'
  | 'none';

export interface ContractRegistryEntry {
  method: ContractHttpMethod;
  openapiPath: string;
  mswPath?: string;
  handlerTag?: string;
  owner: string;
  status: ContractCoverageStatus;
  critical: boolean;
  schemaStatus: ContractSchemaStatus;
  tests: string[];
  persistence?: ContractPersistenceBoundary;
  localContract?: string;
  reason?: string;
  impact?: string;
  migrationTarget?: string;
}

export type OpenApiResponseSchemaAvailability =
  | 'available'
  | 'empty'
  | 'missing'
  | 'binary-response';

export interface ContractOpenApiOperation {
  method: ContractHttpMethod;
  openapiPath: string;
  operationId: string;
  tags: string[];
  summary: string;
  responseSchemaAvailability: OpenApiResponseSchemaAvailability;
  responseContentTypes: string[];
}

export interface MockContractCoverageSummary {
  operationCount: number;
  byStatus: Record<ContractCoverageStatus, number>;
  criticalTotal: number;
  criticalFailures: number;
  schemaValidated: number;
  schemaUnavailable: number;
  binaryResponses: number;
  localContracts: number;
}

export interface MockContractCoverageFailure {
  code: string;
  method?: ContractHttpMethod;
  openapiPath?: string;
  handlerTag?: string;
  file?: string;
  message: string;
}

export interface MockContractCoverageWarning {
  code: string;
  method?: ContractHttpMethod;
  openapiPath?: string;
  handlerTag?: string;
  file?: string;
  message: string;
}

export interface MockContractCoverageReportEntry extends ContractRegistryEntry {
  operationId: string;
  tags: string[];
  summary: string;
  responseSchemaAvailability: OpenApiResponseSchemaAvailability;
  responseContentTypes: string[];
  registryFile: string;
}

export interface MockContractCoverageReport {
  artifact: {
    path: 'shared/openapi.json';
    openapi: string;
    title?: string;
    version?: string;
    fingerprint: string;
    operationCount: number;
  };
  summary: MockContractCoverageSummary;
  entries: MockContractCoverageReportEntry[];
  failures: MockContractCoverageFailure[];
  warnings: MockContractCoverageWarning[];
}
