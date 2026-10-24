import 'fake-indexeddb/auto';

import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import { mockServer } from '../../../tests/mocks/server';
import { createMockHandlers } from './index';
import { MOCK_DEMO_DB_NAME, MockDemoDb, replaceMockDemoDb } from '../store/db';
import { createMockDataSource, replaceMockDataSource } from '../store/datasource';
import type { MockDataSource } from '../store';

describe('auth/system mock handlers', () => {
  let db: MockDemoDb;
  let dataSource: MockDataSource;

  beforeEach(async () => {
    db = new MockDemoDb(`${MOCK_DEMO_DB_NAME}-auth-system-test`);
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

  it('logs in, returns getInfo from data source, and clears session on logout', async () => {
    const loginResponse = await fetch('/api/login', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ username: 'admin', password: 'admin123' }),
    });
    const loginPayload = await loginResponse.json();

    expect(loginPayload.token).toBe('mock-session-admin-20260430000000');

    const infoResponse = await fetch('/api/getInfo', {
      headers: { authorization: `Bearer ${loginPayload.token}` },
    });
    const infoPayload = await infoResponse.json();

    expect(infoPayload.user).toMatchObject({
      userName: 'admin',
      nickName: '若依',
    });
    expect(infoPayload.roles).toEqual(['admin']);
    expect(infoPayload.permissions).toEqual(['*:*:*']);

    const ticketResponse = await fetch('/api/auth/ws-ticket', {
      method: 'POST',
      headers: {
        authorization: `Bearer ${loginPayload.token}`,
        'content-type': 'application/json',
      },
      body: JSON.stringify({ session_id: 'session-demo-readonly' }),
    });
    const ticketPayload = await ticketResponse.json();

    expect(ticketPayload).toMatchObject({
      wsTicket: 'mock-ws-ticket-session-demo-readonly-20260430000000',
      ws_ticket: 'mock-ws-ticket-session-demo-readonly-20260430000000',
      expiresIn: 30,
    });

    const logoutResponse = await fetch('/api/auth/logout', {
      method: 'POST',
      headers: { authorization: `Bearer ${loginPayload.token}` },
    });

    expect(logoutResponse.status).toBe(204);
    expect(await logoutResponse.text()).toBe('');

    const expiredResponse = await fetch('/api/getInfo', {
      headers: { authorization: `Bearer ${loginPayload.token}` },
    });
    expect(expiredResponse.status).toBe(401);
  });

  it.each([
    '/system/role',
    '/system/menu',
    '/system/config',
    '/system/dict/data',
    '/system/dict/type',
  ])('rejects unsupported offline create at %s without pretending to save', async (path) => {
    const response = await fetch(`/api${path}`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({
        roleName: 'unsaved',
        menuName: 'unsaved',
        configName: 'unsaved',
        dictLabel: 'unsaved',
        dictName: 'unsaved',
      }),
    });
    expect(response.status).toBe(501);
    expect(response.headers.get('location')).toBeNull();
    expect(response.headers.get('content-type')).toContain('application/problem+json');
    const body = await response.json();
    expect(body).toMatchObject({
      type: 'about:blank',
      status: 501,
      instance: `/api${path}`,
      errorCode: 'MOCK_SYSTEM_WRITE_NOT_SUPPORTED',
      detail: expect.stringContaining('只读'),
    });
    expect(body).not.toHaveProperty('code');
    expect(body).not.toHaveProperty('msg');
    expect(body).not.toHaveProperty('data');
    expect(await dataSource.system.listRoles()).toHaveLength(2);
    expect((await dataSource.system.listMenus()).some((menu) => menu.menuName === 'unsaved')).toBe(
      false
    );
    expect(
      (await dataSource.system.listDictData()).some((dict) => dict.dictLabel === 'unsaved')
    ).toBe(false);
  });

  it.each([
    ['DELETE', '/system/role/99'],
    ['DELETE', '/system/menu/99'],
    ['DELETE', '/system/config/99'],
    ['DELETE', '/system/dict/type/99'],
    ['DELETE', '/system/dict/data/99'],
    ['PUT', '/system/role/authUser/cancel'],
    ['PUT', '/system/role/authUser/cancelAll?roleId=2&userIds=99'],
    ['PUT', '/system/role/authUser/selectAll?roleId=2&userIds=99'],
    ['PUT', '/system/role'],
    ['PUT', '/system/role/dataScope'],
    ['PUT', '/system/role/changeStatus'],
    ['PUT', '/system/menu'],
    ['PUT', '/system/config'],
    ['PUT', '/system/dict/data'],
    ['PUT', '/system/dict/type'],
    ['DELETE', '/system/config/refreshCache'],
    ['DELETE', '/system/dict/type/refreshCache'],
  ])('rejects unsupported readonly system mutation %s %s', async (method, path) => {
    const response = await fetch(`/api${path}`, {
      method,
      headers: { 'content-type': 'application/json' },
      ...(method === 'PUT' ? { body: JSON.stringify({ roleId: 2, userId: 99 }) } : {}),
    });
    expect(response.status).toBe(501);
    expect(response.headers.get('content-type')).toContain('application/problem+json');
    await expect(response.json()).resolves.toMatchObject({
      status: 501,
      errorCode: 'MOCK_SYSTEM_WRITE_NOT_SUPPORTED',
    });
    expect((await dataSource.system.listRoles()).map((role) => role.roleId)).toEqual([1, 2]);
  });

  it('serves routers, dicts, departments, roles, and user list from data source', async () => {
    const [routers, dicts, depts, roles, users] = await Promise.all([
      fetch('/api/getRouters').then((response) => response.json()),
      fetch('/api/system/dict/data/type/sys_user_sex').then((response) => response.json()),
      fetch('/api/system/dept/treeselect').then((response) => response.json()),
      fetch('/api/system/role/list').then((response) => response.json()),
      fetch('/api/system/user/list?page=1&pageSize=10').then((response) => response.json()),
    ]);

    expect(routers.items[0]).toMatchObject({ name: 'Project', path: '/project' });
    expect(routers.items).toEqual(
      expect.arrayContaining([expect.objectContaining({ name: 'System', path: '/system' })])
    );
    expect(dicts.items).toHaveLength(3);
    expect(depts.items[0]).toMatchObject({ id: 100, label: '若依科技' });
    expect(roles.items).toHaveLength(2);
    expect(users.items).toHaveLength(2);
  });
});
