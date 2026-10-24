export const MOCK_OVERLAY_STATE_TYPES = [
  'empty',
  'latency',
  'problem',
  'forbidden',
  'timeout',
  'unsupported',
  'readonly',
] as const;

export const MOCK_OVERLAY_HTTP_METHODS = [
  'GET',
  'POST',
  'PUT',
  'DELETE',
  'PATCH',
  'OPTIONS',
  'HEAD',
] as const;

export const MOCK_OVERLAY_CONTRACT_EXCEPTIONS = [
  'problem-response',
  'schema-unavailable',
  'local-contract',
  'unhandled-api',
  'not-applicable',
] as const;

export type MockOverlayStateType = (typeof MOCK_OVERLAY_STATE_TYPES)[number];

export type MockOverlayHttpMethod = (typeof MOCK_OVERLAY_HTTP_METHODS)[number];

export type MockOverlayContractException = (typeof MOCK_OVERLAY_CONTRACT_EXCEPTIONS)[number];

export type MockOverlayResetStrategy = 'overlay-only';

export type MockOverlayActivationSource = 'none' | 'bootstrap' | 'runtime-api' | 'vitest';

export type MockOverlayProjection = 'empty-page' | 'empty-list' | 'readonly-view';

export interface MockOverlayTarget {
  method: MockOverlayHttpMethod;
  openapiPath: string;
  mswPath: string;
  handlerTag: string;
}

export interface MockOverlayComposition {
  compatibleWith?: string[];
  conflictsWith?: string[];
}

export interface MockOverlayContractMetadata {
  exception?: MockOverlayContractException;
  reason?: string;
}

export interface MockOverlayResponseConfig {
  status?: number;
  delayMs?: number;
  reason?: string;
  errorCode?: number | string;
  projection?: MockOverlayProjection;
}

export interface MockOverlayRegistryEntry {
  id: string;
  name: string;
  stateType: MockOverlayStateType;
  target: MockOverlayTarget;
  pages: string[];
  owner: string;
  tests: string[];
  risk: string;
  coreMatrix: boolean;
  e2eEnabled: boolean;
  resetStrategy: MockOverlayResetStrategy;
  composition: MockOverlayComposition;
  contract?: MockOverlayContractMetadata;
  response?: MockOverlayResponseConfig;
}

export interface MockOverlayRegistrySummary {
  id: string;
  name: string;
  stateType: MockOverlayStateType;
  method: MockOverlayHttpMethod;
  openapiPath: string;
  mswPath: string;
  handlerTag: string;
  pages: string[];
  owner: string;
  tests: string[];
  coreMatrix: boolean;
  e2eEnabled: boolean;
  resetStrategy: MockOverlayResetStrategy;
  risk: string;
}

export interface MockOverlayState {
  activeIds: string[];
  activeEntries: MockOverlayRegistryEntry[];
  source: MockOverlayActivationSource;
}

export type MockOverlayActivationInput = string[] | MockOverlayState | undefined;

export interface MockOverlayValidationIssue {
  code: string;
  overlayId?: string;
  method?: MockOverlayHttpMethod;
  openapiPath?: string;
  handlerTag?: string;
  message: string;
}
