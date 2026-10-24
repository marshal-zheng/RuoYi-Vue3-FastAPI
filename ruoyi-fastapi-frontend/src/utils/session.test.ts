import axios, { AxiosError, type AxiosAdapter, type InternalAxiosRequestConfig } from 'axios';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { createHttpClient } from '@zxio/http';
import { createSessionTransport } from './session';
import { clearSecurityTokens, getCsrfToken, getToken, setCsrfToken, setToken } from './auth';
import { endQuerySession, scopeRequestOptions, setQuerySession } from '@/queries/context';

const jwt = (seconds: number) =>
  `header.${btoa(JSON.stringify({ exp: Date.now() / 1000 + seconds }))}.signature`;
const response = (config: InternalAxiosRequestConfig, data: unknown, status = 200) => ({
  config,
  data,
  status,
  statusText: '',
  headers: {},
});
const rejected = (config: InternalAxiosRequestConfig, status = 401) =>
  new AxiosError(
    'rejected',
    'ERR_BAD_REQUEST',
    config,
    undefined,
    response(config, { status }, status)
  );
const deferred = () => {
  let resolve!: () => void;
  const promise = new Promise<void>((done) => {
    resolve = done;
  });
  return { promise, resolve };
};

let transport: ReturnType<typeof createSessionTransport>;
let send: ReturnType<typeof vi.fn<AxiosAdapter>>;
let refreshes: number;
let business: InternalAxiosRequestConfig[];
let refreshGate: ReturnType<typeof deferred> | undefined;
let refreshStatus: number;
let attempt: (config: InternalAxiosRequestConfig) => Promise<unknown>;
const originalAdapter = axios.defaults.adapter;

const client = () =>
  createHttpClient({
    axiosConfig: { adapter: transport.adapter },
    tokenProvider: { getToken: () => getToken() || '' },
    successResolver: ({ response: result }) => ({
      ok: true,
      data: result.data,
    }),
  });

beforeEach(() => {
  clearSecurityTokens();
  document.cookie = 'csrf_token=; Max-Age=0; path=/';
  setToken(jwt(3600));
  setCsrfToken('old-csrf');
  refreshes = 0;
  business = [];
  refreshGate = undefined;
  refreshStatus = 200;
  attempt = async () => undefined;
  send = vi.fn(async (config: InternalAxiosRequestConfig) => {
    if (config.url === '/auth/refresh') {
      refreshes++;
      await refreshGate?.promise;
      if (refreshStatus !== 200) throw rejected(config, refreshStatus);
      return response(config, { token: jwt(7200), csrfToken: 'new-csrf' });
    }
    business.push({ ...config, headers: config.headers.concat() });
    await attempt(config);
    return response(config, { ok: true });
  });
  axios.defaults.adapter = send;
  transport = createSessionTransport(vi.fn());
});

afterEach(() => {
  vi.unstubAllGlobals();
  axios.defaults.adapter = originalAdapter;
  clearSecurityTokens();
  endQuerySession();
});

