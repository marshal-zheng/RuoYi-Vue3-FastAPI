import 'fake-indexeddb/auto';

import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import { DemoOfflineDb } from '@/demo/db';
import {
  ProjectRepository,
  ProjectVersionRepository,
  ScenarioRepository,
  SimulationRepository,
} from '@/demo/repositories';
import { defaultDemoScenario } from '@/demo/scenarios';

import { DemoSimulationService } from './simulation';

let db: DemoOfflineDb;
let simulationService: DemoSimulationService;

describe('DemoSimulationService', () => {
  beforeEach(async () => {
    db = new DemoOfflineDb(`demo-simulation-service-test-${crypto.randomUUID()}`);
    await new ScenarioRepository(db).ensureScenario(defaultDemoScenario);
    simulationService = new DemoSimulationService(
      new ProjectRepository(db),
      new ProjectVersionRepository(db),
      new SimulationRepository(db)
    );
  });

  afterEach(async () => {
    await db.delete();
  });

  it('reuses seeded demo sessions and exposes normalized status', async () => {
    const session = await simulationService.createSession({
      projectId: 1001,
      versionId: 2001,
    });
    const status = await simulationService.getStatus(session.sessionId);

    expect(session).toMatchObject({
      sessionId: 'demo-session-1001',
      projectId: 1001,
      versionId: 2001,
      status: 'running',
      readonly: true,
    });

    expect(status).toMatchObject({
      sessionId: 'demo-session-1001',
      status: 'running',
      speed: 1,
      messageCount: 1,
      alarmCount: 1,
      errorCount: 0,
    });
  });

  it('normalizes seeded messages, bandwidth, alarms, faults, events and export payloads', async () => {
    const messages = await simulationService.listMessages('demo-session-1001', 10);
    const bandwidth = await simulationService.listBandwidth('demo-session-1001', {
      portId: 'bus-a',
    });
    const alarms = await simulationService.listAlarms('demo-session-1001');
    const faults = await simulationService.listFaults('demo-session-1001');
    const events = await simulationService.listEvents('demo-session-1001');
    const exportResult = await simulationService.exportSession('demo-session-1001', {
      exportFormat: 'json',
      dataType: 'all',
    });

    expect(messages).toEqual([
      expect.objectContaining({
        id: 'message-1',
        senderNodeName: '平台控制器',
        receiverNodeName: '载荷设备',
        protocolType: '1553B',
        messageType: 'telemetry',
        fillStrategy: 'preset',
      }),
    ]);
    expect(messages[0].payloadHex).toMatch(/^[0-9A-F]+$/);
    expect(messages[0].sizeBytes).toBeGreaterThan(0);

    expect(bandwidth).toEqual([
      expect.objectContaining({
        portId: 'bus-a',
        protocolType: 'LAN',
        bandwidthMbps: 42,
        loadPercent: 42,
      }),
    ]);

    expect(alarms).toEqual([
      expect.objectContaining({
        alarmId: 'alarm-1',
        severity: 'info',
        level: 'info',
        message: '离线演示告警样例',
      }),
    ]);

    expect(faults).toEqual([
      expect.objectContaining({
        faultId: 'fault-1',
        sessionId: 'demo-session-1001',
        faultType: 'disconnect',
        status: 'pending',
      }),
    ]);

    expect(events).toEqual([
      expect.objectContaining({
        eventId: 'event-1',
        name: '默认演示事件',
        status: 'pending',
        triggerCount: 0,
      }),
    ]);

    expect(exportResult).toMatchObject({
      fileName: 'demo-session-1001-simulation-export.json',
      fileSize: expect.any(Number),
    });
    expect(exportResult.downloadUrl).toContain('data:application/json');
    expect(exportResult.content).toContain('"kind": "demo-simulation-export"');
    expect(exportResult.content).toContain('"sessionId": "demo-session-1001"');
  });

  it('combines scenario stream frames with normalized read-only data frames', async () => {
    const frames = await simulationService.listStreamFrames('demo-session-1001');

    expect(frames.map((frame) => frame.type)).toEqual([
      'status',
      'messages',
      'bandwidth',
      'alarms',
      'animation',
      'faults',
      'pong',
    ]);
    expect(frames.find((frame) => frame.type === 'status')).toMatchObject({
      frameId: 'frame-1',
      delayMs: 0,
      payload: expect.objectContaining({
        sessionId: 'demo-session-1001',
        status: 'running',
      }),
    });
    expect(frames.find((frame) => frame.type === 'messages')?.payload).toEqual([
      expect.objectContaining({
        id: 'message-1',
      }),
    ]);
    expect(frames.find((frame) => frame.type === 'faults')?.payload).toEqual([
      expect.objectContaining({
        action: 'created',
        fault: expect.objectContaining({
          faultId: 'fault-1',
          status: 'pending',
        }),
      }),
    ]);
  });
});
