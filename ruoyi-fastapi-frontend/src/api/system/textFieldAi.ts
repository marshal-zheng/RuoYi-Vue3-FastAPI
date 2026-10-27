import { validateBasicRichTextDocument } from '@zxio/text-editor/core';
import type { ZxTextEditorDocument } from '@zxio/text-editor';
import type { AIContextResult } from '@zxio/zxui/ai-context';
import { aiContextDefinitions } from '@/ai-context/definitions';
import type { AxiosResponse } from 'axios';
import type {
  TextFieldAiRequest as GeneratedTextFieldAiRequest,
  TextFieldAiStatus as GeneratedTextFieldAiStatus,
} from '@/api/_generated/types.gen';
import { createSseClient } from '@/api/_generated/core/serverSentEvents.gen';
import { isRecord } from '@/types/http-contract';
import { getSecuritySessionSignal } from '@/utils/auth';
import request from '@/utils/request';

export type TextFieldAIRequest = GeneratedTextFieldAiRequest;
export type TextFieldAIStatus = GeneratedTextFieldAiStatus;

const messages = {
  'context-rejected': 'AI 上下文已失效，请重新打开后重试',
  'policy-rejected': 'AI 策略已更新，请重新加载后重试',
  'permission-denied': '没有此操作权限',
  'quota-exceeded': 'AI 请求过于频繁，请稍后重试',
  'provider-unavailable': 'AI 服务暂不可用，请联系管理员或稍后重试',
  timeout: 'AI 生成超时，请稍后重试',
  'invalid-output': 'AI 返回格式不符合要求，请重试或调整要求',
  'output-limit': 'AI 返回内容超过限制，请缩短要求后重试',
  'incomplete-output': 'AI 输出中断，请重试',
} as const;

export class TextFieldAIError extends Error {
  constructor(
    readonly code: keyof typeof messages,
    readonly retryAfter?: number
  ) {
    super(messages[code]);
    this.name = 'TextFieldAIError';
  }
}
const isCode = (code: unknown): code is keyof typeof messages =>
  typeof code === 'string' && Object.hasOwn(messages, code);
const exact = (value: Record<string, unknown>, keys: string[]) =>
  Object.keys(value).length === keys.length && keys.every((key) => Object.hasOwn(value, key));
const sameIds = (value: unknown, expected: readonly string[]) =>
  Array.isArray(value) &&
  value.length === expected.length &&
  value.every((id, index) => id === expected[index]);

export interface TextFieldAIGenerateOptions {
  signal: AbortSignal;
  onDelta: (text: string) => void;
}

export function getTextFieldAIStatus(
  options: { signal?: AbortSignal } = {}
): Promise<TextFieldAIStatus> {
  return request<TextFieldAIStatus>({
    url: '/system/ai/text-field/status',
    method: 'get',
    signal: options.signal,
    silentError: true,
  });
}

