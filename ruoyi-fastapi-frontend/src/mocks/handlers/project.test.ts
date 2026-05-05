import 'fake-indexeddb/auto';

import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import { mockServer } from '../../../tests/mocks/server';
import { MOCK_PROJECT_IDS, MOCK_VERSION_IDS } from '../data';
import { MOCK_DEMO_DB_NAME, MockDemoDb, replaceMockDemoDb } from '../store/db';
import { createMockDataSource, replaceMockDataSource } from '../store/datasource';
import type { MockDataSource } from '../store';
import { createMockHandlers } from './index';

describe('project/version/topology mock handlers', () => {
  let db: MockDemoDb;
  let dataSource: MockDataSource;

  beforeEach(async () => {
    db = new MockDemoDb(`${MOCK_DEMO_DB_NAME}-project-handler-test`);
    replaceMockDemoDb(db);
    dataSource = createMockDataSource(db);
    replaceMockDataSource(dataSource);
    await dataSource.init();
    mockServer.use(...createMockHandlers({ strategy: 'pure', dataSource }));
  });

  afterEach(async () => {
    replaceMockDataSource(undefined);
    replaceMockDemoDb(undefined);
    await db.delete();
  });

  it('persists project CRUD through the mock store', async () => {
    const created = await fetch('/api/project', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ projectName: '客户演示项目' }),
    }).then((response) => response.json());

    const updated = await fetch('/api/project', {
      method: 'PUT',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({
        projectId: created.projectId,
        projectName: '客户演示项目-更新',
      }),
    }).then((response) => response.json());

    expect(updated).toMatchObject({
      projectId: created.projectId,
      projectName: '客户演示项目-更新',
    });

    const refreshed = createMockDataSource(db);
    await refreshed.init();
    await expect(refreshed.project.get(created.projectId)).resolves.toMatchObject({
      projectName: '客户演示项目-更新',
    });
  });

  it('handles version clone, lock/unlock, delete, and export placeholders', async () => {
    const cloned = await fetch('/api/project/version/clone', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({
        sourceVersionId: MOCK_VERSION_IDS.commandCenterReview,
        versionName: '客户评审副本',
      }),
    }).then((response) => response.json());

    const locked = await fetch('/api/project/version/lock', {
      method: 'PUT',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ versionId: cloned.versionId, isLocked: '1' }),
    }).then((response) => response.json());

    expect(locked).toMatchObject({
      versionName: '客户评审副本',
      isLocked: '1',
    });

    await expect(
      dataSource.topology.getByProjectVersion(MOCK_PROJECT_IDS.commandCenter, cloned.versionId)
    ).resolves.toMatchObject({
      graph: expect.objectContaining({ nodes: expect.any(Array) }),
    });

    const exportResponse = await fetch('/api/project/version/export', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ versionId: cloned.versionId }),
    });
    expect(exportResponse.headers.get('content-type')).toContain('application/msword');

    await fetch('/api/project/version/lock', {
      method: 'PUT',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ versionId: cloned.versionId, isLocked: '0' }),
    });
    await fetch(`/api/project/version/${cloned.versionId}`, {
      method: 'DELETE',
    });
    await expect(dataSource.version.get(cloned.versionId)).resolves.toBeUndefined();
  });

  it('rejects edits and topology saves for locked or mismatched versions', async () => {
    const lockedUpdateResponse = await fetch('/api/project/version', {
      method: 'PUT',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({
        versionId: MOCK_VERSION_IDS.commandCenterBaseline,
        versionName: '不应修改固化版本',
      }),
    });
    const lockedDeleteResponse = await fetch(
      `/api/project/version/${MOCK_VERSION_IDS.commandCenterBaseline}`,
      {
        method: 'DELETE',
      }
    );
    const lockedTopologyResponse = await fetch('/api/project/topology/save', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({
        projectId: MOCK_PROJECT_IDS.commandCenter,
        versionId: MOCK_VERSION_IDS.commandCenterBaseline,
        topologyData: { nodes: [{ id: 'locked-node' }], edges: [] },
      }),
    });
    const mismatchedTopologyResponse = await fetch('/api/project/topology/save', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({
        projectId: MOCK_PROJECT_IDS.trainingRange,
        versionId: MOCK_VERSION_IDS.commandCenterReview,
        topologyData: { nodes: [{ id: 'wrong-project-node' }], edges: [] },
      }),
    });

    expect(lockedUpdateResponse.status).toBe(400);
    expect(lockedDeleteResponse.status).toBe(400);
    expect(lockedTopologyResponse.status).toBe(400);
    expect(mismatchedTopologyResponse.status).toBe(400);
    await expect(lockedTopologyResponse.json()).resolves.toMatchObject({
      detail: '固化版本不允许保存拓扑',
    });
    await expect(mismatchedTopologyResponse.json()).resolves.toMatchObject({
      detail: '版本不属于当前工程',
    });
  });

  it('reads and saves topology by project/version', async () => {
    const saved = await fetch('/api/project/topology/save', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({
        projectId: MOCK_PROJECT_IDS.commandCenter,
        versionId: MOCK_VERSION_IDS.commandCenterReview,
        topologyData: { nodes: [{ id: 'new-node' }], edges: [] },
      }),
    }).then((response) => response.json());

    expect(saved).toMatchObject({
      projectId: MOCK_PROJECT_IDS.commandCenter,
      versionId: MOCK_VERSION_IDS.commandCenterReview,
      topologyData: { nodes: [{ id: 'new-node' }], edges: [] },
    });

    const readBack = await fetch(
      `/api/project/topology/${MOCK_PROJECT_IDS.commandCenter}?version_id=${MOCK_VERSION_IDS.commandCenterReview}`
    ).then((response) => response.json());

    expect(readBack.topologyData).toEqual({
      nodes: [{ id: 'new-node' }],
      edges: [],
    });
  });
});
