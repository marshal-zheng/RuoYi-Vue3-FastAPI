import { describe, expect, it } from 'vitest';

import { createReadonlyOverlayDataSource } from './handlers';
import { setupOverlayMockHandlers } from '../../../tests/mocks/overlays';

async function responseJson(response: Response) {
  return response.json() as Promise<Record<string, unknown>>;
}

describe('mock overlay handlers', () => {
  const context = setupOverlayMockHandlers();

  it('returns schema-compatible empty page projections with overlay headers', async () => {
    context.activateOverlayHandlers(['project-list-empty']);

    const response = await fetch('http://localhost/api/project/list?page=2&pageSize=20');
    const body = await responseJson(response);

    expect(response.status).toBe(200);
    expect(response.headers.get('X-Mock-Response')).toBe('true');
    expect(response.headers.get('X-Mock-Handler')).toBe('project:list');
    expect(response.headers.get('X-Mock-Overlay')).toBe('project-list-empty');
    expect(body).toMatchObject({
      items: [],
      total: 0,
      page: 2,
      pageSize: 20,
    });
  });

  it('returns problem responses without writing through the data source', async () => {
    const before = await context.dataSource().project.list({ page: 1, pageSize: 100 });
    context.activateOverlayHandlers(['project-create-500']);

    const response = await fetch('http://localhost/api/project', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ projectName: 'should-not-persist' }),
    });
    const body = await responseJson(response);
    const after = await context.dataSource().project.list({ page: 1, pageSize: 100 });

    expect(response.status).toBe(500);
    expect(response.headers.get('X-Mock-Handler')).toBe('project:create');
    expect(response.headers.get('X-Mock-Overlay')).toBe('project-create-500');
    expect(body).toMatchObject({
      status: 500,
      detail: '项目创建服务暂不可用',
      errorCode: 'MOCK_PROJECT_CREATE_FAILED',
    });
    expect(after.total).toBe(before.total);
  });

  it('supports 403, 429, timeout, latency, and explicit unsupported responses', async () => {
    context.activateOverlayHandlers(['version-clone-forbidden']);
    const forbidden = await fetch('http://localhost/api/project/version/clone', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ versionId: 2002 }),
    });
    expect(forbidden.status).toBe(403);
    expect(forbidden.headers.get('X-Mock-Overlay')).toBe('version-clone-forbidden');

    context.activateOverlayHandlers(['project-update-429']);
    const rateLimited = await fetch('http://localhost/api/project', {
      method: 'PUT',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ projectId: 1001, projectName: 'rate-limited' }),
    });
    expect(rateLimited.status).toBe(429);
    expect(rateLimited.headers.get('Retry-After')).toBe('30');
    expect(rateLimited.headers.get('X-Mock-Overlay')).toBe('project-update-429');

    context.activateOverlayHandlers(['version-clone-timeout']);
    const timeout = await fetch('http://localhost/api/project/version/clone', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ versionId: 2002 }),
    });
    expect(timeout.status).toBe(504);
    expect(timeout.headers.get('X-Mock-Overlay')).toBe('version-clone-timeout');

    context.activateOverlayHandlers(['topology-load-latency']);
    const topology = await fetch('http://localhost/api/project/topology/1001?version_id=2002');
    expect(topology.status).toBe(200);
    expect(topology.headers.get('X-Mock-Overlay')).toBe('topology-load-latency');
    await expect(responseJson(topology)).resolves.toMatchObject({
      projectId: 1001,
      versionId: 2002,
      topologyData: expect.anything(),
    });

    context.activateOverlayHandlers(['simulation-start-unsupported']);
    const unsupported = await fetch('http://localhost/api/simulation/sessions/demo/start', {
      method: 'POST',
    });
    const unsupportedBody = await responseJson(unsupported);
    expect(unsupported.status).toBe(501);
    expect(unsupported.headers.get('X-Mock-Handler')).toBe('simulation:session-start-unsupported');
    expect(unsupported.headers.get('X-Mock-Overlay')).toBe('simulation-start-unsupported');
    expect(unsupportedBody).toMatchObject({
      reason: '当前 demo-offline 只读模式不支持启动仿真',
      errorCode: 'MOCK_API_NOT_IMPLEMENTED',
    });
    expect(JSON.stringify(unsupportedBody)).toContain('MOCK_API_NOT_IMPLEMENTED');
    expect(JSON.stringify(unsupportedBody)).toContain('当前 demo-offline 只读模式不支持启动仿真');
  });

  it('exposes only read methods through the read-only projection wrapper', async () => {
    const readOnly = createReadonlyOverlayDataSource(context.dataSource());

    expect('list' in readOnly.project).toBe(true);
    expect('get' in readOnly.project).toBe(true);
    expect('create' in readOnly.project).toBe(false);
    expect('save' in readOnly.topology).toBe(false);

    await expect(readOnly.project.list({ page: 1, pageSize: 1 })).resolves.toMatchObject({
      items: expect.any(Array),
    });
  });
});
