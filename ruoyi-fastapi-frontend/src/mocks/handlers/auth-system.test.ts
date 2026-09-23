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

    await fetch('/api/logout', {
      method: 'POST',
      headers: { authorization: `Bearer ${loginPayload.token}` },
    });

    const expiredResponse = await fetch('/api/getInfo', {
      headers: { authorization: `Bearer ${loginPayload.token}` },
    });
    expect(expiredResponse.status).toBe(401);
  });

  it('serves routers, dicts, departments, roles, and user list from data source', async () => {
    const [routers, dicts, depts, roles, users] = await Promise.all([
      fetch('/api/getRouters').then((response) => response.json()),
      fetch('/api/system/dict/data/type/sys_user_sex').then((response) => response.json()),
      fetch('/api/system/dept/treeselect').then((response) => response.json()),
      fetch('/api/system/role/list').then((response) => response.json()),
      fetch('/api/system/user/list?page=1&pageSize=10').then((response) => response.json()),
    ]);

    expect(routers[0]).toMatchObject({ name: 'Project', path: '/project' });
    expect(routers).toEqual(
      expect.arrayContaining([expect.objectContaining({ name: 'System', path: '/system' })])
    );
    expect(dicts.items).toHaveLength(3);
    expect(depts[0]).toMatchObject({ id: 100, label: '若依科技' });
    expect(roles.items).toHaveLength(2);
    expect(users.items).toHaveLength(2);
  });
});