/** One authenticated generation; preview deltas never become a successful document on their own. */
export async function generateTextFieldAI(
  body: TextFieldAIRequest,
  options: TextFieldAIGenerateOptions
): Promise<AIContextResult<ZxTextEditorDocument>> {
  const controller = new AbortController();
  const signals = [options.signal, getSecuritySessionSignal()];
  const abort = () => controller.abort();
  const assertActive = () => {
    if (controller.signal.aborted) throw new DOMException('AI 生成已取消', 'AbortError');
  };
  for (const signal of signals) {
    if (signal.aborted) abort();
    else signal.addEventListener('abort', abort, { once: true });
  }

  let failure: unknown;
  let requestFailure: unknown;
  let stream: AsyncGenerator<unknown, void, unknown> | undefined;
  const invalidResult = () => new TextFieldAIError('invalid-output');
  let terminal: AIContextResult<ZxTextEditorDocument> | TextFieldAIError | undefined;
  const expectedIds = body.context.map((item) => item.id);
  const definition = Object.values(aiContextDefinitions).find((item) => item.id === body.scope);
  const noticeIds = new Set<string>(
    definition?.items.filter((item) => item.sensitivity !== 'secret').map((item) => item.id)
  );

  try {
    assertActive();
    const endpoint = '/system/ai/text-field/generate';
    const base = String(import.meta.env.VITE_APP_BASE_API || '').replace(/\/$/, '');
    ({ stream } = createSseClient({
      url: new URL(`${base}${endpoint}`, window.location.origin).href,
      method: 'POST',
      signal: controller.signal,
      // The generated parser only decodes SSE. The app client owns the actual request and session.
      fetch: async () => {
        try {
          const response = await request<AxiosResponse<ReadableStream<Uint8Array>>>(
            {
              url: endpoint,
              method: 'post',
              data: body,
              headers: {
                Accept: 'text/event-stream',
                'Content-Type': 'application/json',
              },
              responseType: 'stream',
              signal: controller.signal,
              timeout: 0,
              silentSuccess: true,
              silentError: true,
            },
            {
              isReturnNativeResponse: true,
              isTransformResponse: false,
              retry: false,
            }
          );
          assertActive();
          const contentType = String(response.headers['content-type'] || '');
          if (!/^text\/event-stream(?:;|$)/i.test(contentType) || !response.data?.getReader) {
            await response.data?.cancel?.();
            throw invalidResult();
          }
          return new Response(response.data, {
            status: response.status,
            headers: { 'Content-Type': contentType },
          });
        } catch (error) {
          requestFailure = error;
          throw error;
        }
      },
      sseMaxRetryAttempts: 1,
      onSseError(error) {
        failure = error;
      },
    }));

    while (true) {
      const next = await stream.next();
      if (next.done) break;
      const event = next.value;
      assertActive();
      if (
        !isRecord(event) ||
        terminal ||
        event.requestId !== body.requestId ||
        event.captureId !== body.captureId
      )
        throw invalidResult();
      if (
        event.type === 'delta' &&
        exact(event, ['type', 'requestId', 'captureId', 'text']) &&
        typeof event.text === 'string' &&
        event.text.length > 0 &&
        [...event.text].length <= 5000
      ) {
        options.onDelta(event.text);
      } else if (
        event.type === 'error' &&
        exact(event, ['type', 'requestId', 'captureId', 'code', 'message']) &&
        isCode(event.code) &&
        typeof event.message === 'string'
      ) {
        terminal = new TextFieldAIError(event.code);
      } else if (
        event.type === 'result' &&
        exact(event, ['type', 'requestId', 'captureId', 'document', 'notices', 'meta'])
      ) {
        try {
          const document = validateBasicRichTextDocument(event.document);
          if (
            !Array.isArray(event.notices) ||
            event.notices.length > 16 ||
            event.notices.some(
              (notice) =>
                !isRecord(notice) ||
                !exact(notice, ['code', 'contextIds']) ||
                notice.code !== 'information-unavailable' ||
                !Array.isArray(notice.contextIds) ||
                notice.contextIds.length > 16 ||
                new Set(notice.contextIds).size !== notice.contextIds.length ||
                notice.contextIds.some((id) => typeof id !== 'string' || !noticeIds.has(id))
            )
          )
            throw invalidResult();
          if (!document && !event.notices.length) throw invalidResult();
          if (
            !isRecord(event.meta) ||
            !exact(event.meta, ['promptVersion', 'model', 'contextIds']) ||
            event.meta.promptVersion !== 'text-field/v1' ||
            typeof event.meta.model !== 'string' ||
            !event.meta.model ||
            [...event.meta.model].length > 128 ||
            !sameIds(event.meta.contextIds, expectedIds)
          )
            throw invalidResult();
          terminal = {
            document,
            notices: event.notices as AIContextResult<ZxTextEditorDocument>['notices'],
            meta: {
              promptVersion: 'text-field/v1',
              model: event.meta.model,
              contextIds: expectedIds,
            },
          };
        } catch {
          throw invalidResult();
        }
      } else {
        throw invalidResult();
      }
    }
    assertActive();
    if (requestFailure) throw requestFailure;
    if (failure) throw invalidResult();
    if (!terminal) throw invalidResult();
    if (terminal instanceof TextFieldAIError) throw terminal;
    return terminal;
  } catch (error) {
    assertActive();
    if (error instanceof TextFieldAIError) throw error;
    const problem = isRecord(error) && isRecord(error.problem) ? error.problem : undefined;
    if (problem?.status === 401) throw error; // The app HTTP client owns authentication recovery.
    const code = problem?.aiCode;
    const status = problem?.status;
    const mapped = isCode(code)
      ? code
      : status === 403
        ? 'permission-denied'
        : status === 422
          ? 'context-rejected'
          : status === 429
            ? 'quota-exceeded'
            : 'provider-unavailable';
    const meta = isRecord(error) && isRecord(error.meta) ? error.meta : undefined;
    const retryAfter = meta?.retryAfter;
    throw new TextFieldAIError(
      mapped,
      mapped === 'quota-exceeded' &&
      typeof retryAfter === 'number' &&
      Number.isSafeInteger(retryAfter) &&
      retryAfter > 0
        ? retryAfter
        : undefined
    );
  } finally {
    // Abort before closing the parser so its active reader cancels even after a terminal frame.
    controller.abort();
    for (const signal of signals) signal.removeEventListener('abort', abort);
    await stream?.return(undefined).catch(() => undefined);
  }
}