describe('browser session renewal', () => {
  it('renews expired access before concurrent writes and dispatches each body once', async () => {
    setToken(jwt(-10));
    const http = client();
    await Promise.all([
      http.post({ url: '/users', data: { id: 1 } }),
      http.post({ url: '/users', data: { id: 2 } }),
    ]);
    expect(refreshes).toBe(1);
    expect(business.map((config) => config.data)).toEqual(['{"id":1}', '{"id":2}']);
    expect(business.every((config) => config.headers.get('X-CSRF-Token') === 'new-csrf')).toBe(
      true
    );
  });

  it('coalesces concurrent 401s and reuses the new token for late old-token failures', async () => {
    const old = getToken();
    const late = deferred();
    attempt = async (config) => {
      if (config.headers.get('Authorization') === `Bearer ${old}`) {
        if (config.url === '/late') await late.promise;
        throw rejected(config);
      }
    };
    const http = client();
    const last = http.get({ url: '/late' });
    await Promise.all([http.get({ url: '/one' }), http.get({ url: '/two' })]);
    late.resolve();
    await last;
    expect(refreshes).toBe(1);
    expect(business.filter((config) => config.url === '/late')).toHaveLength(2);
  });

  it('preserves the serialized FormData body across one explicit 401', async () => {
    const old = getToken();
    const data = new FormData();
    data.set('file', new File(['qa'], 'qa.txt'));
    attempt = async (config) => {
      if (config.headers.get('Authorization') === `Bearer ${old}`) throw rejected(config);
    };
    await client().post({ url: '/upload', data });
    expect(business).toHaveLength(2);
    expect(business[0].data).toBe(data);
    expect(business[1].data).toBe(data);
    expect(refreshes).toBe(1);
  });

  it('does not loop after the replay is also unauthorized', async () => {
    attempt = async (config) => {
      throw rejected(config);
    };
    await expect(client().get({ url: '/denied' })).rejects.toMatchObject({
      status: 401,
    });
    expect(business).toHaveLength(2);
    expect(refreshes).toBe(1);
  });

  it('keeps a terminal refresh rejection associated with the business request', async () => {
    setToken(jwt(-5));
    refreshStatus = 401;
    await expect(client().post({ url: '/write', data: {} })).rejects.toMatchObject({
      status: 401,
      config: { url: '/write' },
    });
    expect(business).toHaveLength(0);
    expect(refreshes).toBe(1);
  });

  it('returns the original 401 when refresh is revoked', async () => {
    refreshStatus = 401;
    attempt = async (config) => {
      throw rejected(config);
    };
    await expect(client().get({ url: '/revoked' })).rejects.toMatchObject({
      status: 401,
    });
    expect(business).toHaveLength(1);
    expect(refreshes).toBe(1);
  });

  it.each([403, 500])('never refreshes or repeats a %i failure', async (status) => {
    attempt = async (config) => {
      throw rejected(config, status);
    };
    await expect(client().post({ url: '/write', data: {} })).rejects.toMatchObject({ status });
    expect(refreshes).toBe(0);
    expect(business).toHaveLength(1);
  });

  it('does not repeat a mutation after a network failure', async () => {
    attempt = async (config) => {
      throw new AxiosError('network', 'ERR_NETWORK', config);
    };
    await expect(client().post({ url: '/write', data: {} })).rejects.toThrow();
    expect(refreshes).toBe(0);
    expect(business).toHaveLength(1);
  });

  it('does not renew explicitly anonymous or auth endpoint requests', async () => {
    setToken(jwt(-5));
    await client().get({ url: '/public' }, { withToken: false });
    await client().post({ url: '/auth/logout' });
    expect(refreshes).toBe(0);
  });

  it('cancels one waiter without cancelling the shared refresh for another request', async () => {
    setToken(jwt(-5));
    refreshGate = deferred();
    const controller = new AbortController();
    const http = client();
    const first = http.get({ url: '/cancelled', signal: controller.signal });
    const second = http.get({ url: '/active' });
    await vi.waitFor(() => expect(refreshes).toBe(1));
    controller.abort();
    await expect(first).rejects.toMatchObject({ name: 'AbortError' });
    refreshGate.resolve();
    await second;
    expect(business.map((config) => config.url)).toEqual(['/active']);
  });

  it('does not dispatch a request whose query scope ended during refresh', async () => {
    setToken(jwt(-5));
    refreshGate = deferred();
    const scope = setQuerySession('1', ['admin'], []);
    const result = client().get({ url: '/old-scope' }, scopeRequestOptions(scope));
    await vi.waitFor(() => expect(refreshes).toBe(1));
    endQuerySession();
    refreshGate.resolve();
    await expect(result).rejects.toMatchObject({ name: 'AbortError' });
    expect(business).toHaveLength(0);
  });

  it('does not restore local credentials after logout or a replacement login', async () => {
    setToken(jwt(-5));
    refreshGate = deferred();
    const result = client().get({ url: '/old-session' });
    await vi.waitFor(() => expect(refreshes).toBe(1));
    clearSecurityTokens();
    setToken('replacement-login-token');
    refreshGate.resolve();
    await expect(result).rejects.toMatchObject({ name: 'AbortError' });
    expect(getToken()).toBe('replacement-login-token');
    expect(business).toHaveLength(0);
  });

  it('aborts the refresh network request when the security session ends', async () => {
    refreshGate = deferred();
    const result = transport.refresh().catch((error: unknown) => error);
    await vi.waitFor(() => expect(refreshes).toBe(1));
    const refreshConfig = send.mock.calls.find(([config]) => config.url === '/auth/refresh')![0];
    clearSecurityTokens();
    const aborted = refreshConfig.signal?.aborted;
    refreshGate.resolve();
    await result;
    // Ignoring the response body cannot stop its Set-Cookie headers; cancel the transport too.
    expect(aborted).toBe(true);
  });

  it('prefers the current CSRF cookie after rotation by another tab', () => {
    document.cookie = 'csrf_token=other-tab-csrf; path=/';
    expect(getCsrfToken()).toBe('other-tab-csrf');
  });

  it('uses the fetch adapter for streams and preserves authentication, JSON and cancellation after headers', async () => {
    const caller = new AbortController();
    let sent!: Request;
    const fetch = vi.fn<typeof globalThis.fetch>(async (input) => {
      sent = input as Request;
      const stream = new ReadableStream<Uint8Array>({
        start(controller) {
          sent.signal.addEventListener('abort', () =>
            controller.error(new DOMException('Cancelled', 'AbortError'))
          );
        },
      });
      return new Response(stream, {
        headers: { 'content-type': 'text/event-stream' },
      });
    });
    vi.stubGlobal('fetch', fetch);
    const result = await client().post<ReadableStream<Uint8Array>>({
      url: 'https://api.test/remark',
      data: { instruction: '润色备注' },
      responseType: 'stream',
      signal: caller.signal,
    });
    expect(fetch).toHaveBeenCalledOnce();
    expect(business).toHaveLength(0);
    expect(sent.headers.get('Authorization')).toBe(`Bearer ${getToken()}`);
    expect(sent.headers.get('X-CSRF-Token')).toBe('old-csrf');
    expect(await sent.text()).toBe('{"instruction":"润色备注"}');
    expect(sent.signal.aborted).toBe(false);
    const reader = result.getReader();
    const read = expect(reader.read()).rejects.toMatchObject({ name: 'AbortError' });
    caller.abort();
    expect(sent.signal.aborted).toBe(true);
    await read;
    reader.releaseLock();
  });

  it('refreshes one explicit pre-stream 401 and replays the same body with rotated credentials', async () => {
    const sent: Request[] = [];
    const fetch = vi.fn<typeof globalThis.fetch>(async (input) => {
      sent.push(input as Request);
      if (sent.length === 1) {
        return new Response(JSON.stringify({ status: 401, detail: '会话已过期' }), {
          status: 401,
          headers: { 'content-type': 'application/problem+json' },
        });
      }
      return new Response('data: {"type":"result"}\n\n', {
        headers: { 'content-type': 'text/event-stream' },
      });
    });
    vi.stubGlobal('fetch', fetch);
    const result = await client().post<ReadableStream<Uint8Array>>({
      url: 'https://api.test/remark',
      data: { instruction: '润色备注' },
      responseType: 'stream',
    });
    expect(refreshes).toBe(1);
    expect(fetch).toHaveBeenCalledTimes(2);
    expect(await sent[0].text()).toBe(await sent[1].text());
    expect(sent[0].headers.get('X-CSRF-Token')).toBe('old-csrf');
    expect(sent[1].headers.get('X-CSRF-Token')).toBe('new-csrf');
    expect(sent[1].headers.get('Authorization')).toBe(`Bearer ${getToken()}`);
    await result.cancel();
  });

  it('decodes streaming ProblemDetails without refreshing or retrying non-auth failures', async () => {
    const fetch = vi.fn<typeof globalThis.fetch>(
      async () =>
        new Response(JSON.stringify({ status: 503, detail: 'AI 服务尚未配置' }), {
          status: 503,
          headers: { 'content-type': 'application/problem+json' },
        })
    );
    vi.stubGlobal('fetch', fetch);
    await expect(
      client().post({
        url: 'https://api.test/remark',
        responseType: 'stream',
      })
    ).rejects.toMatchObject({
      status: 503,
      data: { detail: 'AI 服务尚未配置' },
    });
    expect(fetch).toHaveBeenCalledOnce();
    expect(refreshes).toBe(0);
  });
});
