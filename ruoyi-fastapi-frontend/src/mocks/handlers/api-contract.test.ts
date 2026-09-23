import 'fake-indexeddb/auto';

import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import { getRouters } from '@/api/menu';
import { getCodeImg, getInfo, login, logout } from '@/api/login';
import { addProject, listProject, updateProject } from '@/api/project/project';
import { cloneProjectVersion, listProjectVersion, lockProjectVersion } from '@/api/project/version';
import { getProjectTopology, saveProjectTopology } from '@/api/project/topology';
import {
  getEvents,
  getSimulationAlarms,
  getSimulationBandwidth,
  getSimulationMessages,
  getSimulationStatus,
  pauseSimulationSession,
} from '@/api/simulation/simulation';
import { getDicts } from '@/api/system/dict/data';
import { listDept } from '@/api/system/dept';
import { listRole } from '@/api/system/role';
import { clearSecurityTokens, setToken } from '@/utils/auth';

import { mockServer } from '../../../tests/mocks/server';
import { MOCK_DEMO_DB_NAME, MockDemoDb, replaceMockDemoDb } from '../store/db';
import { createMockDataSource, replaceMockDataSource } from '../store/datasource';
import type { MockDataSource } from '../store';
import { MOCK_PROJECT_IDS, MOCK_SIMULATION_IDS, MOCK_VERSION_IDS } from '../data';
import { createMockHandlers } from './index';

