import { http, HttpResponse } from 'msw';
import { beforeEach, describe, expect, expectTypeOf, it, vi } from 'vitest';
import { effectScope, ref } from 'vue';
import * as simulationApi from '@/api/simulation/simulation';
import type {
  FaultWire,
  SimulationAlarm,
  SimulationBandwidth,
  SimulationEvent,
  SimulationMessage,
  SimulationFillStrategy,
  SimulationSessionCommandAccepted,
} from '@/api/simulation/types';
import type { HttpCollection } from '@/types/http-contract';
import { useEventTrigger } from '@/views/project/simulation/composables/useEventTrigger';
import { useFaultInjection } from '@/views/project/simulation/composables/useFaultInjection';
import { useSimulationApi } from '@/views/project/simulation/composables/useSimulationApi';
import controllerWire from '../../fixtures/simulation-http-wire.json';
import { mockServer } from '../../mocks/server';

// Recorded by simulation-http-wire.py using real backend controllers and ResponseUtil.
// Serving these bytes through MSW exercises the public HTTP client, not an API mock.
describe('simulation HTTP controller/factory collection contract', () => {
  beforeEach(() => {
    mockServer.use(
      http.get('/api/simulation/sessions/session-1/messages', () =>
        HttpResponse.json(controllerWire.get_simulation_messages)
      ),
      http.get('/api/simulation/sessions/session-1/bandwidth', () =>
        HttpResponse.json(controllerWire.get_simulation_bandwidth)
      ),
      http.get('/api/simulation/sessions/session-1/alarms', () =>
        HttpResponse.json(controllerWire.get_simulation_alarms)
      ),
      http.get('/api/simulation/faults', () => HttpResponse.json(controllerWire.query_faults)),
      http.get('/api/simulation/sessions/session-1/events', () =>
        HttpResponse.json(controllerWire.list_events)
      ),
      http.get('/api/simulation/strategies', () =>
        HttpResponse.json(controllerWire.get_fill_strategies)
      ),
      http.post('/api/simulation/sessions/session-1/start', () =>
        HttpResponse.json(controllerWire.start_accepted.body, {
          status: controllerWire.start_accepted.status,
          headers: { Location: controllerWire.start_accepted.location },
        })
      ),
      http.post('/api/simulation/sessions/session-1/stop', () =>
        HttpResponse.json(controllerWire.stop_accepted.body, {
          status: controllerWire.stop_accepted.status,
          headers: { Location: controllerWire.stop_accepted.location },
        })
      )
    );
  });

  it('keeps accepted commands distinct from polled session status and preserves the Location header', async () => {
    expectTypeOf<Awaited<ReturnType<typeof simulationApi.startSimulationSession>>>().toEqualTypeOf<
      SimulationSessionCommandAccepted<'start'>
    >();
    expectTypeOf<Awaited<ReturnType<typeof simulationApi.stopSimulationSession>>>().toEqualTypeOf<
      SimulationSessionCommandAccepted<'stop'>
    >();
    const api = useSimulationApi();
    expectTypeOf<Awaited<ReturnType<typeof api.startSession>>>().toEqualTypeOf<
      SimulationSessionCommandAccepted<'start'>
    >();
    expectTypeOf<Awaited<ReturnType<typeof api.stopSession>>>().toEqualTypeOf<
      SimulationSessionCommandAccepted<'stop'>
    >();
    for (const action of ['start', 'stop']) {
      const response = await fetch(`/api/simulation/sessions/session-1/${action}`, {
        method: 'POST',
      });
      expect(response.status).toBe(202);
      expect(response.headers.get('Location')).toBe(controllerWire.start_accepted.location);
      await expect(response.json()).resolves.toEqual({
        sessionId: 'session-1',
        action,
        status: 'accepted',
      });
    }
    const started = await api.startSession('session-1');
    const stopped = await api.stopSession('session-1');
    expect(started).toMatchObject(controllerWire.start_accepted.body);
    expect(stopped).toMatchObject(controllerWire.stop_accepted.body);
    expect(started).not.toHaveProperty('messageCount');
    expect(stopped).not.toHaveProperty('messageCount');
  });

  it('publishes one typed items contract for every outer collection', async () => {
    const [messages, bandwidth, alarms, faults, events, strategies] = await Promise.all([
      simulationApi.getSimulationMessages('session-1'),
      simulationApi.getSimulationBandwidth('session-1'),
      simulationApi.getSimulationAlarms('session-1'),
      simulationApi.getFaults('session-1'),
      simulationApi.getEvents('session-1'),
      simulationApi.getFillStrategies(),
    ]);
    expectTypeOf(messages).toEqualTypeOf<HttpCollection<SimulationMessage>>();
    expectTypeOf(bandwidth).toEqualTypeOf<HttpCollection<SimulationBandwidth>>();
    expectTypeOf(alarms).toEqualTypeOf<HttpCollection<SimulationAlarm>>();
    expectTypeOf(faults).toEqualTypeOf<HttpCollection<FaultWire>>();
    expectTypeOf(events).toEqualTypeOf<HttpCollection<SimulationEvent>>();
    expectTypeOf(strategies).toEqualTypeOf<HttpCollection<SimulationFillStrategy>>();
    expect(messages.items).toEqual(controllerWire.get_simulation_messages.items);
    expect(bandwidth.items).toEqual(controllerWire.get_simulation_bandwidth.items);
    expect(alarms.items).toEqual(controllerWire.get_simulation_alarms.items);
    expect(faults.items).toEqual(controllerWire.query_faults.items);
    expect(events.items).toEqual(controllerWire.list_events.items);
    expect(strategies.items).toEqual(controllerWire.get_fill_strategies.items);
    expect(controllerWire.list_faults).toEqual(controllerWire.query_faults);
  });

  it('sends the port_id filter accepted by the actual bandwidth controller', async () => {
    let receivedQuery: URLSearchParams | undefined;
    mockServer.use(
      http.get('/api/simulation/sessions/session-1/bandwidth', ({ request }) => {
        receivedQuery = new URL(request.url).searchParams;
        return HttpResponse.json(controllerWire.get_simulation_bandwidth);
      })
    );
    await simulationApi.getSimulationBandwidth('session-1', 'port-1');
    expect(receivedQuery?.get('port_id')).toBe('port-1');
    expect(receivedQuery?.has('portId')).toBe(false);
  });

  it('projects message, bandwidth and alarm items for reactive data consumers', async () => {
    const api = useSimulationApi();
    const [messages, bandwidth, alarms] = await Promise.all([
      api.fetchMessages('session-1'),
      api.fetchBandwidth('session-1'),
      api.fetchAlarms('session-1'),
    ]);
    expect(messages).toEqual(controllerWire.get_simulation_messages.items);
    expect(bandwidth).toEqual(controllerWire.get_simulation_bandwidth.items);
    expect(alarms).toEqual(controllerWire.get_simulation_alarms.items);
    expect(alarms[0]?.details?.connections).toEqual([{ edgeId: 'edge-1' }]);
  });

  it('loads pending events from the actual collection into event state', async () => {
    const scope = effectScope();
    const events = scope.run(() => useEventTrigger(ref('session-1')));
    if (!events) throw new Error('Event effect scope was not active.');
    try {
      await vi.waitFor(() => expect(events.loading.value).toBe(false));
      expect(events.eventList.value).toEqual(controllerWire.list_events.items);
      expect(events.pendingEventCount.value).toBe(1);
      expect(events.lastError.value).toBeNull();
    } finally {
      scope.stop();
    }
  });

  it('keeps active faults instead of silently discarding a collection resource', async () => {
    const faults = useFaultInjection(ref('session-1'));
    await expect(faults.fetchFaults()).resolves.toMatchObject([
      {
        faultId: 'fault-1',
        faultType: 'disconnect',
        targetId: 'edge-1',
        status: 'active',
      },
    ]);
    expect(faults.loading.value).toBe(false);
  });

  it('preserves arrays embedded inside ordinary object resources', () => {
    expect(controllerWire.embedded_resource).toEqual({
      events: controllerWire.list_events.items,
    });
  });
});
