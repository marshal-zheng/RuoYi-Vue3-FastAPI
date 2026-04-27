import 'fake-indexeddb/auto';

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { DemoOfflineDb, replaceDemoOfflineDb } from '@/demo/db';
import { createDemoOfflineHandlers } from '@/demo/handlers';
import { AuthRepository, ScenarioRepository } from '@/demo/repositories';
import type { DemoRuntimeLogger } from '@/demo/runtime/logger';
import type { RuntimeConfig } from '@/demo/runtime/mode';
import { defaultDemoScenario } from '@/demo/scenarios';
import { DemoAuthService } from '@/demo/services';
import { mockServer } from '../../../tests/mocks/server';

const runtimeConfig: RuntimeConfig = {
  mode: 'demo-offline',
  mockMode: 'pure',
  apiPrefix: '/api',
  scenarioId: 'default',
  debug: true,
  source: 'runtime-mode',
};

const logger: DemoRuntimeLogger = {
  debug: vi.fn(),
  info: vi.fn(),
  warn: vi.fn(),
  error: vi.fn(),
};

let db: DemoOfflineDb;

async function createAuthHeaders(): Promise<HeadersInit> {
  const authService = new DemoAuthService(new AuthRepository(db));
  const login = await authService.login({
    username: 'admin',
    password: 'admin123',
  });

  return {
    Authorization: `Bearer ${login.token}`,
    'Content-Type': 'application/json',
  };
}

describe('demo-offline project handlers', () => {
  beforeEach(async () => {
    db = new DemoOfflineDb(`demo-project-handler-test-${crypto.randomUUID()}`);
    replaceDemoOfflineDb(db);
    await new ScenarioRepository(db).ensureScenario(defaultDemoScenario);
    mockServer.use(...createDemoOfflineHandlers({ config: runtimeConfig, logger }));
  });

  afterEach(async () => {
    await db.delete();
    replaceDemoOfflineDb(undefined);
  });

  it('serves project CRUD and topology save through HTTP handlers', async () => {
    const headers = await createAuthHeaders();

    const createResponse = await fetch('/api/project', {
      method: 'POST',
      headers,
      body: JSON.stringify({
        projectName: 'HTTP 新建工程',
        projectDesc: '来自 handler 测试',
      }),
    });
    const created = await createResponse.json();

    expect(createResponse.status).toBe(200);
    expect(created).toMatchObject({
      projectName: 'HTTP 新建工程',
      projectDesc: '来自 handler 测试',
      createBy: 'admin',
    });

    const projectId = created.projectId;

    const listResponse = await fetch('/api/project/list?projectName=HTTP', {
      headers,
    });
    const listPayload = await listResponse.json();

    expect(listResponse.status).toBe(200);
    expect(listPayload.items).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          projectId,
          projectName: 'HTTP 新建工程',
        }),
      ])
    );

    const topologyResponse = await fetch('/api/project/topology/save', {
      method: 'POST',
      headers,
      body: JSON.stringify({
        projectId,
        topologyData: {
          graph: {
            cells: [{ id: 'http-node' }],
          },
          nodes: [{ id: 'http-node' }],
          edges: [],
        },
      }),
    });
    const topologyPayload = await topologyResponse.json();

    expect(topologyResponse.status).toBe(200);
    expect(topologyPayload).toMatchObject({
      projectId,
      topologyData: {
        graph: {
          cells: [{ id: 'http-node' }],
        },
      },
    });

    const getTopologyResponse = await fetch(`/api/project/topology/${projectId}`, {
      headers,
    });
    const getTopologyPayload = await getTopologyResponse.json();

    expect(getTopologyResponse.status).toBe(200);
    expect(getTopologyPayload.topologyData.graph).toEqual({
      cells: [{ id: 'http-node' }],
    });
  });

  it('returns deterministic binary placeholders for project and version exports', async () => {
    const headers = await createAuthHeaders();

    const projectExportResponse = await fetch('/api/project/export/1001', {
      headers,
    });
    const projectExportText = await projectExportResponse.text();

    expect(projectExportResponse.status).toBe(200);
    expect(projectExportResponse.headers.get('content-disposition')).toContain("filename*=UTF-8''");
    expect(projectExportResponse.headers.get('content-type')).toContain('application/zip');
    expect(projectExportText).toContain('demo-project-export');

    const versionExportResponse = await fetch('/api/project/version/export', {
      method: 'POST',
      headers,
      body: JSON.stringify({
        versionId: 2001,
      }),
    });
    const versionExportText = await versionExportResponse.text();

    expect(versionExportResponse.status).toBe(200);
    expect(versionExportResponse.headers.get('content-type')).toContain('application/msword');
    expect(versionExportText).toContain('demo-version-export-word');
  });
});
