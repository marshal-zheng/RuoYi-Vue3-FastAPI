import 'fake-indexeddb/auto';

import { createServer, type Server } from 'node:http';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import { mockServer } from '../../../tests/mocks/server';
import { MOCK_DEMO_DB_NAME, MockDemoDb, replaceMockDemoDb } from '../store/db';
import { createMockDataSource, replaceMockDataSource } from '../store/datasource';
import type { MockDataSource } from '../store';
import { createMockHandlers } from './index';

async function listen(server: Server): Promise<number> {
  await new Promise<void>((resolve) => {
    server.listen(0, '127.0.0.1', resolve);
  });
  const address = server.address();
  if (!address || typeof address === 'string') {
    throw new Error('Failed to allocate test server port');
  }
  return address.port;
}

async function close(server: Server): Promise<void> {
  if (!server.listening) return;
  await new Promise<void>((resolve, reject) => {
    server.close((error) => (error ? reject(error) : resolve()));
  });
}

describe('fallback mock handlers', () => {
  let db: MockDemoDb;
  let dataSource: MockDataSource;

  beforeEach(async () => {
    db = new MockDemoDb(`${MOCK_DEMO_DB_NAME}-fallback-handler-test`);
    replaceMockDemoDb(db);
    dataSource = createMockDataSource(db);
    replaceMockDataSource(dataSource);
    await dataSource.init();
    mockServer.use(...createMockHandlers({ strategy: 'fallback', dataSource }));
  });

  afterEach(async () => {
    replaceMockDataSource(undefined);
    replaceMockDemoDb(undefined);
    await db.delete();
  });

  it('passes through successful upstream responses', async () => {
    const upstream = createServer((_request, response) => {
      response.writeHead(200, { 'content-type': 'application/json' });
      response.end(JSON.stringify({ source: 'upstream', ok: true }));
    });
    const port = await listen(upstream);

    try {
      const response = await fetch(`http://127.0.0.1:${port}/api/project/list`);

      expect(response.status).toBe(200);
      expect(response.headers.get('X-Mock-Response')).toBeNull();
      await expect(response.json()).resolves.toEqual({ source: 'upstream', ok: true });
    } finally {
      await close(upstream);
    }
  });

  it('falls back to mock data when upstream returns 404', async () => {
    const upstream = createServer((_request, response) => {
      response.writeHead(404, { 'content-type': 'application/json' });
      response.end(JSON.stringify({ detail: 'not found upstream' }));
    });
    const port = await listen(upstream);

    try {
      const response = await fetch(`http://127.0.0.1:${port}/api/project/list?page=1&pageSize=10`);

      expect(response.status).toBe(200);
      expect(response.headers.get('X-Mock-Handler')).toBe('project:list');
      await expect(response.json()).resolves.toMatchObject({
        items: expect.arrayContaining([
          expect.objectContaining({ projectName: expect.any(String) }),
        ]),
      });
    } finally {
      await close(upstream);
    }
  });

  it('falls back to mock data when upstream is unreachable', async () => {
    const closedServer = createServer();
    const closedPort = await listen(closedServer);
    await close(closedServer);

    const response = await fetch(
      `http://127.0.0.1:${closedPort}/api/project/list?page=1&pageSize=10`
    );

    expect(response.status).toBe(200);
    expect(response.headers.get('X-Mock-Handler')).toBe('project:list');
    await expect(response.json()).resolves.toMatchObject({
      items: expect.arrayContaining([expect.objectContaining({ projectName: expect.any(String) })]),
    });
  });
});
