import {
  isBatchResult,
  type BatchResult,
  type HttpContractMeta,
  type ProblemDetails,
} from '@/types/http-contract';

import { resolveFeedbackRegistryEntry } from './registry';
import { showMessage } from './message';
import { showNotification } from './notification';
import type {
  FeedbackOptions,
  ProblemFeedbackContext,
  ResolvedFeedbackOptions,
  SuccessFeedbackContext,
} from './types';

const DEFAULT_ACCEPTED_MESSAGE = '请求已受理，可稍后查看进度';

const toNumber = (value: unknown): number | undefined => {
  if (value === null || value === undefined || value === '') {
    return undefined;
  }
  const numericValue = Number(value);
  return Number.isFinite(numericValue) ? numericValue : undefined;
};

const resolveMessage = (
  value: string | ((context: SuccessFeedbackContext) => string) | undefined,
  context: SuccessFeedbackContext,
  fallback: string
): string => {
  if (typeof value === 'function') {
    return value(context);
  }
  if (typeof value === 'string' && value.trim()) {
    return value;
  }
  return fallback;
};

const appendTracking = (problem: ProblemDetails, meta: HttpContractMeta): string => {
  const lines = [problem.detail || problem.title];
  if (meta.retryAfter !== undefined) {
    lines.push(`请在 ${meta.retryAfter} 秒后重试`);
  }
  if (problem.requestId || meta.requestId) {
    lines.push(`Request ID: ${problem.requestId || meta.requestId}`);
  }
  if (problem.traceId || meta.traceId) {
    lines.push(`Trace ID: ${problem.traceId || meta.traceId}`);
  }
  return lines.filter(Boolean).join('\n');
};

const readBatchSummary = (payload: unknown): BatchResult | null => {
  return isBatchResult(payload) ? payload : null;
};

export const resolveFeedbackOptions = (options?: FeedbackOptions): ResolvedFeedbackOptions => ({
  mode: options?.mode ?? 'silent',
  key: options?.key,
  successContext: options?.successContext ?? {},
  validationTarget: options?.validationTarget,
});

export const presentSuccessFeedback = ({
  status,
  payload,
  meta,
  feedback,
}: {
  status: number;
  payload: unknown;
  meta: HttpContractMeta;
  feedback: ResolvedFeedbackOptions;
}): void => {
  if (feedback.mode !== 'auto') {
    return;
  }

  const context: SuccessFeedbackContext = {
    key: feedback.key,
    status,
    payload,
    meta,
    successContext: feedback.successContext,
  };
  const entry = feedback.key ? resolveFeedbackRegistryEntry(feedback.key) : { success: '操作成功' };

  if (status === 202) {
    void showNotification({
      type: 'info',
      title: '已受理',
      message: resolveMessage(entry.accepted, context, DEFAULT_ACCEPTED_MESSAGE),
      duration: 4000,
    });
    return;
  }

  const batchResult = readBatchSummary(payload);
  if (batchResult) {
    const succeeded = toNumber(batchResult.summary.succeeded) ?? 0;
    const failed = toNumber(batchResult.summary.failed) ?? 0;
    const total = toNumber(batchResult.summary.total) ?? batchResult.results.length;
    const summaryMessage = `共 ${total} 项，成功 ${succeeded} 项，失败 ${failed} 项`;
    if (failed > 0 && succeeded > 0) {
      void showNotification({
        type: 'warning',
        title: '部分完成',
        message: summaryMessage,
        duration: 5000,
      });
      return;
    }
    if (failed > 0) {
      void showNotification({
        type: 'error',
        title: '操作未完成',
        message: summaryMessage,
        duration: 5000,
      });
      return;
    }
  }

  void showMessage({
    type: 'success',
    message: resolveMessage(entry.success, context, '操作成功'),
  });
};

export const presentProblemFeedback = ({
  problem,
  meta,
  feedback,
}: ProblemFeedbackContext): void => {
  if (feedback.mode !== 'auto') {
    return;
  }

  if (problem.status === 422 && feedback.validationTarget && problem.errors?.length) {
    feedback.validationTarget.apply(problem.errors);
    return;
  }

  const message = appendTracking(problem, meta);
  if (problem.status === 429) {
    void showNotification({
      type: 'warning',
      title: problem.title || '请求过于频繁',
      message,
      duration: 6000,
    });
    return;
  }

  if (problem.status === 422) {
    const errorLines = (problem.errors || []).map((item) => `${item.field}: ${item.message}`);
    void showNotification({
      type: 'error',
      title: problem.title || '参数验证失败',
      message: errorLines.length ? errorLines.join('\n') : message,
      duration: 6000,
    });
    return;
  }

  if (problem.status >= 500 || [403, 404, 409].includes(problem.status)) {
    void showNotification({
      type: 'error',
      title: problem.title || '请求失败',
      message,
      duration: 6000,
    });
    return;
  }

  void showMessage({ type: 'error', message: problem.detail || problem.title || '请求失败' });
};
