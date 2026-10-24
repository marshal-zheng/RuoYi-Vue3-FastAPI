import type {
  HttpContractMeta,
  ProblemDetails,
  ProblemValidationError,
} from '@/types/http-contract';

export type FeedbackMode = 'auto' | 'manual' | 'silent';

export interface ValidationTarget {
  apply(errors: ProblemValidationError[]): void;
}

export interface FeedbackOptions {
  mode?: FeedbackMode;
  key?: string;
  successContext?: Record<string, unknown>;
  validationTarget?: ValidationTarget;
}

export interface ResolvedFeedbackOptions {
  mode: FeedbackMode;
  key?: string;
  successContext: Record<string, unknown>;
  validationTarget?: ValidationTarget;
}

export interface FeedbackRegistryEntry {
  success: string | ((context: SuccessFeedbackContext) => string);
  accepted?: string | ((context: SuccessFeedbackContext) => string);
}

export interface SuccessFeedbackContext {
  key?: string;
  status: number;
  payload: unknown;
  meta: HttpContractMeta;
  successContext: Record<string, unknown>;
}

export interface ProblemFeedbackContext {
  problem: ProblemDetails;
  meta: HttpContractMeta;
  feedback: ResolvedFeedbackOptions;
}
