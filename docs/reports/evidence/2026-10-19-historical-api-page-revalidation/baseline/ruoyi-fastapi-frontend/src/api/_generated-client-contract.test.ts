import { describe, expect, expectTypeOf, it, vi } from 'vitest';
import { createClient } from './_generated/client/client.gen';
import { createSseClient, type StreamEvent } from './_generated/core/serverSentEvents.gen';

interface Resource {
  id: number;
  name: string;
}
interface ApiError {
  code: string;
}

describe('generated Fetch SDK transport contract', () => {
  it('retains data and error generics through public methods in fields mode', async () => {
    const fetch = vi
      .fn<typeof globalThis.fetch>()
      .mockResolvedValue(Response.json({ id: 7, name: 'HTTP' }));
    const client = createClient({ baseUrl: 'https://sdk.test', fetch });
    const result = await client.get<Resource, ApiError, false, 'fields'>({
      url: '/resources/{id}',
      path: { id: 7 },
      query: { name: 'two words' },
      responseStyle: 'fields',
    });
    expectTypeOf(result.data).toEqualTypeOf<Resource | undefined>();
    expectTypeOf(result.error).toEqualTypeOf<ApiError | undefined>();
    expect(result).toMatchObject({ data: { id: 7, name: 'HTTP' }, error: undefined });
    expect(result.request).toBeInstanceOf(Request);
    expect(result.response).toBeInstanceOf(Response);
    const request = fetch.mock.calls[0][0];
    expect(request).toBeInstanceOf(Request);
    if (!(request instanceof Request)) throw new TypeError('SDK must submit a Request');
    const url = new URL(request.url);
    expect(url.pathname).toBe('/resources/7');
    expect(url.searchParams.get('name')).toBe('two words');
  });

  it('retains the response generic in data mode with throwOnError', async () => {
    const fetch = vi
      .fn<typeof globalThis.fetch>()
      .mockResolvedValue(Response.json({ id: 8, name: 'UDP' }));
    const client = createClient({ baseUrl: 'https://sdk.test', fetch });
    const result = await client.post<Resource, ApiError, true, 'data'>({
      url: '/resources',
      body: { name: 'UDP' },
      throwOnError: true,
      responseStyle: 'data',
    });
    expectTypeOf(result).toEqualTypeOf<Resource>();
    expect(result).toEqual({ id: 8, name: 'UDP' });
    const request = fetch.mock.calls[0][0];
    if (!(request instanceof Request)) throw new TypeError('SDK must submit a Request');
    expect(await request.json()).toEqual({ name: 'UDP' });
  });

  it.each(['data', 'fields'] as const)(
    'parses a 204 response without attempting JSON in %s mode',
    async (responseStyle) => {
      const fetch = vi
        .fn<typeof globalThis.fetch>()
        .mockResolvedValue(new Response(null, { status: 204 }));
      const client = createClient({ baseUrl: 'https://sdk.test', fetch });
      const result = await client.delete<null, ApiError, false, typeof responseStyle>({
        url: '/resources/7',
        responseStyle,
      });
      if (responseStyle === 'data') expect(result).toBeNull();
      else expect(result).toMatchObject({ data: null, error: undefined });
    }
  );

  it.each(['data', 'fields'] as const)(
    'returns parsed failure details in %s mode',
    async (responseStyle) => {
      const fetch = vi
        .fn<typeof globalThis.fetch>()
        .mockResolvedValue(Response.json({ code: 'MISSING' }, { status: 404 }));
      const client = createClient({ baseUrl: 'https://sdk.test', fetch });
      const result = await client.get<Resource, ApiError, false, typeof responseStyle>({
        url: '/resources/7',
        responseStyle,
      });
      if (responseStyle === 'data') expect(result).toBeUndefined();
      else expect(result).toMatchObject({ data: undefined, error: { code: 'MISSING' } });
    }
  );

  it.each(['data', 'fields'] as const)(
    'rejects failures when throwOnError is enabled in %s mode',
    async (responseStyle) => {
      const fetch = vi
        .fn<typeof globalThis.fetch>()
        .mockResolvedValue(Response.json({ code: 'MISSING' }, { status: 404 }));
      const client = createClient({ baseUrl: 'https://sdk.test', fetch });
      await expect(
        client.get<Resource, ApiError, true, typeof responseStyle>({
          url: '/resources/7',
          responseStyle,
          throwOnError: true,
        })
      ).rejects.toEqual({ code: 'MISSING' });
    }
  );

  it('parses an empty 200 JSON body and forwards a transformed validated response', async () => {
    const fetch = vi
      .fn<typeof globalThis.fetch>()
      .mockResolvedValue(new Response('', { headers: { 'content-type': 'application/json' } }));
    const validate = vi.fn().mockResolvedValue(undefined);
    const transform = vi.fn().mockResolvedValue({ id: 9, name: 'TCP' });
    const client = createClient({ baseUrl: 'https://sdk.test', fetch });
    await expect(
      client.get<Resource, ApiError, true, 'data'>({
        url: '/resources/9',
        responseStyle: 'data',
        throwOnError: true,
        responseValidator: validate,
        responseTransformer: transform,
      })
    ).resolves.toEqual({ id: 9, name: 'TCP' });
    expect(validate).toHaveBeenCalledWith({});
    expect(transform).toHaveBeenCalledWith({});
  });
  it('types SSE event data separately from normal void completion', async () => {
    const fetch = vi.fn<typeof globalThis.fetch>().mockResolvedValue(
      new Response('data: {"id":10,"name":"SSE"}\n\n', {
        headers: { 'content-type': 'text/event-stream' },
      })
    );
    const client = createClient({ baseUrl: 'https://sdk.test', fetch });
    const { stream } = await client.sse.get<Resource>({
      url: '/events',
      sseMaxRetryAttempts: 1,
    });
    const event = await stream.next();
    expect(event).toMatchObject({ done: false, value: { id: 10, name: 'SSE' } });
    expectTypeOf(event.value).toEqualTypeOf<Resource | void>();
    expect(await stream.next()).toEqual({ done: true, value: undefined });
  });

  it('propagates a status-mapped SSE payload to callbacks and the generator', async () => {
    const fetch = vi.fn<typeof globalThis.fetch>().mockResolvedValue(
      new Response('data: {"id":11,"name":"Mapped SSE"}\n\n', {
        headers: { 'content-type': 'text/event-stream' },
      })
    );
    const events: StreamEvent<Resource>[] = [];
    const client = createClient({ baseUrl: 'https://sdk.test', fetch });
    const { stream } = await client.sse.get<{ 200: Resource }>({
      url: '/events',
      sseMaxRetryAttempts: 1,
      onSseEvent(event) {
        expectTypeOf(event.data).toEqualTypeOf<Resource>();
        events.push(event);
      },
    });
    const event = await stream.next();
    expectTypeOf(event.value).toEqualTypeOf<Resource | void>();
    expect(events[0].data).toEqual({ id: 11, name: 'Mapped SSE' });
    expect(event).toMatchObject({ done: false, value: events[0].data });
    expect(await stream.next()).toEqual({ done: true, value: undefined });
  });

  it('propagates standalone SSE resource data to the public callback', async () => {
    const fetch = vi.fn<typeof globalThis.fetch>().mockResolvedValue(
      new Response('data: {"id":12,"name":"Direct SSE"}\n\n', {
        headers: { 'content-type': 'text/event-stream' },
      })
    );
    const events: StreamEvent<Resource>[] = [];
    const { stream } = createSseClient<Resource>({
      url: 'https://sdk.test/events',
      fetch,
      sseMaxRetryAttempts: 1,
      onSseEvent(event) {
        expectTypeOf(event.data).toEqualTypeOf<Resource>();
        events.push(event);
      },
    });
    expect(await stream.next()).toMatchObject({
      done: false,
      value: { id: 12, name: 'Direct SSE' },
    });
    expect(events[0].data.id).toBe(12);
    expect(await stream.next()).toEqual({ done: true, value: undefined });
  });

  it('keeps control-only SSE frames out of data callbacks while retaining their metadata', async () => {
    const fetch = vi.fn<typeof globalThis.fetch>().mockResolvedValue(
      new Response('id: resume-7\nretry: 1500\n\ndata: {"id":13,"name":"Controlled SSE"}\n\n', {
        headers: { 'content-type': 'text/event-stream' },
      })
    );
    const onSseEvent = vi.fn();
    const client = createClient({ baseUrl: 'https://sdk.test', fetch });
    const { stream } = await client.sse.get<{ 200: Resource }>({
      url: '/events',
      sseMaxRetryAttempts: 1,
      onSseEvent,
    });
    expect(await stream.next()).toMatchObject({
      done: false,
      value: { id: 13, name: 'Controlled SSE' },
    });
    expect(onSseEvent).toHaveBeenCalledTimes(1);
    expect(onSseEvent).toHaveBeenCalledWith({
      data: { id: 13, name: 'Controlled SSE' },
      event: undefined,
      id: 'resume-7',
      retry: 1500,
    });
    expect(await stream.next()).toEqual({ done: true, value: undefined });
  });

  it('keeps SSE validator failures unknown and normal completion void', async () => {
    const fetch = vi
      .fn<typeof globalThis.fetch>()
      .mockResolvedValue(
        new Response('data: {}\n\n', { headers: { 'content-type': 'text/event-stream' } })
      );
    const onSseError = vi.fn<(error: unknown) => void>();
    const client = createClient({ baseUrl: 'https://sdk.test', fetch });
    const { stream } = await client.sse.get<Resource>({
      url: '/events',
      sseMaxRetryAttempts: 1,
      onSseError,
      responseValidator: async () => {
        throw { code: 'INVALID' };
      },
    });
    expect(await stream.next()).toEqual({ done: true, value: undefined });
    expect(onSseError).toHaveBeenCalledWith({ code: 'INVALID' });
  });
  it('returns null for explicit JSON 204 without changing empty 200 JSON semantics', async () => {
    const fetch = vi
      .fn<typeof globalThis.fetch>()
      .mockResolvedValueOnce(new Response(null, { status: 204 }))
      .mockResolvedValueOnce(
        new Response('', { headers: { 'content-type': 'application/json', 'content-length': '0' } })
      );
    const client = createClient({ baseUrl: 'https://sdk.test', fetch });
    await expect(
      client.delete<null, ApiError, true, 'data'>({
        url: '/resources/7',
        parseAs: 'json',
        responseStyle: 'data',
        throwOnError: true,
      })
    ).resolves.toBeNull();
    await expect(
      client.get<unknown, ApiError, true, 'data'>({
        url: '/resources/7',
        parseAs: 'json',
        responseStyle: 'data',
        throwOnError: true,
      })
    ).resolves.toEqual({});
  });
  it('preserves native network errors in the unknown SSE error hook', async () => {
    const error = new TypeError('network offline');
    const fetch = vi.fn<typeof globalThis.fetch>().mockRejectedValue(error);
    const onSseError = vi.fn<(error: unknown) => void>();
    const client = createClient({ baseUrl: 'https://sdk.test', fetch });
    const { stream } = await client.sse.get<Resource>({
      url: '/events',
      sseMaxRetryAttempts: 1,
      onSseError,
    });
    expect(await stream.next()).toEqual({ done: true, value: undefined });
    expect(onSseError).toHaveBeenCalledWith(error);
    expect(onSseError.mock.calls[0][0]).toBeInstanceOf(TypeError);
  });

  it('preserves non-2xx HTTP transport errors in the unknown SSE error hook', async () => {
    const fetch = vi
      .fn<typeof globalThis.fetch>()
      .mockResolvedValue(
        new Response('unavailable', { status: 503, statusText: 'Service Unavailable' })
      );
    const onSseError = vi.fn<(error: unknown) => void>();
    const client = createClient({ baseUrl: 'https://sdk.test', fetch });
    const { stream } = await client.sse.get<Resource>({
      url: '/events',
      sseMaxRetryAttempts: 1,
      onSseError,
    });
    expect(await stream.next()).toEqual({ done: true, value: undefined });
    const error = onSseError.mock.calls[0][0];
    expect(error).toBeInstanceOf(Error);
    if (!(error instanceof Error))
      throw new TypeError('HTTP stream failures must remain Error instances');
    expect(error.message).toContain('503');
  });
});
