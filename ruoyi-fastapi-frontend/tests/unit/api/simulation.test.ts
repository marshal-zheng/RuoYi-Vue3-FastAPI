import { describe, expect, it, vi } from 'vitest';

import * as simulationApi from '@/api/simulation/simulation';
import { MOCK_SIMULATION_IDS } from '@/mocks/data';
import { createNetworkErrorHandler, createStatusHandler } from '@/mocks/handlers/error-common';
import { expectRequestTimeout } from '../../helpers/error-assertions';
import { setupMainlineMockHandlers } from '../../mocks/mainline';
import { setupOverlayMockHandlers } from '../../mocks/overlays';
import { mockServer } from '../../mocks/server';

describe('Simulation API contract', () => {
  setupMainlineMockHandlers();

  it('runs control calls through the real HTTP request path', async () => {
    const sessionId = MOCK_SIMULATION_IDS.commandCenterSession;

    await expect(
      simulationApi.createSimulationSession({
        projectId: 1001,
        versionId: 2002,
      })
    ).resolves.toMatchObject({
      sessionId,
      status: 'running',
    });
    await expect(simulationApi.startSimulation(1, { speed: 1.0 })).rejects.toMatchObject({
      status: 501,
    });
    await expect(simulationApi.pauseSimulation(sessionId)).rejects.toMatchObject({
      status: 501,
    });
    await expect(simulationApi.resumeSimulation(sessionId)).rejects.toMatchObject({
      status: 501,
    });
    await expect(simulationApi.stopSimulation(sessionId)).rejects.toMatchObject({
      status: 501,
    });
    await expect(simulationApi.setSimulationSpeed(sessionId, 2)).rejects.toMatchObject({
      status: 501,
    });
  });

  it('loads read models and export payloads through MSW', async () => {
    const sessionId = MOCK_SIMULATION_IDS.commandCenterSession;

    await expect(simulationApi.getSimulationStatus(sessionId)).resolves.toMatchObject({
      status: 'running',
    });
    await expect(simulationApi.getSimulationStatistics(sessionId)).resolves.toMatchObject({
      status: 'running',
    });
    await expect(simulationApi.getSimulationMessages(sessionId, 10)).resolves.toMatchObject({
      items: expect.arrayContaining([expect.objectContaining({ sessionId })]),
    });
    await expect(simulationApi.getSimulationAlarms(sessionId)).resolves.toMatchObject({
      items: expect.arrayContaining([expect.objectContaining({ sessionId })]),
    });

    const exported = await simulationApi.exportSimulationResults(sessionId, 'csv');
    expect(exported).toBeInstanceOf(Blob);
  });

  it('handles event trigger and WebSocket URL construction', async () => {
    const sessionId = MOCK_SIMULATION_IDS.commandCenterSession;

    await expect(
      simulationApi.triggerEvent(sessionId, {
        name: '故障注入',
        actionType: 'inject_fault',
        actionParams: { faultType: 'disconnect', targetId: 'edge-1' },
      })
    ).rejects.toMatchObject({
      status: 501,
    });

    class TestWebSocket {
      url: string;

      constructor(url: string) {
        this.url = url;
      }

      close() {}
    }
    vi.stubGlobal('WebSocket', TestWebSocket);

    const ws = simulationApi.connectSimulationWebSocket(sessionId);
    expect(ws.url).toContain(`/simulation/${sessionId}/ws`);
    ws.close();
  });

  it('maps 503, 429, and network failures from MSW', async () => {
    const sessionId = MOCK_SIMULATION_IDS.commandCenterSession;
    const statusPath = `/simulation/sessions/${sessionId}/status`;

    mockServer.use(createStatusHandler('get', statusPath, 503));
    await expect(simulationApi.getSimulationStatus(sessionId)).rejects.toMatchObject({
      status: 503,
    });

    mockServer.use(createStatusHandler('get', statusPath, 429));
    await expect(simulationApi.getSimulationStatus(sessionId)).rejects.toMatchObject({
      status: 429,
    });

    mockServer.use(createNetworkErrorHandler('get', statusPath));
    await expect(simulationApi.getSimulationStatus(sessionId)).rejects.toBeInstanceOf(Error);

    await expectRequestTimeout('get', statusPath);
  });
});

describe('Simulation API overlay contract', () => {
  const overlays = setupOverlayMockHandlers();

  it('enters readonly and unsupported simulation states through API wrappers', async () => {
    overlays.activateOverlayHandlers(['simulation-session-readonly']);
    await expect(
      simulationApi.createSimulationSession({
        projectId: 1001,
        versionId: 2002,
      })
    ).resolves.toMatchObject({
      readonly: true,
    });

    overlays.activateOverlayHandlers(['simulation-start-unsupported']);
    await expect(
      simulationApi.startSimulationSession(MOCK_SIMULATION_IDS.commandCenterSession)
    ).rejects.toMatchObject({
      status: 501,
    });

    overlays.activateOverlayHandlers(['simulation-pause-unsupported']);
    await expect(
      simulationApi.pauseSimulationSession(MOCK_SIMULATION_IDS.commandCenterSession)
    ).rejects.toMatchObject({
      status: 501,
    });
  });
});
