import type { AxiosResponse } from 'axios';
import type {
  RemarkAiRequest as GeneratedRemarkAiRequest,
  RemarkAiStatus as GeneratedRemarkAiStatus,
} from '@/api/_generated/types.gen';
import { createSseClient } from '@/api/_generated/core/serverSentEvents.gen';
import { readRemark, type RemarkValue } from '@/components/ui/Remark/contract';
import { isRecord } from '@/types/http-contract';
import { getSecuritySessionSignal } from '@/utils/auth';
import request from '@/utils/request';

export type RemarkAiRequest = GeneratedRemarkAiRequest;
export type RemarkAiStatus = GeneratedRemarkAiStatus;
export type RemarkAiScene = RemarkAiRequest['scene'];
export type RemarkAiContext = NonNullable<RemarkAiRequest['context']>;

export interface RemarkAiGenerateOptions {
  signal: AbortSignal;
  onDelta: (text: string) => void;
}

export class RemarkAiError extends Error {
  constructor(
    message: string,
    readonly code: string,
    options?: ErrorOptions
  ) {
    super(message, options);
    this.name = 'RemarkAiError';
  }
}

export function getRemarkAIStatus(options: { signal?: AbortSignal } = {}): Promise<RemarkAiStatus> {
  return request<RemarkAiStatus>({
    url: '/system/remark/ai/status',
    method: 'get',
    signal: options.signal,
    silentError: true,
  });
}

/** One authenticated generation; preview deltas never become a successful document on their own. */
export async function generateRemarkAI(
  body: RemarkAiRequest,
  options: RemarkAiGenerateOptions
): Promise<RemarkValue> {
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
  const invalidResult = () =>
    new RemarkAiError('AI 返回的备注格式不正确，请重试', 'invalid_result');

  try {
    assertActive();
    const endpoint = '/system/remark/ai/generate';
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
      if (!isRecord(event)) throw invalidResult();
      if (event.type === 'delta' && typeof event.text === 'string') {
        options.onDelta(event.text);
      } else if (event.type === 'error' && typeof event.message === 'string') {
        throw new RemarkAiError(
          event.message || 'AI 生成失败，请重试',
          typeof event.code === 'string' ? event.code : 'generation_failed'
        );
      } else if (event.type === 'result' && 'document' in event) {
        let document: RemarkValue;
        try {
          document = readRemark(event.document);
        } catch {
          throw invalidResult();
        }
        if (!document) throw invalidResult();
        return document;
      } else {
        throw invalidResult();
      }
    }
    assertActive();
    if (requestFailure) throw requestFailure;
    throw new RemarkAiError('AI 生成中断，请重试', 'stream_interrupted', {
      cause: failure,
    });
  } finally {
    // Abort before closing the parser so its active reader cancels even after a terminal frame.
    controller.abort();
    for (const signal of signals) signal.removeEventListener('abort', abort);
    await stream?.return(undefined).catch(() => undefined);
  }
}
