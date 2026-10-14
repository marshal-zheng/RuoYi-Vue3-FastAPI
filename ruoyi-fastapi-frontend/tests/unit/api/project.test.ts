import { describe, expect, it } from 'vitest';

import * as projectApi from '@/api/project/project';
import * as topologyApi from '@/api/project/topology';
import * as versionApi from '@/api/project/version';
import { MOCK_PROJECT_IDS, MOCK_VERSION_IDS } from '@/mocks/data';
import { createNetworkErrorHandler, createStatusHandler } from '@/mocks/handlers/error-common';
import { expectRequestTimeout } from '../../helpers/error-assertions';
import { setupMainlineMockHandlers } from '../../mocks/mainline';
import { setupOverlayMockHandlers } from '../../mocks/overlays';
import { mockServer } from '../../mocks/server';

describe('Project API contract', () => {
  setupMainlineMockHandlers();

  it('fetches paged projects through the HTTP contract', async () => {
    const result = await projectApi.listProject({
      page: 1,
      pageSize: 20,
      projectName: '指挥',
    });

    expect(result).toMatchObject({
      total: 1,
      page: 1,
      pageSize: 20,
      items: [
        expect.objectContaining({
          projectName: expect.stringContaining('指挥'),
        }),
      ],
    });
  });

  it('handles project CRUD payloads through MSW handlers', async () => {
    await expect(projectApi.getProject(MOCK_PROJECT_IDS.commandCenter)).resolves.toMatchObject({
      projectId: MOCK_PROJECT_IDS.commandCenter,
      projectCode: 'PRJ-1001',
    });

    await expect(
      projectApi.addProject({
        projectName: '新工程',
        projectCode: 'NEW001',
      })
    ).resolves.toMatchObject({
      projectName: '新工程',
    });

    await expect(
      projectApi.updateProject({
        projectId: 1003,
        projectName: '更新工程',
      })
    ).resolves.toMatchObject({
      projectId: 1003,
      projectName: '更新工程',
    });

    await expect(projectApi.delProject([1, 2, 3])).resolves.toBeNull();
  });

  it('supports topology and export endpoints without mocking request internals', async () => {
    await expect(
      topologyApi.getProjectTopology(
        MOCK_PROJECT_IDS.commandCenter,
        MOCK_VERSION_IDS.commandCenterReview
      )
    ).resolves.toMatchObject({
      projectId: MOCK_PROJECT_IDS.commandCenter,
      topologyData: expect.anything(),
    });

    await expect(
      topologyApi.saveProjectTopology({
        projectId: MOCK_PROJECT_IDS.commandCenter,
        versionId: MOCK_VERSION_IDS.commandCenterReview,
        topologyData: {
          nodes: [{ id: 'node-2' }],
          edges: [],
        },
      })
    ).resolves.toMatchObject({
      projectId: MOCK_PROJECT_IDS.commandCenter,
      versionId: MOCK_VERSION_IDS.commandCenterReview,
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
    await expect(projectApi.listProject({})).rejects.toMatchObject({
      status: 503,
    });

    mockServer.use(createStatusHandler('get', '/project/list', 429));
    await expect(projectApi.listProject({})).rejects.toMatchObject({
      status: 429,
    });

    mockServer.use(createNetworkErrorHandler('get', '/project/list'));
    await expect(projectApi.listProject({})).rejects.toBeInstanceOf(Error);

    await expectRequestTimeout('get', '/project/list');
  });
});

describe('Project API overlay contract', () => {
  const overlays = setupOverlayMockHandlers();

  it('enters project and version empty states through API wrappers', async () => {
    overlays.activateOverlayHandlers(['project-list-empty']);
    await expect(projectApi.listProject({ page: 1, pageSize: 20 })).resolves.toMatchObject({
      items: [],
      total: 0,
      page: 1,
      pageSize: 20,
    });

    overlays.activateOverlayHandlers(['version-list-empty']);
    await expect(
      versionApi.listProjectVersion({
        page: 1,
        pageSize: 20,
        projectId: MOCK_PROJECT_IDS.commandCenter,
      })
    ).resolves.toMatchObject({
      items: [],
      total: 0,
      page: 1,
      pageSize: 20,
    });
  });

  it('enters project write, rate-limit, forbidden, timeout, and topology errors through API wrappers', async () => {
    overlays.activateOverlayHandlers(['project-create-500']);
    await expect(projectApi.addProject({ projectName: 'overlay failure' })).rejects.toMatchObject({
      status: 500,
    });

    overlays.activateOverlayHandlers(['project-update-429']);
    await expect(
      projectApi.updateProject({
        projectId: MOCK_PROJECT_IDS.commandCenter,
        projectName: 'overlay rate limit',
      })
    ).rejects.toMatchObject({
      status: 429,
    });

    overlays.activateOverlayHandlers(['version-clone-forbidden']);
    await expect(
      versionApi.cloneProjectVersion({
        sourceVersionId: MOCK_VERSION_IDS.commandCenterReview,
        versionNumber: '2.0.0',
        versionName: '克隆版本',
      })
    ).rejects.toMatchObject({
      status: 403,
    });

    overlays.activateOverlayHandlers(['topology-save-500']);
    await expect(
      topologyApi.saveProjectTopology({
        projectId: MOCK_PROJECT_IDS.commandCenter,
        versionId: MOCK_VERSION_IDS.commandCenterReview,
        topologyData: { nodes: [], edges: [] },
      })
    ).rejects.toMatchObject({
      status: 500,
    });
  });
});
