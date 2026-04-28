import type { ValidationIssue } from './types.js';

export class ToolError extends Error {
  readonly issue: ValidationIssue;

  constructor(issue: ValidationIssue) {
    super(`${issue.code}: ${issue.fixHint}`);
    this.name = 'ToolError';
    this.issue = issue;
  }
}

export interface ToolErrorPayload {
  message: string;
  issue: ValidationIssue;
}

export interface CheckResult {
  profile: 'candidate-focused-tests' | 'frontend-type-check' | 'candidate-demo-offline-build' | 'promoted-demo-offline-build';
  command: string[];
  cwd: string;
  exitCode: number | null;
  durationMs: number;
  passed: boolean;
  summary: string;
  stdoutTail: string[];
  stderrTail: string[];
  nextActions: string[];
}

export function createIssue(params: ValidationIssue): ValidationIssue {
  return params;
}

export function issueFromUnknown(error: unknown, fallbackPath = '$'): ValidationIssue {
  if (error instanceof ToolError) {
    return error.issue;
  }

  return {
    path: fallbackPath,
    code: 'unexpected_error',
    severity: 'error',
    actual: error instanceof Error ? error.message : String(error),
    expected: 'Successful tool execution',
    fixHint: 'Inspect the error details and retry after correcting the input or project state.',
    autoRepairable: false,
  };
}
