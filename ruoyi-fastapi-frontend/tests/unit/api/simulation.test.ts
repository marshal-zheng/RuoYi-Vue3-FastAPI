import { beforeEach, describe, expect, it, vi } from 'vitest';

import * as simulationApi from '@/api/simulation/simulation';
import {
  createApiContractHandlers,
  createNetworkErrorHandler,
  createStatusHandler,
} from '../../mocks/api-contract-handlers';
import { mockServer } from '../../mocks/server';

describe('Simulation API contract', () => {
  beforeEach(() => {
    mockServer.use(...createApiContractHandlers());
  });

  it('runs control calls through the real HTTP request path', async () => {
    await expect(simulationApi.startSimulation(1, { speed: 1.0 })).resolves.toMatchObject({
      data: {
        status: 'running',
        request: {
          project_id: 1,
          config: { speed: 1.0 },
        },
      },
    });
    await expect(simulationApi.pauseSimulation(1)).resolves.toMatchObject({
      data: { status: 'paused' },
    });
    await expect(simulationApi.resumeSimulation(1)).resolves.toMatchObject({
      data: { status: 'running' },
    });
    await expect(simulationApi.stopSimulation(1)).resolves.toMatchObject({
      data: { status: 'stopped', duration: 100.5 },
    });
    await expect(simulationApi.setSimulationSpeed(1, 2)).resolves.toMatchObject({
      data: { speed: 2 },
    });
  });

  it('loads read models and export payloads through MSW', async () => {
    await expect(simulationApi.getSimulationStatus(1)).resolves.toMatchObject({
      data: { status: 'running', current_time: 50.5 },
    });
    await expect(simulationApi.getSimulationStatistics(1)).resolves.toMatchObject({
      data: {
        total_messages: 10000,
        messages_by_protocol: { '1553B': 6000 },
      },
    });
    await expect(simulationApi.getSimulationMessages(1, 10)).resolves.toMatchObject({
      data: [expect.objectContaining({ protocol_type: '1553B' })],
    });
    await expect(simulationApi.getSimulationAlarms(1)).resolves.toMatchObject({
      data: [expect.objectContaining({ level: 'warning' })],
    });

    const exported = await simulationApi.exportSimulationResults(1, 'csv');
    expect(exported).toBeInstanceOf(Blob);
  });

  it('handles event trigger and WebSocket URL construction', async () => {
    await expect(
      simulationApi.triggerEvent(1, {
        event_type: 'fault_injection',
        fault_type: 'communication_loss',
      })
    ).resolves.toMatchObject({
      data: { success: true },
    });

    class TestWebSocket {
      url: string;

      constructor(url: string) {
        this.url = url;
      }

      close() {}
    }
    vi.stubGlobal('WebSocket', TestWebSocket);

    const ws = simulationApi.connectSimulationWebSocket(1);
    expect(ws.url).toContain('/simulation/1/ws');
    ws.close();
  });

  it('maps 503, 429, and network failures from MSW', async () => {
    mockServer.use(createStatusHandler('get', '/simulation/sessions/1/status', 503));
    await expect(simulationApi.getSimulationStatus(1)).rejects.toMatchObject({ status: 503 });

    mockServer.use(createStatusHandler('get', '/simulation/sessions/1/status', 429));
    await expect(simulationApi.getSimulationStatus(1)).rejects.toMatchObject({ status: 429 });

    mockServer.use(createNetworkErrorHandler('get', '/simulation/sessions/1/status'));
    await expect(simulationApi.getSimulationStatus(1)).rejects.toBeInstanceOf(Error);
  });
});
