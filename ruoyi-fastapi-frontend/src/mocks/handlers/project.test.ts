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
    mockServer.use(
      ...createMockHandlers({ strategy: 'pure', dataSource, onMissingCapability: 'error' })
    );
  });

  afterEach(async () => {
    replaceMockDataSource(undefined);
    replaceMockDemoDb(undefined);
    await db.delete();
  });

  it.each(['GET', 'PUT'])('rejects the obsolete nested topology %s route', async (method) => {
    const response = await fetch(`/api/project/${MOCK_PROJECT_IDS.commandCenter}/topology`, {
      method,
      headers: { 'content-type': 'application/json' },
      ...(method === 'PUT'
        ? {
            body: JSON.stringify({
              versionId: MOCK_VERSION_IDS.commandCenterReview,
              topologyData: { nodes: [], edges: [] },
            }),
          }
        : {}),
    });
    expect(response.status).toBe(501);
    expect(response.headers.get('X-Mock-Handler')).toBe('unhandled-api');
  });

  it('returns a created resource Location that reads the persisted project', async () => {
    const response = await fetch('/api/project', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ projectName: 'created resource contract' }),
    });
    expect(response.status).toBe(201);
    const created = await response.json();
    const location = response.headers.get('location');
    expect(location).toBe(new URL(`/api/project/${created.projectId}`, response.url).href);
    if (!location) throw new Error('A persisted creation must return Location');
    const resource = await fetch(location).then((res) => res.json());
    const { versionId, ...project } = created;
    expect(resource).toEqual(project);
    expect(versionId).toBeGreaterThan(0);
    expect(
      await fetch(`/api/project/version/${versionId}`).then((res) => res.json())
    ).toMatchObject({
      projectId: created.projectId,
      versionId,
      versionNumber: 'v1.0.0',
    });
    const deleted = await fetch(location, { method: 'DELETE' });
    expect(deleted.status).toBe(204);
    expect(await deleted.text()).toBe('');
    expect((await fetch(location)).status).toBe(404);
  });

  it('returns a created resource Location that reads the persisted version', async () => {
    const response = await fetch('/api/project/version', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({
        projectId: MOCK_PROJECT_IDS.commandCenter,
        versionName: 'created version',
        versionNumber: '9.0.0',
      }),
    });
    expect(response.status).toBe(201);
    const created = await response.json();
    const location = response.headers.get('location');
    expect(location).toBe(new URL(`/api/project/version/${created.versionId}`, response.url).href);
    if (!location) throw new Error('A persisted creation must return Location');
    expect(await fetch(location).then((res) => res.json())).toEqual(created);
    const deleted = await fetch(location, { method: 'DELETE' });
    expect(deleted.status).toBe(204);
    expect(await deleted.text()).toBe('');
    expect((await fetch(location)).status).toBe(404);
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

  it('rejects the obsolete clone id alias and missing required names without writing a version', async () => {
    const before = await dataSource.version.list(MOCK_PROJECT_IDS.commandCenter);
    for (const body of [
      {
        versionId: MOCK_VERSION_IDS.commandCenterReview,
        versionName: 'legacy',
        versionNumber: '7.0.0',
      },
      { sourceVersionId: MOCK_VERSION_IDS.commandCenterReview, versionName: 'missing number' },
    ]) {
      const response = await fetch('/api/project/version/clone', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify(body),
      });
      expect(response.status).toBe(422);
      expect(response.headers.get('location')).toBeNull();
    }
    expect((await dataSource.version.list(MOCK_PROJECT_IDS.commandCenter)).total).toBe(
      before.total
    );
  });

  it('clones to the requested version number and reads the persisted created resource', async () => {
    const response = await fetch('/api/project/version/clone', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({
        sourceVersionId: MOCK_VERSION_IDS.commandCenterReview,
        versionName: 'number contract',
        versionNumber: '8.3.1',
      }),
    });
    expect(response.status).toBe(201);
    const body = await response.json();
    expect(body).toMatchObject({
      versionName: 'number contract',
      versionNumber: '8.3.1',
      isLocked: '0',
    });
    const location = response.headers.get('location');
    if (!location) throw new Error('A successful clone must return its persisted Location');
    expect(await fetch(location).then((res) => res.json())).toEqual(body);
    expect(
      await dataSource.topology.getByProjectVersion(MOCK_PROJECT_IDS.commandCenter, body.versionId)
    ).toMatchObject({ graph: expect.objectContaining({ nodes: expect.any(Array) }) });
  });

  it('rejects a duplicate requested clone version number without adding a second copy', async () => {
    const body = {
      sourceVersionId: MOCK_VERSION_IDS.commandCenterReview,
      versionName: 'unique clone',
      versionNumber: '8.9.2',
    };
    const send = () =>
      fetch('/api/project/version/clone', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify(body),
      });
    expect((await send()).status).toBe(201);
    const before = await dataSource.version.list(MOCK_PROJECT_IDS.commandCenter);
    const duplicate = await send();
    expect(duplicate.status).toBe(409);
    expect(duplicate.headers.get('location')).toBeNull();
    expect((await dataSource.version.list(MOCK_PROJECT_IDS.commandCenter)).total).toBe(
      before.total
    );
  });

  it('handles version clone, lock/unlock, delete, and export placeholders', async () => {
    const cloned = await fetch('/api/project/version/clone', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({
        sourceVersionId: MOCK_VERSION_IDS.commandCenterReview,
        versionName: '客户评审副本',
        versionNumber: '7.2.0',
      }),
    }).then((response) => response.json());

    const locked = await fetch('/api/project/version/lock', {
      method: 'PUT',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ versionId: cloned.versionId, isLocked: '1' }),
    }).then((response) => response.json());

    expect(locked).toMatchObject({
      versionName: '客户评审副本',
      versionNumber: '7.2.0',
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

    expect(lockedUpdateResponse.status).toBe(409);
    expect(lockedDeleteResponse.status).toBe(409);
    expect(lockedTopologyResponse.status).toBe(409);
    expect(mismatchedTopologyResponse.status).toBe(404);
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
