import { afterEach, describe, expect, it, vi } from 'vitest';
import { HttpResponse } from 'msw';

import { withBackendFallback } from './with-backend-fallback';

describe('withBackendFallback', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('returns mock response directly in pure strategy', async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal('fetch', fetchMock);

    const response = await withBackendFallback(
      new Request('http://localhost/api/demo'),
      () => HttpResponse.json({ ok: true }),
      { strategy: 'pure', tag: 'demo' }
    );

    expect(fetchMock).not.toHaveBeenCalled();
    expect(response.headers.get('X-Mock-Mode')).toBe('pure');
    await expect(response.json()).resolves.toEqual({ ok: true });
  });

  it('passes through upstream success in fallback strategy', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(HttpResponse.json({ upstream: true })));

    const response = await withBackendFallback(
      new Request('http://localhost/api/demo'),
      () => HttpResponse.json({ mock: true }),
      { strategy: 'fallback' }
    );

    expect(response.headers.get('X-Mock-Response')).toBeNull();
    await expect(response.json()).resolves.toEqual({ upstream: true });
  });

  it('falls back on upstream 404 and network errors', async () => {
    const request = new Request('http://localhost/api/demo');
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(new Response(null, { status: 404 }))
      .mockRejectedValueOnce(new Error('network'));
    vi.stubGlobal('fetch', fetchMock);

    const notFoundFallback = await withBackendFallback(
      request,
      () => HttpResponse.json({ mock: 'not-found' }),
      { strategy: 'fallback', tag: 'fallback' }
    );
    const networkFallback = await withBackendFallback(
      request,
      () => HttpResponse.json({ mock: 'network' }),
      { strategy: 'fallback', tag: 'fallback' }
    );

    expect(notFoundFallback.headers.get('X-Mock-Handler')).toBe('fallback');
    await expect(notFoundFallback.json()).resolves.toEqual({ mock: 'not-found' });
    await expect(networkFallback.json()).resolves.toEqual({ mock: 'network' });
  });
});
