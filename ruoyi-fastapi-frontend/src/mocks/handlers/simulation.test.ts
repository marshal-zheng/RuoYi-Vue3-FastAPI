import 'fake-indexeddb/auto';

import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import { mockServer } from '../../../tests/mocks/server';
import { MOCK_SIMULATION_IDS } from '../data';
import { MOCK_DEMO_DB_NAME, MockDemoDb, replaceMockDemoDb } from '../store/db';
import { createMockDataSource, replaceMockDataSource } from '../store/datasource';
import type { MockDataSource } from '../store';
import { createMockHandlers } from './index';

describe('simulation mock handlers', () => {
  let db: MockDemoDb;
  let dataSource: MockDataSource;

  beforeEach(async () => {
    db = new MockDemoDb(`${MOCK_DEMO_DB_NAME}-simulation-handler-test`);
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

  it('serves read-only status, messages, bandwidth, alarms, and events', async () => {
    const sessionId = MOCK_SIMULATION_IDS.commandCenterSession;
    const [status, messages, bandwidth, alarms, events] = await Promise.all([
      fetch(`/api/simulation/sessions/${sessionId}/status`).then((response) => response.json()),
      fetch(`/api/simulation/sessions/${sessionId}/messages?limit=1`).then((response) =>
        response.json()
      ),
      fetch(`/api/simulation/sessions/${sessionId}/bandwidth`).then((response) => response.json()),
      fetch(`/api/simulation/sessions/${sessionId}/alarms`).then((response) => response.json()),
      fetch(`/api/simulation/sessions/${sessionId}/events`).then((response) => response.json()),
    ]);

    expect(status).toMatchObject({ sessionId, status: 'running', messageCount: 2 });
    expect(messages).toHaveLength(1);
    expect(bandwidth[0]).toMatchObject({ sessionId, bandwidthMbps: 860 });
    expect(alarms[0]).toMatchObject({ sessionId, severity: 'warning' });
    expect(events).toHaveLength(2);
  });

  it('returns deterministic unsupported responses for control and write operations', async () => {
    const sessionId = MOCK_SIMULATION_IDS.commandCenterSession;
    const startResponse = await fetch(`/api/simulation/sessions/${sessionId}/start`, {
      method: 'POST',
    });
    const faultResponse = await fetch('/api/simulation/faults', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ sessionId }),
    });

    await expect(startResponse.json()).resolves.toMatchObject({
      code: 501,
      data: null,
    });
    await expect(faultResponse.json()).resolves.toMatchObject({
      code: 501,
      data: null,
    });
  });
});
