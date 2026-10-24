import { describe, expect, it } from 'vitest';
import { http, HttpResponse } from 'msw';
import { createApiPath } from '@/mocks/constants';
import { setupMainlineMockHandlers } from '../../../tests/mocks/mainline';
import { mockServer } from '../../../tests/mocks/server';
import { exportProtocol } from './protocol';

describe('protocol export wire contract', () => {
  setupMainlineMockHandlers();

  it('submits the real Form parameter and decodes the XLSX response as binary', async () => {
    // High-byte preservation is covered by the isolated native-browser XHR probe;
    // MSW's jsdom XHR shim routes response bytes through UTF-8 text.
    const bytes = new Uint8Array([80, 75, 3, 4, 0, 1, 2]);
    let contentType = '';
    let body = '';
    mockServer.use(
      http.post(createApiPath('/system/protocol/export'), async ({ request }) => {
        contentType = request.headers.get('content-type') ?? '';
        body = await request.text();
        if (!contentType.startsWith('application/x-www-form-urlencoded')) {
          return HttpResponse.json(
            { detail: 'protocolId Form field is required' },
            { status: 422 }
          );
        }
        expect(new URLSearchParams(body).get('protocolId')).toBe('7');
        return new HttpResponse(bytes, {
          headers: {
            'content-type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
          },
        });
      })
    );

    const result = await exportProtocol({ protocolId: 7 });

    expect(contentType).toContain('application/x-www-form-urlencoded');
    expect(body).toBe('protocolId=7');
    expect(result).toBeInstanceOf(Blob);
    expect(result.size).toBe(bytes.byteLength);
    expect(result.type).toBe('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
  });
});
