import { beforeEach, describe, expect, it } from 'vitest';

import * as projectApi from '@/api/project/project';
import {
  createApiContractHandlers,
  createNetworkErrorHandler,
  createStatusHandler,
} from '../../mocks/api-contract-handlers';
import { mockServer } from '../../mocks/server';

describe('Project API contract', () => {
  beforeEach(() => {
    mockServer.use(...createApiContractHandlers());
  });

  it('fetches paged projects through the HTTP contract', async () => {
    const result = await projectApi.listProject({ page: 2, pageSize: 20, projectName: '星载' });

    expect(result).toMatchObject({
      total: 1,
      page: 2,
      pageSize: 20,
      items: [expect.objectContaining({ projectName: '星载' })],
    });
    expect(result.pager).toMatchObject({ mode: 'offset', page: 2, size: 20, total: 1 });
  });

  it('handles project CRUD payloads through MSW handlers', async () => {
    await expect(projectApi.getProject(1)).resolves.toMatchObject({
      projectId: 1,
      projectCode: 'PRJ-001',
    });

    await expect(
      projectApi.addProject({
        projectName: '新工程',
        projectCode: 'NEW001',
      })
    ).resolves.toMatchObject({
      projectId: 2,
      projectName: '新工程',
    });

    await expect(
      projectApi.updateProject({
        projectId: 2,
        projectName: '更新工程',
      })
    ).resolves.toMatchObject({
      projectId: 2,
      projectName: '更新工程',
    });

    await expect(projectApi.delProject([1, 2, 3])).resolves.toBeNull();
  });

  it('supports topology and export endpoints without mocking request internals', async () => {
    await expect(projectApi.getProjectTopology(1)).resolves.toMatchObject({
      projectId: 1,
      topologyData: {
        nodes: [expect.objectContaining({ id: 'node-1' })],
      },
    });

    await expect(
      projectApi.updateProjectTopology(1, {
        nodes: [{ id: 'node-2' }],
        edges: [],
      })
    ).resolves.toMatchObject({
      projectId: 1,
      topologyData: {
        nodes: [{ id: 'node-2' }],
        edges: [],
      },
    });

    const exported = await projectApi.exportProject(1);
    expect(exported).toBeInstanceOf(Blob);
  });

  it('maps 503, 429, and network failures from the real request path', async () => {
    mockServer.use(createStatusHandler('get', '/project/list', 503));
    await expect(projectApi.listProject({})).rejects.toMatchObject({ status: 503 });

    mockServer.use(createStatusHandler('get', '/project/list', 429));
    await expect(projectApi.listProject({})).rejects.toMatchObject({ status: 429 });

    mockServer.use(createNetworkErrorHandler('get', '/project/list'));
    await expect(projectApi.listProject({})).rejects.toBeInstanceOf(Error);
  });
});
