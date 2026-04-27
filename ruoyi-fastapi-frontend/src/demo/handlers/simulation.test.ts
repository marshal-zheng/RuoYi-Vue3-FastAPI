import 'fake-indexeddb/auto';

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { DemoOfflineDb, replaceDemoOfflineDb } from '@/demo/db';
import { createDemoOfflineHandlers } from '@/demo/handlers';
import { AuthRepository, ScenarioRepository } from '@/demo/repositories';
import type { DemoRuntimeLogger } from '@/demo/runtime/logger';
import type { RuntimeConfig } from '@/demo/runtime/mode';
import { defaultDemoScenario } from '@/demo/scenarios';
import { DemoAuthService } from '@/demo/services';
import { mockServer } from '../../../tests/mocks/server';

const runtimeConfig: RuntimeConfig = {
  mode: 'demo-offline',
  mockMode: 'pure',
  apiPrefix: '/api',
  scenarioId: 'default',
  debug: true,
  source: 'runtime-mode',
};

const logger: DemoRuntimeLogger = {
  debug: vi.fn(),
  info: vi.fn(),
  warn: vi.fn(),
  error: vi.fn(),
};

let db: DemoOfflineDb;

interface CapturedWsMessage {
  type?: string;
  data?: unknown;
}

async function createAuthHeaders(): Promise<HeadersInit> {
  const authService = new DemoAuthService(new AuthRepository(db));
  const login = await authService.login({
    username: 'admin',
    password: 'admin123',
  });

  return {
    Authorization: `Bearer ${login.token}`,
    'Content-Type': 'application/json',
  };
}

function waitForCondition(predicate: () => boolean, timeoutMs = 2000): Promise<void> {
  const startedAt = Date.now();

  return new Promise((resolve, reject) => {
    const tick = () => {
      if (predicate()) {
        resolve();
        return;
      }

      if (Date.now() - startedAt > timeoutMs) {
        reject(new Error('Timed out waiting for WebSocket demo condition.'));
        return;
      }

      setTimeout(tick, 10);
    };

    tick();
  });
}

function waitForOpen(socket: WebSocket): Promise<void> {
  return new Promise((resolve, reject) => {
    socket.addEventListener('open', () => resolve(), {
      once: true,
    });
    socket.addEventListener('error', () => reject(new Error('WebSocket failed to open.')), {
      once: true,
    });
  });
}

