import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { AxiosResponse } from 'axios';
import { clearSecurityTokens } from '@/utils/auth';
import { mockRemark } from '@/mocks/data/remark';
import request from '@/utils/request';
import { generateTextFieldAI, getTextFieldAIStatus, type TextFieldAIRequest } from './textFieldAi';

vi.mock('@/utils/request', () => ({ default: vi.fn() }));
const body: TextFieldAIRequest = {
  version: 'ai-context/v1',
  requestId: '12345678-1234-4234-8234-123456789abc',
  captureId: '22345678-1234-4234-8234-123456789abc',
  manifestRevision: 'a'.repeat(64),
  policyRevision: 'b'.repeat(64),
  scope: 'system.post',
  purpose: 'remark',
  action: 'draft',
  selectedContextIds: [],
  profile: 'basic-rich-text',
  instruction: '整理为岗位说明',
  target: 'document',
  document: null,
  selection: null,
  candidate: null,
  context: [{ id: 'postName', label: '岗位名称', sensitivity: 'public', value: '巡检员' }],
};
const document = mockRemark('负责日常巡检。', 'ai');
const result = {
  document,
  notices: [],
  meta: { promptVersion: 'text-field/v1', model: 'local-model', contextIds: ['postName'] },
};
const event = (data: Record<string, unknown>) => ({
  requestId: body.requestId,
  captureId: body.captureId,
  ...data,
});
const frame = (data: Record<string, unknown>) =>
  `event: message\ndata: ${JSON.stringify(event(data))}\n\n`;
const final = () => frame({ type: 'result', ...result });
const response = (data: ReadableStream<Uint8Array>) =>
  ({
    data,
    status: 200,
    headers: { 'content-type': 'text/event-stream; charset=utf-8' },
  }) as AxiosResponse<ReadableStream<Uint8Array>>;
const respond = (text: string) =>
  vi.mocked(request).mockResolvedValue(response(new Response(text).body!));
const options = () => ({ signal: new AbortController().signal, onDelta: vi.fn() });
beforeEach(() => {
  vi.mocked(request).mockReset();
  clearSecurityTokens();
});
afterEach(() => clearSecurityTokens());

