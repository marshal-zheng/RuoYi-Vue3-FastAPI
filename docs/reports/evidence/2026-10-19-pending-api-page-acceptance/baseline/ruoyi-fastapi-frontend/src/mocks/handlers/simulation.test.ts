import 'fake-indexeddb/auto';

import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import { mockServer } from '../../../tests/mocks/server';
import controllerWire from '../../../tests/fixtures/simulation-http-wire.json';
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
    expect(messages.items).toHaveLength(1);
    expect(messages.items[0].timestamp).toEqual(expect.any(Number));
    expect(bandwidth.items[0]).toMatchObject({ sessionId, bandwidthMbps: 860 });
    expect(bandwidth.items[0].timestamp).toEqual(expect.any(Number));
    expect(alarms.items[0]).toMatchObject({ sessionId, severity: 'warning' });
    expect(alarms.items[0].timestamp).toEqual(expect.any(Number));
    expect(events.items).toHaveLength(2);
    expect(events.items).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          eventId: 'event-001',
          name: 'session_started',
          status: 'triggered',
        }),
      ])
    );
  });

  it('filters the bandwidth collection using the controller port_id query', async () => {
    const sessionId = MOCK_SIMULATION_IDS.commandCenterSession;
    const matching = await fetch(
      `/api/simulation/sessions/${sessionId}/bandwidth?port_id=mock-port`
    );
    expect((await matching.json()).items).toHaveLength(2);
    const missing = await fetch(
      `/api/simulation/sessions/${sessionId}/bandwidth?port_id=missing-port`
    );
    await expect(missing.json()).resolves.toEqual({ items: [] });
  });

  it('serves empty fault lists and strategy options as collections', async () => {
    const sessionId = MOCK_SIMULATION_IDS.commandCenterSession;
    for (const path of ['/simulation/faults', `/simulation/sessions/${sessionId}/faults`]) {
      const response = await fetch(`/api${path}`);
      await expect(response.json()).resolves.toEqual({ items: [] });
    }
    const strategies = await fetch('/api/simulation/strategies');
    await expect(strategies.json()).resolves.toEqual(controllerWire.get_fill_strategies);
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

    for (const response of [startResponse, faultResponse]) {
      expect(response.status).toBe(501);
      expect(response.headers.get('content-type')).toContain('application/problem+json');
      const body = await response.json();
      expect(body).toMatchObject({
        type: 'about:blank',
        title: 'MOCK_SIMULATION_NOT_SUPPORTED',
        status: 501,
        errorCode: 'MOCK_SIMULATION_NOT_SUPPORTED',
        detail: expect.stringContaining('首批只读 mock 不支持'),
        instance: expect.stringContaining('/api/simulation/'),
      });
      expect(body).not.toHaveProperty('code');
      expect(body).not.toHaveProperty('msg');
      expect(body).not.toHaveProperty('data');
    }
  });
});