describe('demo-offline simulation handlers', () => {
  beforeEach(async () => {
    db = new DemoOfflineDb(`demo-simulation-handler-test-${crypto.randomUUID()}`);
    replaceDemoOfflineDb(db);
    await new ScenarioRepository(db).ensureScenario(defaultDemoScenario);
    mockServer.use(...createDemoOfflineHandlers({ config: runtimeConfig, logger }));
  });

  afterEach(async () => {
    await db.delete();
    replaceDemoOfflineDb(undefined);
  });

  it('serves simulation read endpoints through HTTP handlers', async () => {
    const headers = await createAuthHeaders();

    const createResponse = await fetch('/api/simulation/sessions', {
      method: 'POST',
      headers,
      body: JSON.stringify({
        projectId: 1001,
        versionId: 2001,
      }),
    });
    const created = await createResponse.json();
    const sessionId = created.sessionId;

    expect(createResponse.status).toBe(200);
    expect(created).toMatchObject({
      sessionId: 'demo-session-1001',
      projectId: 1001,
      versionId: 2001,
      status: 'running',
    });

    const statusResponse = await fetch(`/api/simulation/sessions/${sessionId}/status`, {
      headers,
    });
    const statusPayload = await statusResponse.json();
    expect(statusResponse.status).toBe(200);
    expect(statusPayload).toMatchObject({
      sessionId,
      status: 'running',
      messageCount: 1,
      alarmCount: 1,
    });

    const messagesResponse = await fetch(`/api/simulation/sessions/${sessionId}/messages?limit=5`, {
      headers,
    });
    const messagesPayload = await messagesResponse.json();
    expect(messagesResponse.status).toBe(200);
    expect(messagesPayload).toEqual([
      expect.objectContaining({
        id: 'message-1',
        senderNodeName: '平台控制器',
        receiverNodeName: '载荷设备',
      }),
    ]);

    const bandwidthResponse = await fetch(
      `/api/simulation/sessions/${sessionId}/bandwidth?portId=bus-a`,
      {
        headers,
      }
    );
    const bandwidthPayload = await bandwidthResponse.json();
    expect(bandwidthResponse.status).toBe(200);
    expect(bandwidthPayload).toEqual([
      expect.objectContaining({
        portId: 'bus-a',
        bandwidthMbps: 42,
      }),
    ]);

    const alarmsResponse = await fetch(`/api/simulation/sessions/${sessionId}/alarms`, {
      headers,
    });
    const alarmsPayload = await alarmsResponse.json();
    expect(alarmsResponse.status).toBe(200);
    expect(alarmsPayload).toEqual([
      expect.objectContaining({
        alarmId: 'alarm-1',
        message: '离线演示告警样例',
      }),
    ]);

    const faultsResponse = await fetch(`/api/simulation/faults?sessionId=${sessionId}`, {
      headers,
    });
    const faultsPayload = await faultsResponse.json();
    expect(faultsResponse.status).toBe(200);
    expect(faultsPayload).toEqual([
      expect.objectContaining({
        faultId: 'fault-1',
        status: 'pending',
      }),
    ]);

    const eventsResponse = await fetch(`/api/simulation/sessions/${sessionId}/events`, {
      headers,
    });
    const eventsPayload = await eventsResponse.json();
    expect(eventsResponse.status).toBe(200);
    expect(eventsPayload).toEqual([
      expect.objectContaining({
        eventId: 'event-1',
        status: 'pending',
      }),
    ]);

    const exportResponse = await fetch(`/api/simulation/sessions/${sessionId}/export`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        exportFormat: 'json',
        dataType: 'all',
      }),
    });
    const exportPayload = await exportResponse.json();
    expect(exportResponse.status).toBe(200);
    expect(exportPayload).toMatchObject({
      fileName: 'demo-session-1001-simulation-export.json',
      fileSize: expect.any(Number),
    });

    const strategiesResponse = await fetch('/api/simulation/strategies', {
      headers,
    });
    const strategiesPayload = await strategiesResponse.json();
    expect(strategiesResponse.status).toBe(200);
    expect(strategiesPayload).toEqual(
      expect.arrayContaining([expect.objectContaining({ value: 'preset' })])
    );
  });

  it('issues ws tickets and serves a read-only WebSocket stream', async () => {
    const headers = await createAuthHeaders();
    const ticketResponse = await fetch('/api/auth/ws-ticket', {
      method: 'POST',
      headers,
      body: JSON.stringify({
        session_id: 'demo-session-1001',
      }),
    });
    const ticketPayload = await ticketResponse.json();

    expect(ticketResponse.status).toBe(200);
    expect(ticketPayload).toMatchObject({
      wsTicket: expect.stringMatching(/^demo-ws-ticket-/),
      expiresIn: 30,
    });

    const messages: CapturedWsMessage[] = [];
    const socket = new WebSocket(
      `ws://localhost/api/simulation/sessions/demo-session-1001/ws?ticket=${encodeURIComponent(
        ticketPayload.wsTicket
      )}`
    );

    socket.addEventListener('message', (event) => {
      messages.push(JSON.parse(String(event.data)) as CapturedWsMessage);
    });

    await waitForOpen(socket);
    await waitForCondition(() =>
      ['status', 'messages', 'bandwidth', 'alarms', 'faults'].every((type) =>
        messages.some((message) => message.type === type)
      )
    );

    socket.send(JSON.stringify({ type: 'ping' }));
    await waitForCondition(() => messages.some((message) => message.type === 'pong'));

    expect(messages.find((message) => message.type === 'status')?.data).toMatchObject({
      sessionId: 'demo-session-1001',
      status: 'running',
    });
    expect(messages.find((message) => message.type === 'messages')?.data).toEqual([
      expect.objectContaining({
        id: 'message-1',
      }),
    ]);
    expect(messages.find((message) => message.type === 'faults')?.data).toEqual([
      expect.objectContaining({
        action: 'created',
        fault: expect.objectContaining({
          faultId: 'fault-1',
        }),
      }),
    ]);

    socket.close();
  });

  it('returns deterministic 501 payloads for unsupported simulation control and write endpoints', async () => {
    const headers = await createAuthHeaders();
    const cases = [
      {
        input: `/api/simulation/sessions/demo-session-1001/start`,
        method: 'POST',
        capability: 'simulation-control',
      },
      {
        input: `/api/simulation/faults`,
        method: 'POST',
        capability: 'simulation-write',
      },
      {
        input: `/api/simulation/sessions/demo-session-1001/events/event-1/trigger`,
        method: 'POST',
        capability: 'simulation-write',
      },
    ] as const;

    for (const testCase of cases) {
      const response = await fetch(testCase.input, {
        method: testCase.method,
        headers,
        body: testCase.method === 'POST' ? '{}' : undefined,
      });
      const payload = await response.json();

      expect(response.status).toBe(501);
      expect(payload).toMatchObject({
        type: 'about:blank',
        title: 'Demo Capability Not Supported',
        status: 501,
        instance: testCase.input,
        errorCode: 'DEMO_NOT_SUPPORTED',
      });
      expect(payload.detail).toContain('DEMO_NOT_SUPPORTED');
      expect(payload.detail).toContain(testCase.capability);
    }
  });
});