describe('mock handlers through frontend API contracts', () => {
  let db: MockDemoDb;
  let dataSource: MockDataSource;

  beforeEach(async () => {
    clearSecurityTokens();
    db = new MockDemoDb(`${MOCK_DEMO_DB_NAME}-api-contract-test`);
    replaceMockDemoDb(db);
    dataSource = createMockDataSource(db);
    replaceMockDataSource(dataSource);
    await dataSource.init();
    mockServer.use(...createMockHandlers({ strategy: 'pure', dataSource }));
  });

  afterEach(async () => {
    clearSecurityTokens();
    replaceMockDataSource(undefined);
    replaceMockDemoDb(undefined);
    await db.delete();
  });

  it('covers auth and system handlers via the real request path', async () => {
    await expect(getCodeImg()).resolves.toMatchObject({
      captchaEnabled: false,
      uuid: 'mock-uuid-20260430000000',
    });

    const loginResult = await login('admin', 'admin123', '1234', 'uuid-1');
    expect(loginResult).toMatchObject({
      token: 'mock-session-admin-20260430000000',
    });

    setToken(loginResult.token);

    await expect(getInfo()).resolves.toMatchObject({
      user: expect.objectContaining({ userName: 'admin', nickName: '若依' }),
      roles: ['admin'],
      permissions: ['*:*:*'],
    });

    await expect(getRouters()).resolves.toEqual([
      expect.objectContaining({ name: 'Project', path: '/project' }),
      expect.objectContaining({ name: 'System', path: '/system' }),
    ]);
    await expect(getDicts('sys_user_sex')).resolves.toMatchObject({
      items: expect.arrayContaining([
        expect.objectContaining({ dictType: 'sys_user_sex', dictValue: '0' }),
      ]),
    });
    await expect(listDept({})).resolves.toMatchObject({
      items: expect.arrayContaining([
        expect.objectContaining({ deptId: 100, deptName: '若依科技' }),
      ]),
    });
    await expect(listRole({})).resolves.toMatchObject({
      items: [
        expect.objectContaining({ roleKey: 'admin' }),
        expect.objectContaining({ roleKey: 'editor' }),
      ],
    });

    await expect(logout({ silentSuccess: true, silentError: true })).resolves.toBeNull();
    await expect(dataSource.auth.findSessionByToken(loginResult.token)).resolves.toBeUndefined();
  });

  it('covers project, version, and topology handlers via frontend API functions', async () => {
    const projects = await listProject({
      page: 1,
      pageSize: 10,
      projectName: '指挥',
    });

    expect(projects).toMatchObject({
      total: 1,
      items: [
        expect.objectContaining({
          projectId: MOCK_PROJECT_IDS.commandCenter,
          projectName: expect.stringContaining('指挥'),
        }),
      ],
    });

    const created = await addProject({ projectName: '客户验收演示工程' });
    const updated = await updateProject({
      projectId: created.projectId,
      projectName: '客户验收演示工程-更新',
    });
    expect(updated).toMatchObject({
      projectId: created.projectId,
      projectName: '客户验收演示工程-更新',
    });

    const rehydrated = createMockDataSource(db);
    await rehydrated.init();
    await expect(rehydrated.project.get(created.projectId)).resolves.toMatchObject({
      projectName: '客户验收演示工程-更新',
    });

    await expect(
      listProjectVersion({ projectId: MOCK_PROJECT_IDS.commandCenter })
    ).resolves.toMatchObject({
      items: [
        expect.objectContaining({
          versionId: MOCK_VERSION_IDS.commandCenterBaseline,
        }),
        expect.objectContaining({
          versionId: MOCK_VERSION_IDS.commandCenterReview,
        }),
      ],
    });

    const cloned = await cloneProjectVersion({
      sourceVersionId: MOCK_VERSION_IDS.commandCenterReview,
      versionName: 'API 合约副本',
    });
    await expect(
      lockProjectVersion({ versionId: cloned.versionId, isLocked: '1' })
    ).resolves.toMatchObject({
      versionId: cloned.versionId,
      versionName: 'API 合约副本',
      isLocked: '1',
    });

    const graph = { nodes: [{ id: 'api-contract-node' }], edges: [] };
    await expect(
      saveProjectTopology({
        projectId: MOCK_PROJECT_IDS.commandCenter,
        versionId: MOCK_VERSION_IDS.commandCenterReview,
        topologyData: graph,
      })
    ).resolves.toMatchObject({
      topologyData: graph,
    });
    await expect(
      getProjectTopology(MOCK_PROJECT_IDS.commandCenter, MOCK_VERSION_IDS.commandCenterReview)
    ).resolves.toMatchObject({
      topologyData: graph,
    });
  });

  it('covers simulation read models and unsupported writes via frontend API functions', async () => {
    const sessionId = MOCK_SIMULATION_IDS.commandCenterSession;

    await expect(getSimulationStatus(sessionId)).resolves.toMatchObject({
      sessionId,
      status: 'running',
      messageCount: 2,
    });
    await expect(getSimulationMessages(sessionId, 1)).resolves.toEqual([
      expect.objectContaining({ sessionId }),
    ]);
    await expect(getSimulationBandwidth(sessionId)).resolves.toEqual([
      expect.objectContaining({ sessionId, bandwidthMbps: 860 }),
      expect.objectContaining({ sessionId, bandwidthMbps: 910 }),
    ]);
    await expect(getSimulationAlarms(sessionId)).resolves.toEqual([
      expect.objectContaining({ sessionId, severity: 'warning' }),
    ]);
    await expect(getEvents(sessionId)).resolves.toEqual([
      expect.objectContaining({ sessionId }),
      expect.objectContaining({ sessionId }),
    ]);

    await expect(pauseSimulationSession(sessionId)).rejects.toMatchObject({
      status: 501,
    });
  });

  it('returns deterministic 501 for demo-offline API gaps', async () => {
    mockServer.use(
      ...createMockHandlers({
        strategy: 'pure',
        dataSource,
        onMissingCapability: 'error',
      })
    );

    const handled = await fetch('/api/project/list?page=1&pageSize=10');
    expect(handled.status).toBe(200);
    expect(handled.headers.get('X-Mock-Handler')).toBe('project:list');

    const missing = await fetch('/api/not-implemented-yet?trace=1', {
      method: 'PATCH',
    });

    expect(missing.status).toBe(501);
    expect(missing.headers.get('X-Mock-Handler')).toBe('unhandled-api');
    await expect(missing.json()).resolves.toEqual({
      code: 501,
      msg: 'MOCK_API_NOT_IMPLEMENTED: PATCH /api/not-implemented-yet?trace=1 尚未在单套 mock 主线中实现',
      data: null,
    });
  });
});
