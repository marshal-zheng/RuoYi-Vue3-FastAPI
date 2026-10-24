import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { AxiosResponse } from 'axios';
import { clearSecurityTokens } from '@/utils/auth';
import { mockRemark } from '@/mocks/data/remark';
import request from '@/utils/request';
import { generateRemarkAI, getRemarkAIStatus, type RemarkAiRequest } from './remarkAi';

vi.mock('@/utils/request', () => ({ default: vi.fn() }));

const body: RemarkAiRequest = {
  scene: 'post',
  instruction: '整理为简洁的岗位说明',
  target: 'document',
  document: null,
  context: { postName: '巡检员' },
};
const document = mockRemark('负责日常巡检。', 'ai');
const frame = (event: unknown) => `data: ${JSON.stringify(event)}\n\n`;
const response = (data: ReadableStream<Uint8Array>) =>
  ({
    data,
    status: 200,
    headers: { 'content-type': 'text/event-stream; charset=utf-8' },
  }) as AxiosResponse<ReadableStream<Uint8Array>>;
const respond = (text: string) =>
  vi.mocked(request).mockResolvedValue(response(new Response(text).body!));
const options = () => ({
  signal: new AbortController().signal,
  onDelta: vi.fn(),
});

beforeEach(() => {
  vi.mocked(request).mockReset();
  clearSecurityTokens();
});
afterEach(() => clearSecurityTokens());

