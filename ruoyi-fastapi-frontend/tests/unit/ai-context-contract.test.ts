import { readFileSync, readdirSync } from 'node:fs';
import { resolve } from 'node:path';
import Ajv2020 from 'ajv/dist/2020';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { AI_CONTEXT_PLACEHOLDER_GRAMMAR, AI_CONTEXT_VERSION } from '@zxio/zxui/ai-context';
import { validateBasicRichTextDocument } from '@zxio/text-editor/core';
import { generateTextFieldAI, type TextFieldAIRequest } from '@/api/system/textFieldAi';
import request from '@/utils/request';

vi.mock('@/utils/request', () => ({ default: vi.fn() }));
vi.mock('@/ai-context/definitions', async () => {
  const data = await import('../../../shared/ai-context/vectors/manifest-cases/valid.json');
  return {
    aiContextDefinitions: Object.fromEntries(
      Object.entries(data.default.value.scopes).map(([id, metadata]) => [id, { id, ...metadata }])
    ),
  };
});
const root = resolve(process.cwd(), '../shared/ai-context');
const read = (path: string) => JSON.parse(readFileSync(resolve(root, path), 'utf8'));
const ajv = new Ajv2020({ strict: false, allErrors: true });
ajv.addKeyword({
  keyword: 'x-codec',
  validate: (_schema: unknown, value: unknown) => {
    try {
      validateBasicRichTextDocument(value);
      return true;
    } catch {
      return false;
    }
  },
});
const body = read('vectors/request/draft.json').value as TextFieldAIRequest;
const options = () => ({ signal: new AbortController().signal, onDelta: vi.fn() });
beforeEach(() => {
  vi.mocked(request).mockReset();
});

describe('shared ai-context/v1 vectors', () => {
  for (const [folder, schema] of [
    ['request', 'request'],
    ['events', 'events'],
    ['manifest-cases', 'manifest'],
  ] as const) {
    const validate = ajv.compile(read(`${schema}.schema.json`));
    for (const name of readdirSync(resolve(root, 'vectors', folder)).filter((name) =>
      name.endsWith('.json')
    )) {
      const vector = read(`vectors/${folder}/${name}`);
      it(`${folder}/${name} agrees with the shared schema and actual document codec`, () => {
        expect(validate(vector.value), JSON.stringify(validate.errors)).toBe(vector.valid);
      });
    }
  }
  it('uses the public library grammar exactly', () => {
    expect({ version: AI_CONTEXT_VERSION, ...AI_CONTEXT_PLACEHOLDER_GRAMMAR }).toEqual(
      read('placeholder-grammar.json')
    );
    const pattern = new RegExp(AI_CONTEXT_PLACEHOLDER_GRAMMAR.wholePattern);
    for (const test of read('vectors/placeholders.json').cases)
      expect(pattern.test(test.value)).toBe(test.valid);
  });
  for (const test of read('vectors/http/errors.json').cases) {
    it(`HTTP ${test.status}/${test.aiCode ?? 'default'} maps before SSE starts`, async () => {
      const error = Object.assign(new Error('safe HTTP rejection'), {
        problem: test,
        meta: { retryAfter: Number(test.retryAfter) },
      });
      vi.mocked(request).mockRejectedValue(error);
      const promise = generateTextFieldAI(body, options());
      if (test.expected === 'authentication') await expect(promise).rejects.toBe(error);
      else
        await expect(promise).rejects.toMatchObject({
          code: test.expected,
          ...(test.retryAfter ? { retryAfter: Number(test.retryAfter) } : {}),
        });
      expect(request).toHaveBeenCalledTimes(1);
    });
  }
  for (const test of read('vectors/streams/boundaries.json').cases) {
    it(`actual SSE consumer: ${test.id}`, async () => {
      const text = test.events
        .map((event: unknown) => `event: message\ndata: ${JSON.stringify(event)}\n\n`)
        .join('');
      vi.mocked(request).mockResolvedValue({
        status: 200,
        headers: { 'content-type': 'text/event-stream' },
        data: new Response(text).body!,
      });
      const config = options();
      const caller = new AbortController();
      if (test.end === 'abort') caller.abort();
      const promise = generateTextFieldAI(body, { ...config, signal: caller.signal });
      if (test.expected === 'notice-only')
        await expect(promise).resolves.toMatchObject({
          document: null,
          notices: expect.any(Array),
        });
      else if (test.expected === 'cancelled')
        await expect(promise).rejects.toMatchObject({ name: 'AbortError' });
      else await expect(promise).rejects.toMatchObject({ code: test.expected });
      expect(request).toHaveBeenCalledTimes(test.end === 'abort' ? 0 : 1);
    });
  }
});