describe('field AI HTTP and SSE boundary', () => {
  it('uses the authenticated app request exactly once with retries disabled', async () => {
    respond(': keepalive\n\n' + final());
    await expect(generateTextFieldAI(body, options())).resolves.toEqual(result);
    expect(request).toHaveBeenCalledTimes(1);
    expect(request).toHaveBeenCalledWith(
      expect.objectContaining({
        url: '/system/ai/text-field/generate',
        method: 'post',
        data: body,
        responseType: 'stream',
        signal: expect.any(AbortSignal),
        timeout: 0,
      }),
      { isReturnNativeResponse: true, isTransformResponse: false, retry: false }
    );
  });
  it('decodes arbitrary UTF-8 chunk boundaries', async () => {
    const bytes = new TextEncoder().encode(frame({ type: 'delta', text: '负责😀' }) + final());
    const stream = new ReadableStream<Uint8Array>({
      start(controller) {
        for (let i = 0; i < bytes.length; i += 7) controller.enqueue(bytes.slice(i, i + 7));
        controller.close();
      },
    });
    vi.mocked(request).mockResolvedValue(response(stream));
    const config = options();
    await expect(generateTextFieldAI(body, config)).resolves.toEqual(result);
    expect(config.onDelta.mock.calls).toEqual([['负责😀']]);
  });
  it('waits for normal EOF after a terminal result', async () => {
    let controller!: ReadableStreamDefaultController<Uint8Array>;
    vi.mocked(request).mockResolvedValue(
      response(
        new ReadableStream({
          start(value) {
            controller = value;
          },
        })
      )
    );
    let settled = false;
    const promise = generateTextFieldAI(body, options()).finally(() => {
      settled = true;
    });
    controller.enqueue(new TextEncoder().encode(final()));
    await new Promise((resolve) => setTimeout(resolve, 20));
    expect(settled).toBe(false);
    controller.close();
    await expect(promise).resolves.toEqual(result);
  });
  it.each([
    final() + final(),
    final() + frame({ type: 'delta', text: 'late' }),
    frame({ type: 'error', code: 'timeout', message: 'safe' }) + final(),
    frame({ type: 'result', ...result, requestId: body.captureId }),
    frame({ type: 'result', ...result, captureId: body.requestId }),
    frame({ type: 'result', ...result, meta: { ...result.meta, contextIds: [] } }),
    frame({ type: 'result', document: null, notices: [], meta: result.meta }),
    frame({
      type: 'result',
      ...result,
      notices: [{ code: 'information-unavailable', contextIds: ['password'] }],
    }),
    'data: {not-json}\n\n',
  ])('rejects invalid sequences/envelopes without adopting or replaying', async (text) => {
    respond(text);
    await expect(generateTextFieldAI(body, options())).rejects.toMatchObject({
      code: 'invalid-output',
    });
    expect(request).toHaveBeenCalledTimes(1);
  });
  it.each(['', frame({ type: 'delta', text: '未完成' })])(
    'rejects EOF without terminal',
    async (text) => {
      respond(text);
      await expect(generateTextFieldAI(body, options())).rejects.toMatchObject({
        code: 'invalid-output',
      });
    }
  );
  it('accepts notice-only and uses finite error text for upstream failures', async () => {
    const notices = [{ code: 'information-unavailable', contextIds: ['postCode'] }];
    respond(frame({ type: 'result', ...result, document: null, notices }));
    await expect(generateTextFieldAI(body, options())).resolves.toEqual({
      ...result,
      document: null,
      notices,
    });
    respond(frame({ type: 'error', code: 'provider-unavailable', message: 'PRIVATE-SDK-ERROR' }));
    await expect(generateTextFieldAI(body, options())).rejects.toMatchObject({
      code: 'provider-unavailable',
    });
    await expect(generateTextFieldAI(body, options())).rejects.not.toHaveProperty(
      'message',
      'PRIVATE-SDK-ERROR'
    );
  });
  it.each([
    [403, 'policy-rejected'],
    [403, 'permission-denied'],
    [422, 'context-rejected'],
    [429, 'quota-exceeded'],
    [503, 'provider-unavailable'],
  ] as const)('maps HTTP %s / %s separately from SSE', async (status, aiCode) => {
    vi.mocked(request).mockRejectedValue(
      Object.assign(new Error('PRIVATE-HTTP'), { problem: { status, aiCode } })
    );
    await expect(generateTextFieldAI(body, options())).rejects.toMatchObject({ code: aiCode });
    expect(request).toHaveBeenCalledTimes(1);
  });
  it('leaves login failures to the app auth boundary', async () => {
    const error = Object.assign(new Error('login required'), { problem: { status: 401 } });
    vi.mocked(request).mockRejectedValue(error);
    await expect(generateTextFieldAI(body, options())).rejects.toBe(error);
  });
  it.each(['caller', 'session'] as const)(
    'cancels a live stream on %s invalidation',
    async (source) => {
      let controller!: ReadableStreamDefaultController<Uint8Array>;
      const cancel = vi.fn();
      vi.mocked(request).mockResolvedValue(
        response(
          new ReadableStream({
            start(value) {
              controller = value;
            },
            cancel,
          })
        )
      );
      const caller = new AbortController();
      const onDelta = vi.fn();
      const promise = generateTextFieldAI(body, { signal: caller.signal, onDelta });
      const rejected = expect(promise).rejects.toMatchObject({ name: 'AbortError' });
      controller.enqueue(new TextEncoder().encode(frame({ type: 'delta', text: '未完成' })));
      await vi.waitFor(() => expect(onDelta).toHaveBeenCalledOnce());
      if (source === 'caller') caller.abort();
      else clearSecurityTokens();
      await rejected;
      await vi.waitFor(() => expect(cancel).toHaveBeenCalledOnce());
      expect(request).toHaveBeenCalledTimes(1);
    }
  );
  it('does not dispatch an already cancelled request', async () => {
    const caller = new AbortController();
    caller.abort();
    await expect(
      generateTextFieldAI(body, { ...options(), signal: caller.signal })
    ).rejects.toMatchObject({ name: 'AbortError' });
    expect(request).not.toHaveBeenCalled();
  });
  it('loads status through the app HTTP contract', async () => {
    vi.mocked(request).mockResolvedValue({ available: false });
    const signal = new AbortController().signal;
    await expect(getTextFieldAIStatus({ signal })).resolves.toEqual({ available: false });
    expect(request).toHaveBeenCalledWith({
      url: '/system/ai/text-field/status',
      method: 'get',
      signal,
      silentError: true,
    });
  });
});