describe('AI remark streaming API', () => {
  it('uses the authenticated app request once with JSON, cancellation and retries disabled', async () => {
    respond(': keepalive\n\n' + frame({ type: 'result', document }));
    const config = options();
    await expect(generateRemarkAI(body, config)).resolves.toEqual(document);
    expect(request).toHaveBeenCalledTimes(1);
    expect(request).toHaveBeenCalledWith(
      expect.objectContaining({
        url: '/system/remark/ai/generate',
        method: 'post',
        data: body,
        headers: {
          Accept: 'text/event-stream',
          'Content-Type': 'application/json',
        },
        responseType: 'stream',
        signal: expect.any(AbortSignal),
        timeout: 0,
        silentSuccess: true,
        silentError: true,
      }),
      {
        isReturnNativeResponse: true,
        isTransformResponse: false,
        retry: false,
      }
    );
    expect(config.onDelta).not.toHaveBeenCalled();
  });

  it('decodes chunked UTF-8 events and only resolves after a valid final document', async () => {
    const bytes = new TextEncoder().encode(
      frame({ type: 'delta', text: '负责' }) +
        frame({ type: 'delta', text: '日常巡检。' }) +
        frame({ type: 'result', document })
    );
    const stream = new ReadableStream<Uint8Array>({
      start(controller) {
        for (let i = 0; i < bytes.length; i += 7) controller.enqueue(bytes.slice(i, i + 7));
        controller.close();
      },
    });
    vi.mocked(request).mockResolvedValue(response(stream));
    const config = options();
    await expect(generateRemarkAI(body, config)).resolves.toEqual(document);
    expect(config.onDelta.mock.calls).toEqual([['负责'], ['日常巡检。']]);
  });

  it('returns an in-stream error without accepting preview text or retrying', async () => {
    respond(
      frame({ type: 'delta', text: '不完整' }) +
        frame({
          type: 'error',
          code: 'provider_timeout',
          message: 'AI 响应超时，请重试',
        })
    );
    await expect(generateRemarkAI(body, options())).rejects.toMatchObject({
      code: 'provider_timeout',
      message: 'AI 响应超时，请重试',
    });
    expect(request).toHaveBeenCalledTimes(1);
  });

  it.each(['', frame({ type: 'delta', text: '未完成' }), 'data: {"type":"result"'])(
    'rejects incomplete streams (%j)',
    async (text) => {
      respond(text);
      await expect(generateRemarkAI(body, options())).rejects.toMatchObject({
        code: 'stream_interrupted',
      });
      expect(request).toHaveBeenCalledTimes(1);
    }
  );

  it.each([null, { version: 2 }, { ...document, assets: [{ id: 'unsupported' }] }])(
    'rejects results outside the shared remark policy',
    async (invalidDocument) => {
      respond(frame({ type: 'result', document: invalidDocument }));
      await expect(generateRemarkAI(body, options())).rejects.toMatchObject({
        code: 'invalid_result',
      });
    }
  );

  it('preserves normalized HTTP ProblemDetails and never reconnects a rejected request', async () => {
    const error = Object.assign(new Error('AI 服务尚未配置'), {
      status: 503,
      problem: { status: 503, detail: 'AI 服务尚未配置' },
    });
    vi.mocked(request).mockRejectedValue(error);
    await expect(generateRemarkAI(body, options())).rejects.toBe(error);
    expect(request).toHaveBeenCalledTimes(1);
  });

  it('fails a disconnected read instead of turning partial text into a result', async () => {
    let streamController!: ReadableStreamDefaultController<Uint8Array>;
    const stream = new ReadableStream<Uint8Array>({
      start(controller) {
        streamController = controller;
      },
    });
    vi.mocked(request).mockResolvedValue(response(stream));
    const config = options();
    const result = generateRemarkAI(body, config);
    const rejected = expect(result).rejects.toMatchObject({
      code: 'stream_interrupted',
    });
    streamController.enqueue(new TextEncoder().encode(frame({ type: 'delta', text: '草稿' })));
    await vi.waitFor(() => expect(config.onDelta).toHaveBeenCalledWith('草稿'));
    streamController.error(new Error('socket closed'));
    await rejected;
    expect(request).toHaveBeenCalledTimes(1);
  });

  it.each(['caller', 'session'] as const)(
    'cancels a live stream on %s invalidation',
    async (source) => {
      let streamController!: ReadableStreamDefaultController<Uint8Array>;
      const cancel = vi.fn();
      const stream = new ReadableStream<Uint8Array>({
        start(controller) {
          streamController = controller;
        },
        cancel,
      });
      vi.mocked(request).mockResolvedValue(response(stream));
      const caller = new AbortController();
      const onDelta = vi.fn();
      const result = generateRemarkAI(body, { signal: caller.signal, onDelta });
      const rejected = expect(result).rejects.toMatchObject({
        name: 'AbortError',
      });
      streamController.enqueue(new TextEncoder().encode(frame({ type: 'delta', text: '未完成' })));
      await vi.waitFor(() => expect(onDelta).toHaveBeenCalledOnce());
      if (source === 'caller') caller.abort();
      else clearSecurityTokens();
      await rejected;
      await vi.waitFor(() => expect(cancel).toHaveBeenCalledOnce());
      expect(request).toHaveBeenCalledTimes(1);
    }
  );

  it('does not send a request already cancelled by its caller', async () => {
    const caller = new AbortController();
    caller.abort();
    await expect(
      generateRemarkAI(body, { ...options(), signal: caller.signal })
    ).rejects.toMatchObject({ name: 'AbortError' });
    expect(request).not.toHaveBeenCalled();
  });

  it('closes the stream once the complete result is received', async () => {
    const cancel = vi.fn();
    const stream = new ReadableStream<Uint8Array>({
      start(controller) {
        controller.enqueue(new TextEncoder().encode(frame({ type: 'result', document })));
      },
      cancel,
    });
    vi.mocked(request).mockResolvedValue(response(stream));
    await expect(generateRemarkAI(body, options())).resolves.toEqual(document);
    await vi.waitFor(() => expect(cancel).toHaveBeenCalledOnce());
  });

  it('closes a still-open stream when a terminal error is received', async () => {
    const cancel = vi.fn();
    const stream = new ReadableStream<Uint8Array>({
      start(controller) {
        controller.enqueue(
          new TextEncoder().encode(frame({ type: 'error', code: 'failed', message: '生成失败' }))
        );
      },
      cancel,
    });
    vi.mocked(request).mockResolvedValue(response(stream));
    await expect(generateRemarkAI(body, options())).rejects.toMatchObject({ code: 'failed' });
    await vi.waitFor(() => expect(cancel).toHaveBeenCalledOnce());
  });

  it('checks availability through the same app request contract', async () => {
    vi.mocked(request).mockResolvedValue({ available: false });
    const signal = new AbortController().signal;
    await expect(getRemarkAIStatus({ signal })).resolves.toEqual({
      available: false,
    });
    expect(request).toHaveBeenCalledWith({
      url: '/system/remark/ai/status',
      method: 'get',
      signal,
      silentError: true,
    });
  });
});
