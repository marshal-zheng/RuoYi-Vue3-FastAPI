import 'fake-indexeddb/auto';

import { afterEach, describe, expect, it } from 'vitest';

import { MOCK_PROJECT_IDS, MOCK_SIMULATION_IDS, MOCK_VERSION_IDS } from '../data';
import { MOCK_DEMO_DB_NAME, MockDemoDb, replaceMockDemoDb } from './db';
import { createMockDataSource, replaceMockDataSource } from './datasource';

describe('DexieMockDataSource', () => {
  let db: MockDemoDb | undefined;

  afterEach(async () => {
    replaceMockDataSource(undefined);
    replaceMockDemoDb(undefined);
    if (db) {
      await db.delete();
      db = undefined;
    }
  });

  function createDataSource() {
    db = new MockDemoDb(`${MOCK_DEMO_DB_NAME}-datasource-test`);
    replaceMockDemoDb(db);
    return createMockDataSource(db);
  }

  it('supports auth sessions and system read repositories', async () => {
    const dataSource = createDataSource();
    await dataSource.init();

    const account = await dataSource.auth.findAccountByUsername('admin');
    const session = await dataSource.auth.createSession('admin');

    expect(account?.roles).toContain('admin');
    await expect(dataSource.auth.findSessionByToken(session.token)).resolves.toMatchObject({
      username: 'admin',
    });
    await expect(dataSource.system.listMenus()).resolves.toHaveLength(4);
    await expect(dataSource.system.listDictData('sys_user_sex')).resolves.toHaveLength(3);

    await dataSource.auth.deleteSession(session.token);
    await expect(dataSource.auth.findSessionByToken(session.token)).resolves.toBeUndefined();
  });

  it('persists project, version, and topology changes across data source instances', async () => {
    const dataSource = createDataSource();
    await dataSource.init();

    const created = await dataSource.project.create({ projectName: '持久化演示项目' });
    const updated = await dataSource.project.update(created.projectId, { status: 'paused' });
    const createdVersion = await dataSource.version.create({
      projectId: created.projectId,
      versionName: '客户评审副本',
    });
    const topology = await dataSource.topology.save(created.projectId, createdVersion.versionId, {
      nodes: [{ id: 'node-a' }],
      edges: [],
    });
    const locked = await dataSource.version.lock(createdVersion.versionId);

    expect(updated.status).toBe('paused');
    expect(locked.locked).toBe(true);
    expect(topology.id).toBe(`topology-${created.projectId}-${locked.versionId}`);

    const refreshed = createMockDataSource(db);
    await refreshed.init();

    await expect(refreshed.project.get(created.projectId)).resolves.toMatchObject({
      projectName: '持久化演示项目',
      status: 'paused',
    });
    await expect(
      refreshed.topology.getByProjectVersion(created.projectId, locked.versionId)
    ).resolves.toMatchObject({
      graph: { nodes: [{ id: 'node-a' }], edges: [] },
    });
  });

  it('exposes simulation data as read-only repository queries', async () => {
    const dataSource = createDataSource();
    await dataSource.init();

    await expect(dataSource.simulation.listSessions()).resolves.toEqual([
      expect.objectContaining({
        sessionId: MOCK_SIMULATION_IDS.commandCenterSession,
        projectId: MOCK_PROJECT_IDS.commandCenter,
      }),
    ]);
    await expect(
      dataSource.simulation.getSession(MOCK_SIMULATION_IDS.commandCenterSession)
    ).resolves.toMatchObject({
      versionId: MOCK_VERSION_IDS.commandCenterReview,
    });
    await expect(
      dataSource.simulation.listFrames(MOCK_SIMULATION_IDS.commandCenterSession)
    ).resolves.toHaveLength(2);
    await expect(
      dataSource.simulation.listMessages(MOCK_SIMULATION_IDS.commandCenterSession)
    ).resolves.toHaveLength(2);
    await expect(
      dataSource.simulation.listEvents(MOCK_SIMULATION_IDS.commandCenterSession)
    ).resolves.toHaveLength(2);
  });
});
